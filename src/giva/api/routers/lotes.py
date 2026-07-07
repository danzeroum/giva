"""POST /lotes (upload), GET /lotes, GET /lotes/{id}, GET /lotes/{id}/linhas,
POST /lotes/{id}/linhas/{numero}/contestacoes, GET /lotes/{id}/saida.xlsx —
fluxo do Analista ponta a ponta (Fase 3, ADR-03/ADR-07).

RBAC por escopo de dado, não por rota: um `analista` só enxerga os próprios
lotes (filtra por `criado_por`); `operador`/`admin` enxergam todos — quem não
é dono recebe 404 (não 403), para não revelar que o lote existe.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import psycopg
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response

from giva.api.deps import get_conexao, get_usuario_atual
from giva.api.schemas.lotes import (
    ContestacaoRequest,
    ContestacaoResposta,
    LinhaLoteResposta,
    LoteResposta,
)
from giva.api.seguranca import UsuarioToken
from giva.armazenamento import caminho_saida, salvar_entrada
from giva.decisao.statuses import pior_status
from giva.pipeline.leitor import ler_planilha
from giva.pipeline.persistencia_sql import abrir_lote, concluir_lote, persistir_linhas
from giva.saida.montador import construir_resumo, montar_xlsx
from giva.worker.composicao import pipeline_padrao
from giva.worker.fila import enfileirar_lote

router = APIRouter(prefix="/lotes", tags=["lotes"])

# ADR-03: lotes com até este tanto de linhas processam na própria request;
# acima disso, vão para a fila do worker.
_LIMITE_SINCRONO = 5000

_CAMPOS_LOTE = (
    "id, nome_arquivo, status, total_linhas, linhas_processadas, criado_por, "
    "criado_em, concluido_em, resumo"
)


def _lote_da_linha(linha: tuple[Any, ...]) -> LoteResposta:
    (
        id_, nome_arquivo, status_, total, processadas,
        criado_por, criado_em, concluido_em, resumo,
    ) = linha
    return LoteResposta(
        id=id_,
        nome_arquivo=nome_arquivo,
        status=status_,
        total_linhas=total,
        linhas_processadas=processadas,
        criado_por=criado_por,
        criado_em=criado_em,
        concluido_em=concluido_em,
        resumo=resumo,
    )


def _buscar_lote(
    con: psycopg.Connection[Any], lote_id: int, usuario: UsuarioToken
) -> LoteResposta:
    # Bandit (B608) marca a f-string abaixo como possível injeção — falso
    # positivo: _CAMPOS_LOTE é constante fixa do módulo (nunca entrada do
    # usuário); lote_id vai parametrizado (%s).
    linha = con.execute(
        f"SELECT {_CAMPOS_LOTE} FROM lote WHERE id = %s", (lote_id,)  # nosec B608
    ).fetchone()
    if linha is None:
        raise HTTPException(status_code=404, detail="Lote não encontrado.")
    lote = _lote_da_linha(linha)
    if usuario.papel == "analista" and lote.criado_por != usuario.email:
        raise HTTPException(status_code=404, detail="Lote não encontrado.")
    return lote


@router.post("", status_code=status.HTTP_201_CREATED)
def enviar(
    arquivo: UploadFile,
    usuario: Annotated[UsuarioToken, Depends(get_usuario_atual)],
    con: Annotated[psycopg.Connection[Any], Depends(get_conexao)],
) -> LoteResposta:
    conteudo = arquivo.file.read()
    nome_arquivo = arquivo.filename or "planilha.csv"
    try:
        # despacha .xlsx (assinatura ZIP) vs CSV; ColunaAusenteError -> 422.
        dados = ler_planilha(conteudo, nome_arquivo)
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=422, detail="Arquivo não é CSV UTF-8 nem .xlsx válido."
        ) from exc

    caminho_entrada = salvar_entrada(conteudo)
    if len(dados.linhas) <= _LIMITE_SINCRONO:
        lote_id = abrir_lote(con, arquivo_entrada=caminho_entrada, criado_por=usuario.email)
        con.execute(
            "UPDATE lote SET total_linhas = %s, nome_arquivo = %s WHERE id = %s",
            (len(dados.linhas), nome_arquivo, lote_id),
        )
        linhas = pipeline_padrao(con).processar(dados.linhas)
        persistir_linhas(con, lote_id, linhas)
        resumo = construir_resumo(linhas)
        saida = caminho_saida(lote_id)
        Path(saida).write_bytes(montar_xlsx(dados.colunas_originais, linhas))
        con.execute(
            "UPDATE lote SET linhas_processadas = %s WHERE id = %s",
            (len(linhas), lote_id),
        )
        concluir_lote(con, lote_id, arquivo_saida=saida, resumo=resumo)
    else:
        lote_id = enfileirar_lote(con, arquivo_entrada=caminho_entrada, criado_por=usuario.email)
        con.execute(
            "UPDATE lote SET nome_arquivo = %s WHERE id = %s", (nome_arquivo, lote_id)
        )
    con.commit()
    return _buscar_lote(con, lote_id, usuario)


@router.get("")
def listar(
    usuario: Annotated[UsuarioToken, Depends(get_usuario_atual)],
    con: Annotated[psycopg.Connection[Any], Depends(get_conexao)],
    pagina: int = 1,
    tamanho_pagina: int = 20,
) -> list[LoteResposta]:
    limite = max(1, min(tamanho_pagina, 100))
    offset = max(0, (pagina - 1) * limite)
    # Falso positivo do Bandit (B608), mesmo motivo de _buscar_lote acima:
    # _CAMPOS_LOTE é constante fixa; usuario.email/limite/offset vão
    # parametrizados (%s).
    if usuario.papel == "analista":
        linhas = con.execute(
            f"SELECT {_CAMPOS_LOTE} FROM lote WHERE criado_por = %s "  # nosec B608
            "ORDER BY criado_em DESC LIMIT %s OFFSET %s",
            (usuario.email, limite, offset),
        ).fetchall()
    else:
        linhas = con.execute(
            f"SELECT {_CAMPOS_LOTE} FROM lote ORDER BY criado_em DESC LIMIT %s OFFSET %s",  # nosec B608
            (limite, offset),
        ).fetchall()
    return [_lote_da_linha(linha) for linha in linhas]


@router.get("/{lote_id}")
def detalhe(
    lote_id: int,
    usuario: Annotated[UsuarioToken, Depends(get_usuario_atual)],
    con: Annotated[psycopg.Connection[Any], Depends(get_conexao)],
) -> LoteResposta:
    return _buscar_lote(con, lote_id, usuario)


@router.get("/{lote_id}/linhas")
def linhas_do_lote(
    lote_id: int,
    usuario: Annotated[UsuarioToken, Depends(get_usuario_atual)],
    con: Annotated[psycopg.Connection[Any], Depends(get_conexao)],
    status_filtro: str | None = None,
    uf: str | None = None,
    pagina: int = 1,
    tamanho_pagina: int = 50,
) -> list[LinhaLoteResposta]:
    _buscar_lote(con, lote_id, usuario)  # 404 se não existe / não é do dono
    limite = max(1, min(tamanho_pagina, 200))
    offset = max(0, (pagina - 1) * limite)

    condicoes = ["lote_id = %s"]
    parametros: list[Any] = [lote_id]
    if uf:
        condicoes.append("uf = %s")
        parametros.append(uf)
    if status_filtro:
        # Aproximação: casa se QUALQUER um dos status_* da linha bater — não
        # exatamente "o pior status é X" (que exigiria uma coluna computada).
        condicoes.append(
            "(statuses->>'status_linha' = %s OR statuses->>'status_ncm' = %s "
            "OR statuses->>'status_aliquota' = %s OR statuses->>'status_descricao' = %s)"
        )
        parametros.extend([status_filtro] * 4)
    parametros.extend([limite, offset])

    # Falso positivo do Bandit (B608): `condicoes` só acumula fragmentos
    # fixos ("lote_id = %s", "uf = %s", ...) declarados acima neste mesmo
    # módulo; os valores de usuário (uf, status_filtro, lote_id, limite,
    # offset) vão todos em `parametros`, nunca concatenados na string.
    sql = (
        "SELECT numero, originais, enriquecido, statuses, proveniencia, uf "
        f"FROM lote_linha WHERE {' AND '.join(condicoes)} "  # nosec B608
        "ORDER BY numero LIMIT %s OFFSET %s"
    )

    resultado = []
    for numero, originais, enriquecido, statuses, proveniencia, uf_linha in con.execute(
        sql, parametros
    ).fetchall():
        resultado.append(
            LinhaLoteResposta(
                numero=numero,
                originais=originais,
                enriquecimento=enriquecido or {},
                status=pior_status((statuses or {}).values()),
                uf=uf_linha,
                proveniencia=proveniencia or {},
            )
        )
    return resultado


@router.post(
    "/{lote_id}/linhas/{numero}/contestacoes", status_code=status.HTTP_201_CREATED
)
def contestar(
    lote_id: int,
    numero: int,
    dados: ContestacaoRequest,
    usuario: Annotated[UsuarioToken, Depends(get_usuario_atual)],
    con: Annotated[psycopg.Connection[Any], Depends(get_conexao)],
) -> ContestacaoResposta:
    _buscar_lote(con, lote_id, usuario)  # 404 se não existe / não é do dono
    existe = con.execute(
        "SELECT 1 FROM lote_linha WHERE lote_id = %s AND numero = %s", (lote_id, numero)
    ).fetchone()
    if existe is None:
        raise HTTPException(status_code=404, detail="Linha não encontrada.")

    linha = con.execute(
        "INSERT INTO contestacao (lote_id, numero_linha, autor_id, tipo, texto) "
        "VALUES (%s, %s, %s, %s, %s) "
        "RETURNING id, lote_id, numero_linha, autor_id, tipo, texto, status, criado_em",
        (lote_id, numero, usuario.id, dados.tipo, dados.texto),
    ).fetchone()
    con.commit()
    if linha is None:
        raise RuntimeError("INSERT INTO contestacao ... RETURNING não devolveu linha")
    (id_, lote_id_, numero_linha, autor_id, tipo, texto, status_, criado_em) = linha
    return ContestacaoResposta(
        id=id_,
        lote_id=lote_id_,
        numero_linha=numero_linha,
        autor_id=autor_id,
        tipo=tipo,
        texto=texto,
        status=status_,
        criado_em=criado_em,
    )


@router.get("/{lote_id}/saida.xlsx")
def baixar_saida(
    lote_id: int,
    usuario: Annotated[UsuarioToken, Depends(get_usuario_atual)],
    con: Annotated[psycopg.Connection[Any], Depends(get_conexao)],
) -> Response:
    lote = _buscar_lote(con, lote_id, usuario)
    if lote.status != "concluido":
        raise HTTPException(status_code=409, detail="Lote ainda não foi concluído.")
    linha = con.execute(
        "SELECT arquivo_saida FROM lote WHERE id = %s", (lote_id,)
    ).fetchone()
    caminho = linha[0] if linha else None
    if not caminho or not Path(caminho).exists():
        raise HTTPException(status_code=404, detail="Arquivo de saída não encontrado.")
    return Response(
        content=Path(caminho).read_bytes(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="lote_{lote_id}.xlsx"'},
    )
