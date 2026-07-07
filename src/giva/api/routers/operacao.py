"""Bloco B — Operação (Fase 4): validação de UF (B2), parâmetros do motor
(B3), exceções de categoria (B4), contestações (B5), e cargas (B1 — leitura
apenas; aprovação/diff ficaram fora desta fase, ver `pendencias.md`).

Todas as rotas exigem papel `operador` ou `admin` — o Bloco B é território do
operador (RBAC por rota, diferente de `routers/lotes.py`, cujo RBAC é por
escopo de dado; aqui não há "dono", é uma área inteira restrita por papel).

B1 (cargas) é leitura apenas nesta fase (aprovação/diff de carga fica para a
fase da base histórica). Os demais (B2 validação de UF, B3 parâmetros, B4
exceções, B5 contestações) usam os repositórios do giva
(`RepositorioAliquotaSQL.listar_vigencias_correntes`/`atualizar_status_validacao`,
`RepositorioCategoriaSQL.listar_excecoes`/`criar_excecao`).
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg.types.json import Jsonb

from giva.aliquota.repositorio_sql import RepositorioAliquotaSQL
from giva.api.deps import exige_papel, get_conexao
from giva.api.schemas.operacao import (
    AtualizarParametroRequest,
    AtualizarStatusUfRequest,
    CargaResposta,
    ContestacaoOperacaoResposta,
    CriarExcecaoRequest,
    EncaminharContestacaoRequest,
    ExcecaoResposta,
    HistoricoParametroItem,
    ParametroResposta,
    UfResposta,
)
from giva.api.seguranca import UsuarioToken
from giva.auditoria import registrar as registrar_auditoria
from giva.categoria.repositorio_sql import RepositorioCategoriaSQL

router = APIRouter(tags=["operacao"])

_Operador = Annotated[UsuarioToken, Depends(exige_papel("operador", "admin"))]
_Conexao = Annotated[psycopg.Connection[Any], Depends(get_conexao)]


# --- B2: validação por UF ---------------------------------------------------


def _uf_resposta(v: Any) -> UfResposta:
    return UfResposta(
        uf=v.uf,
        vigencia_inicio=v.vigencia_inicio,
        vigencia_fim=v.vigencia_fim,
        aliquota_modal=v.aliquota_modal,
        fecp_percentual=v.fecp_percentual,
        fecp_incidencia=v.fecp_incidencia,
        status_validacao=v.status_validacao,
        fonte_legal=v.fonte_legal,
        fonte_compilada=v.fonte_compilada,
    )


@router.get("/ufs")
def listar_ufs(usuario: _Operador, con: _Conexao) -> list[UfResposta]:
    """Grid das UFs com vigência corrente (B2 — validação fiscal)."""
    vigencias = RepositorioAliquotaSQL(con).listar_vigencias_correntes(date.today())
    return [_uf_resposta(v) for v in vigencias]


@router.put("/ufs/{uf}")
def atualizar_uf(
    uf: str, dados: AtualizarStatusUfRequest, usuario: _Operador, con: _Conexao
) -> UfResposta:
    """Promove o `status_validacao` da vigência corrente de uma UF (B2)."""
    repo = RepositorioAliquotaSQL(con)
    hoje = date.today()
    anterior = repo.buscar_vigencia(uf, hoje)
    if anterior is None:
        raise HTTPException(
            status_code=404, detail=f"Sem vigência corrente de alíquota para {uf}."
        )
    repo.atualizar_status_validacao(uf, hoje, dados.status_validacao)
    registrar_auditoria(
        con,
        quem=usuario.email,
        acao="uf_status_validacao_atualizado",
        alvo=f"aliquota_icms_modal:{uf}",
        antes={"status_validacao": anterior.status_validacao},
        depois={"status_validacao": dados.status_validacao},
    )
    con.commit()
    atual = repo.buscar_vigencia(uf, hoje)
    if atual is None:
        raise RuntimeError("vigência sumiu após UPDATE de status_validacao")
    return _uf_resposta(atual)


# --- B3: parâmetros do motor -------------------------------------------------


@router.get("/parametros")
def listar_parametros(usuario: _Operador, con: _Conexao) -> list[ParametroResposta]:
    linhas = con.execute(
        "SELECT nome, valor, atualizado_em FROM parametro ORDER BY nome"
    ).fetchall()
    return [
        ParametroResposta(nome=nome, valor=valor, atualizado_em=atualizado_em)
        for nome, valor, atualizado_em in linhas
    ]


@router.put("/parametros/{nome}")
def atualizar_parametro(
    nome: str, dados: AtualizarParametroRequest, usuario: _Operador, con: _Conexao
) -> ParametroResposta:
    anterior = con.execute(
        "SELECT valor FROM parametro WHERE nome = %s", (nome,)
    ).fetchone()
    if anterior is None:
        raise HTTPException(status_code=404, detail=f"Parâmetro '{nome}' não existe.")
    linha = con.execute(
        "UPDATE parametro SET valor = %s, atualizado_em = now() WHERE nome = %s "
        "RETURNING nome, valor, atualizado_em",
        (Jsonb(dados.valor), nome),
    ).fetchone()
    if linha is None:
        raise RuntimeError("UPDATE parametro ... RETURNING não devolveu linha")
    registrar_auditoria(
        con,
        quem=usuario.email,
        acao="parametro_atualizado",
        alvo=f"parametro:{nome}",
        antes={"valor": anterior[0]},
        depois={"valor": dados.valor},
    )
    con.commit()
    nome_, valor_, atualizado_em_ = linha
    return ParametroResposta(nome=nome_, valor=valor_, atualizado_em=atualizado_em_)


@router.get("/parametros/{nome}/historico")
def historico_parametro(
    nome: str, usuario: _Operador, con: _Conexao
) -> list[HistoricoParametroItem]:
    linhas = con.execute(
        "SELECT quando, quem, antes, depois FROM auditoria "
        "WHERE alvo = %s ORDER BY quando DESC",
        (f"parametro:{nome}",),
    ).fetchall()
    return [
        HistoricoParametroItem(quando=quando, quem=quem, antes=antes, depois=depois)
        for quando, quem, antes, depois in linhas
    ]


# --- B4: exceções de categoria -----------------------------------------------


def _excecao_por_ncm(con: Any, ncm: str, versao: str) -> ExcecaoResposta:
    linha = con.execute(
        "SELECT ncm, categoria, justificativa, versao, origem_tipo, "
        "origem_contestacao_id, autor_id, criado_em FROM regras_excecao "
        "WHERE ncm = %s AND versao = %s",
        (ncm, versao),
    ).fetchone()
    if linha is None:
        raise RuntimeError("exceção sumiu após INSERT")
    campos = (
        "ncm", "categoria", "justificativa", "versao", "origem_tipo",
        "origem_contestacao_id", "autor_id", "criado_em",
    )
    return ExcecaoResposta(**dict(zip(campos, linha, strict=True)))


@router.get("/excecoes")
def listar_excecoes(usuario: _Operador, con: _Conexao) -> list[ExcecaoResposta]:
    """Regras de exceção NCM→categoria (B4)."""
    return [
        ExcecaoResposta(**registro)
        for registro in RepositorioCategoriaSQL(con).listar_excecoes()
    ]


@router.post("/excecoes", status_code=status.HTTP_201_CREATED)
def criar_excecao(
    dados: CriarExcecaoRequest, usuario: _Operador, con: _Conexao
) -> ExcecaoResposta:
    """Cria/atualiza uma exceção NCM→categoria na versão vigente (B4)."""
    repo = RepositorioCategoriaSQL(con)
    versao = repo.versao_vigente()
    repo.criar_excecao(
        ncm=dados.ncm,
        categoria=dados.categoria,
        justificativa=dados.justificativa,
        versao=versao,
        origem_tipo=dados.origem_tipo,
        origem_contestacao_id=dados.origem_contestacao_id,
        autor_id=usuario.id,
    )
    registrar_auditoria(
        con,
        quem=usuario.email,
        acao="excecao_categoria_criada",
        alvo=f"regras_excecao:{dados.ncm}:{versao}",
        depois={"categoria": dados.categoria, "justificativa": dados.justificativa},
    )
    con.commit()
    return _excecao_por_ncm(con, dados.ncm, versao)


# --- B5: contestações ---------------------------------------------------------


@router.get("/contestacoes")
def listar_contestacoes(
    usuario: _Operador, con: _Conexao, status_filtro: str | None = None
) -> list[ContestacaoOperacaoResposta]:
    if status_filtro:
        linhas = con.execute(
            "SELECT id, lote_id, numero_linha, autor_id, tipo, texto, status, "
            "resolucao, criado_em, resolvido_em FROM contestacao "
            "WHERE status = %s ORDER BY criado_em DESC",
            (status_filtro,),
        ).fetchall()
    else:
        linhas = con.execute(
            "SELECT id, lote_id, numero_linha, autor_id, tipo, texto, status, "
            "resolucao, criado_em, resolvido_em FROM contestacao "
            "ORDER BY criado_em DESC"
        ).fetchall()
    campos = (
        "id", "lote_id", "numero_linha", "autor_id", "tipo", "texto",
        "status", "resolucao", "criado_em", "resolvido_em",
    )
    return [
        ContestacaoOperacaoResposta(**dict(zip(campos, linha, strict=True)))
        for linha in linhas
    ]


@router.put("/contestacoes/{contestacao_id}/encaminhar")
def encaminhar_contestacao(
    contestacao_id: int,
    dados: EncaminharContestacaoRequest,
    usuario: _Operador,
    con: _Conexao,
) -> ContestacaoOperacaoResposta:
    atual = con.execute(
        "SELECT status FROM contestacao WHERE id = %s", (contestacao_id,)
    ).fetchone()
    if atual is None:
        raise HTTPException(status_code=404, detail="Contestação não encontrada.")
    if atual[0] == "resolvida":
        raise HTTPException(status_code=409, detail="Contestação já resolvida.")

    if dados.destino == "excecao":
        if not dados.categoria or not dados.ncm:
            raise HTTPException(
                status_code=422,
                detail="destino 'excecao' exige 'categoria' e 'ncm'.",
            )
        repo_cat = RepositorioCategoriaSQL(con)
        repo_cat.criar_excecao(
            ncm=dados.ncm,
            categoria=dados.categoria,
            justificativa=dados.resolucao,
            versao=repo_cat.versao_vigente(),
            origem_tipo="contestacao",
            origem_contestacao_id=contestacao_id,
            autor_id=usuario.id,
        )

    linha = con.execute(
        "UPDATE contestacao SET status = 'resolvida', resolucao = %s, "
        "resolvido_em = now() WHERE id = %s "
        "RETURNING id, lote_id, numero_linha, autor_id, tipo, texto, status, "
        "resolucao, criado_em, resolvido_em",
        (dados.resolucao, contestacao_id),
    ).fetchone()
    if linha is None:
        raise RuntimeError("UPDATE contestacao ... RETURNING não devolveu linha")
    registrar_auditoria(
        con,
        quem=usuario.email,
        acao="contestacao_encaminhada",
        alvo=f"contestacao:{contestacao_id}",
        depois={"destino": dados.destino, "resolucao": dados.resolucao},
    )
    con.commit()
    campos = (
        "id", "lote_id", "numero_linha", "autor_id", "tipo", "texto",
        "status", "resolucao", "criado_em", "resolvido_em",
    )
    return ContestacaoOperacaoResposta(**dict(zip(campos, linha, strict=True)))


# --- B1: cargas (leitura apenas nesta fase — ver pendencias.md) --------------


@router.get("/cargas")
def listar_cargas(usuario: _Operador, con: _Conexao) -> list[CargaResposta]:
    linhas = con.execute(
        "SELECT id, fonte, arquivo_bruto, hash_arquivo, data_coleta, criado_em, "
        "promovido_em, promovido_por FROM carga ORDER BY criado_em DESC"
    ).fetchall()
    campos = (
        "id", "fonte", "arquivo_bruto", "hash_arquivo", "data_coleta",
        "criado_em", "promovido_em", "promovido_por",
    )
    return [CargaResposta(**dict(zip(campos, linha, strict=True))) for linha in linhas]
