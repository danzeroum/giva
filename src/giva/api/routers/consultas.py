"""Consultas prontas (Bloco B — Banco de dados). Perguntas frequentes à base,
com resultado tabular genérico (`{cols, rows, nota}`) para render único + cópia
TSV no front. Todas as rotas são leitura; a única com efeito é a auditoria de
cada `POST /consultas/sql`.

RBAC operador/admin, no padrão de `operacao.py`. O SQL livre tem defesa em
profundidade: validação em `giva.api.consultas_sql` (SELECT-only, whitelist,
LIMIT forçado) + conexão read-only dedicada + `statement_timeout` + auditoria.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Any

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from psycopg.rows import dict_row

from giva.api.consultas_sql import LIMITE_PADRAO, SqlNaoPermitidoError, preparar_consulta
from giva.api.deps import exige_papel, get_conexao
from giva.api.schemas.consultas import ConsultaResposta, SqlRequest
from giva.api.seguranca import UsuarioToken
from giva.auditoria import registrar as registrar_auditoria
from giva.categoria.repositorio_sql import RepositorioCategoriaSQL
from giva.config import dsn_readonly

router = APIRouter(prefix="/consultas", tags=["consultas"])

_Operador = Annotated[UsuarioToken, Depends(exige_papel("operador", "admin"))]
_Conexao = Annotated[psycopg.Connection[Any], Depends(get_conexao)]

# Rótulos leigos de status_validacao SÓ para a célula de relatório desta consulta
# (camada de exibição — o enum no banco/contrato não muda; ver a tabela de-para
# do handoff e frontend/src/data/copy.ts).
_VALIDACAO_LABEL = {
    "validada": "conferida na fonte oficial",
    "confirmada_fonte_secundaria": "conferida em fonte secundária",
    "divergencia_entre_fontes": "fontes não batem — conferir",
    "pendente_validacao": "ainda não conferida",
}


# --- helpers -----------------------------------------------------------------


def _fmt_ncm(codigo: str) -> str:
    """8 dígitos → 0000.00.00 (como o usuário lê a NCM). Deixa como veio se não
    tiver 8 dígitos."""
    d = re.sub(r"\D", "", codigo or "")
    return f"{d[0:4]}.{d[4:6]}.{d[6:8]}" if len(d) == 8 else codigo


def _ato(tipo: Any, numero: Any, ano: Any) -> str:
    partes = [p for p in (tipo, numero and str(numero), ano and str(ano)) if p]
    if not partes:
        return "—"
    if numero and ano:
        return f"{tipo or ''} {numero}/{ano}".strip()
    return " ".join(str(p) for p in partes)


def _periodo_data(periodo: str | None) -> date | None:
    """'AAAA-MM' (ou 'AAAA-MM-DD') → date. Vazio → None. Formato inválido → 400."""
    p = (periodo or "").strip()
    if not p:
        return None
    m = re.fullmatch(r"(\d{4})-(\d{2})(?:-(\d{2}))?", p)
    if not m:
        raise HTTPException(status_code=400, detail="Período deve ser AAAA-MM (ex.: 2026-05).")
    ano, mes, dia = int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)
    try:
        return date(ano, mes, dia)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Período inválido.") from exc


def _resumo_json(valor: dict[str, Any] | None) -> str:
    """Compacta um lado (antes/depois) da auditoria numa string legível."""
    if not valor:
        return "(novo)"
    return " · ".join(f"{k}: {v}" for k, v in valor.items())


def _celula(v: Any) -> Any:
    """Deixa a célula JSON-serializável para o envelope genérico (números e
    strings passam; Decimal/date/range viram texto)."""
    if v is None or isinstance(v, (int, float, str, bool)):
        return v
    return str(v)


# --- 1. Buscar um NCM --------------------------------------------------------


@router.get("/ncm")
def consulta_ncm(
    usuario: _Operador, con: _Conexao, q: str | None = None, periodo: str | None = None
) -> ConsultaResposta:
    termo = (q or "").strip()
    if not termo:
        raise HTTPException(
            status_code=400,
            detail="Informe um código NCM (≥4 dígitos) ou um termo da descrição.",
        )
    digitos = re.sub(r"\D", "", termo)
    por_codigo = len(digitos) >= 4
    data_periodo = _periodo_data(periodo)
    cols = ["código", "descrição oficial", "vigente desde", "ato legal"]

    # Se período informado e o histórico decenal tiver cobertura, responde dele.
    if data_periodo is not None:
        with con.cursor(row_factory=dict_row) as cur:
            if por_codigo:
                cond, param = "h.codigo LIKE %(m)s", digitos + "%"
            else:
                cond, param = "h.descricao ILIKE %(m)s", f"%{termo}%"
            cur.execute(
                "SELECT h.codigo, h.descricao, lower(h.vigencia) AS inicio, "
                "h.ato_tipo, h.ato_numero, h.ato_ano, c.id AS carga_id "
                "FROM ncm_historico h JOIN carga c ON c.id = h.carga_id "
                f"WHERE h.vigencia @> %(d)s::date AND {cond} "  # nosec B608
                "ORDER BY h.codigo LIMIT 200",
                {"d": data_periodo, "m": param},
            )
            hist = cur.fetchall()
        if hist:
            rows = [
                [_fmt_ncm(r["codigo"]), r["descricao"], str(r["inicio"]),
                 _ato(r["ato_tipo"], r["ato_numero"], r["ato_ano"])]
                for r in hist
            ]
            return ConsultaResposta(
                cols=cols, rows=rows,
                nota=f"fonte: ncm_historico · redação vigente em {periodo}",
            )

    with con.cursor(row_factory=dict_row) as cur:
        if por_codigo:
            cond, param = "v.codigo LIKE %(m)s", digitos + "%"
        else:
            cond, param = "v.descricao ILIKE %(m)s", f"%{termo}%"
        cur.execute(
            "SELECT v.codigo, v.descricao, v.data_inicio, v.ato_tipo, v.ato_numero, "
            "v.ato_ano, c.id AS carga_id, c.data_coleta "
            "FROM ncm_vigente v JOIN carga c ON c.id = v.carga_id "
            f"WHERE {cond} ORDER BY v.codigo LIMIT 200",  # nosec B608
            {"m": param},
        )
        linhas = cur.fetchall()

    rows = [
        [_fmt_ncm(r["codigo"]), r["descricao"], str(r["data_inicio"]),
         _ato(r["ato_tipo"], r["ato_numero"], r["ato_ano"])]
        for r in linhas
    ]
    if linhas:
        prov = linhas[0]
        nota = f"fonte: ncm_vigente · carga #{prov['carga_id']} · coleta {prov['data_coleta']}"
        if periodo:
            nota += f" · período {periodo} respondido pela redação vigente"
    else:
        nota = "fonte: ncm_vigente · nenhum código encontrado"
    return ConsultaResposta(cols=cols, rows=rows, nota=nota)


# --- 2. Alíquota de um estado ------------------------------------------------


@router.get("/aliquota")
def consulta_aliquota(
    usuario: _Operador, con: _Conexao, uf: str, periodo: str | None = None
) -> ConsultaResposta:
    data = _periodo_data(periodo) or date.today()
    cols = ["UF", "período", "alíquota modal", "vigência", "validação", "fonte"]
    with con.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT uf, aliquota_modal, status_validacao, fonte_compilada, "
            "lower(vigencia) AS inicio "
            "FROM aliquota_icms_modal WHERE uf = %(uf)s AND vigencia @> %(d)s::date",
            {"uf": uf.upper(), "d": data},
        )
        r = cur.fetchone()
    if r is None:
        return ConsultaResposta(
            cols=cols, rows=[],
            nota=f"fonte: aliquota_icms_modal · sem vigência para {uf.upper()} no período",
        )
    modal = f"{r['aliquota_modal']:.1f}%".replace(".", ",")
    rows = [[
        r["uf"], periodo or "corrente", modal, f"desde {r['inicio']}",
        _VALIDACAO_LABEL.get(r["status_validacao"], r["status_validacao"]),
        r["fonte_compilada"],
    ]]
    return ConsultaResposta(
        cols=cols, rows=rows,
        nota="fonte: aliquota_icms_modal · modal nominal, sem FECP (playbook §5)",
    )


# --- 3. Por que caiu nessa categoria -----------------------------------------


@router.get("/regras")
def consulta_regras(usuario: _Operador, con: _Conexao, ncm: str) -> ConsultaResposta:
    digitos = re.sub(r"\D", "", ncm or "")
    if len(digitos) < 4:
        raise HTTPException(status_code=400, detail="Informe um NCM com pelo menos 4 dígitos.")
    versao = RepositorioCategoriaSQL(con).versao_vigente()
    cols = ["precedência", "gatilho", "categoria", "detalhe"]
    rows: list[list[Any]] = []

    with con.cursor(row_factory=dict_row) as cur:
        if len(digitos) == 8:
            cur.execute(
                "SELECT categoria, justificativa FROM regras_excecao "
                "WHERE ncm = %(ncm)s AND versao = %(v)s",
                {"ncm": digitos, "v": versao},
            )
            exc = cur.fetchone()
            if exc:
                rows.append(["1. exceção (NCM exato)", _fmt_ncm(digitos),
                             exc["categoria"], exc["justificativa"]])

        cur.execute(
            "SELECT prefixo, categoria FROM regra_ncm_categoria "
            "WHERE versao = %(v)s AND left(%(ncm)s, length(prefixo)) = prefixo "
            "ORDER BY length(prefixo) DESC",
            {"ncm": digitos, "v": versao},
        )
        for i, f in enumerate(cur.fetchall()):
            rotulo = "2. faixa de NCM (vence: mais específica)" if i == 0 else "2. faixa de NCM"
            detalhe = f"regra_ncm_categoria {versao}"
            rows.append([rotulo, f["prefixo"] + "*", f["categoria"], detalhe])

    # Palavra-chave é fallback pela descrição (não pelo NCM) — mostrado como o
    # último elo da precedência, sem enumerar todas as regras de palavra.
    rows.append(["3. palavra-chave", "(pela descrição)", "—",
                 "fallback quando o NCM não resolve → senão, Indefinido"])
    return ConsultaResposta(
        cols=cols, rows=rows,
        nota="precedência do categorizador: exceção → faixa NCM (prefixo mais longo) "
        "→ palavra-chave → Indefinido",
    )


# --- 4. Linhas processadas ---------------------------------------------------


@router.get("/linhas")
def consulta_linhas(
    usuario: _Operador,
    con: _Conexao,
    status: str | None = None,
    uf: str | None = None,
    lote_id: int | None = None,
    pagina: int = 1,
    tamanho_pagina: int = 50,
) -> ConsultaResposta:
    limite = max(1, min(tamanho_pagina, 200))
    offset = max(0, (pagina - 1) * limite)
    condicoes: list[str] = []
    parametros: list[Any] = []
    if lote_id is not None:
        condicoes.append("lote_id = %s")
        parametros.append(lote_id)
    if uf:
        condicoes.append("uf = %s")
        parametros.append(uf.upper())
    if status:
        # Mesma aproximação de routers/lotes.py: casa se qualquer status_* bater.
        condicoes.append(
            "(statuses->>'status_linha' = %s OR statuses->>'status_ncm' = %s "
            "OR statuses->>'status_aliquota' = %s OR statuses->>'status_descricao' = %s)"
        )
        parametros.extend([status] * 4)
    where = f"WHERE {' AND '.join(condicoes)} " if condicoes else ""
    parametros.extend([limite, offset])

    cols = ["lote", "linha", "NCM", "período", "descrição", "UF", "status", "categoria", "alíquota"]
    rows: list[list[Any]] = []
    with con.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT lote_id, numero, originais, enriquecido, statuses, uf "
            f"FROM lote_linha {where}ORDER BY lote_id, numero LIMIT %s OFFSET %s",  # nosec B608
            parametros,
        )
        for r in cur.fetchall():
            orig = r["originais"] or {}
            enr = r["enriquecido"] or {}
            statuses = r["statuses"] or {}
            pior = _pior(statuses.values())
            rows.append([
                r["lote_id"], r["numero"],
                orig.get("NCM", "—"), orig.get("Período", "—"), orig.get("Descrição", "—"),
                r["uf"] or "—", pior,
                enr.get("categoria_macro", "—"), enr.get("aliquota_icms_interna", "—"),
            ])
    return ConsultaResposta(
        cols=cols, rows=rows, nota="fonte: lote_linha (join lote) · statuses do contrato DT-01..04",
    )


def _pior(chaves: Any) -> str:
    """Pior farol de um conjunto de status (severidade cinza<verde<amarelo<vermelho)."""
    from giva.decisao.statuses import pior_status

    lista = [c for c in chaves if c]
    return pior_status(lista) if lista else "—"


# --- 5. Quem mudou o quê -----------------------------------------------------


@router.get("/auditoria")
def consulta_auditoria(
    usuario: _Operador, con: _Conexao, filtro: str | None = None,
    pagina: int = 1, tamanho_pagina: int = 100,
) -> ConsultaResposta:
    limite = max(1, min(tamanho_pagina, 500))
    offset = max(0, (pagina - 1) * limite)
    f = (filtro or "").strip()
    like = f"%{f}%"
    cols = ["quando", "quem", "ação", "alvo", "antes → depois"]
    rows: list[list[Any]] = []
    with con.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT quando, quem, acao, alvo, antes, depois FROM auditoria "
            "WHERE %(f)s = '' OR quem ILIKE %(like)s OR acao ILIKE %(like)s "
            "OR alvo ILIKE %(like)s "
            "ORDER BY quando DESC LIMIT %(lim)s OFFSET %(off)s",
            {"f": f, "like": like, "lim": limite, "off": offset},
        )
        for r in cur.fetchall():
            mudanca = f"{_resumo_json(r['antes'])} → {_resumo_json(r['depois'])}"
            rows.append([str(r["quando"]), r["quem"], r["acao"], r["alvo"], mudanca])
    return ConsultaResposta(
        cols=cols, rows=rows, nota="fonte: auditoria · imutável, ordenada do mais recente",
    )


# --- 6. Situação da base -----------------------------------------------------


@router.get("/saude")
def consulta_saude(usuario: _Operador, con: _Conexao) -> ConsultaResposta:
    def escalar(sql: str, params: Any = None) -> Any:
        row = con.execute(sql, params or ()).fetchone()
        return row[0] if row else 0

    hoje = (date.today(),)
    n_ncm = escalar("SELECT count(*) FROM ncm_vigente")
    n_hist = escalar("SELECT count(*) FROM ncm_historico")
    n_ufs = escalar(
        "SELECT count(*) FROM aliquota_icms_modal WHERE vigencia @> %s::date", hoje
    )
    n_uf_pend = escalar(
        "SELECT count(*) FROM aliquota_icms_modal "
        "WHERE vigencia @> %s::date AND status_validacao <> 'validada'",
        hoje,
    )
    versao = RepositorioCategoriaSQL(con).versao_vigente()
    n_exc = escalar("SELECT count(*) FROM regras_excecao WHERE versao = %s", (versao,))
    n_stag = escalar("SELECT count(*) FROM carga WHERE status = 'staging'")
    n_cargas = escalar("SELECT count(*) FROM carga")
    n_cont = escalar("SELECT count(*) FROM contestacao")
    n_cont_abertas = escalar("SELECT count(*) FROM contestacao WHERE status = 'aberta'")

    cols = ["base", "cobertura", "situação"]
    rows: list[list[Any]] = [
        ["ncm_vigente", f"{n_ncm} códigos", f"{n_stag} carga(s) em staging aguardando revisão"],
        ["ncm_historico", f"{n_hist} redações históricas", "revisão SH / histórico decenal"],
        ["aliquota_icms_modal", f"{n_ufs} UFs com vigência corrente", f"{n_uf_pend} não validadas"],
        ["regras de categoria", f"18 categorias · {versao}", f"{n_exc} exceções ativas"],
        ["cargas", f"{n_cargas} registradas", f"{n_stag} em staging"],
        ["contestações", f"{n_cont} no total", f"{n_cont_abertas} abertas"],
    ]
    return ConsultaResposta(
        cols=cols, rows=rows,
        nota="visão compilada de carga, ncm_vigente, aliquota_icms_modal, "
        "regras_excecao e contestacao",
    )


# --- 7. Avançado (SQL) — somente leitura, defesa em profundidade -------------


@router.post("/sql")
def consulta_sql(dados: SqlRequest, usuario: _Operador, con: _Conexao) -> ConsultaResposta:
    try:
        sql_seguro = preparar_consulta(dados.sql)
    except SqlNaoPermitidoError as exc:
        raise HTTPException(status_code=400, detail=exc.mensagem) from exc

    # Conexão read-only dedicada (camada 1) + read-only tx + statement_timeout.
    ro = psycopg.connect(dsn_readonly(), autocommit=True)
    try:
        ro.execute("SET statement_timeout = '5s'")
        ro.execute("SET default_transaction_read_only = on")
        with ro.cursor() as cur:
            try:
                cur.execute(sql_seguro)
            except psycopg.Error as exc:
                msg = (exc.diag.message_primary if exc.diag else None) or str(exc)
                raise HTTPException(
                    status_code=400, detail=f"Não consegui rodar a consulta: {msg}"
                ) from exc
            cols = [c.name for c in cur.description] if cur.description else []
            linhas = cur.fetchall()
    finally:
        ro.close()

    rows = [[_celula(v) for v in linha] for linha in linhas]
    # Auditoria da execução (camada 5) — na conexão principal (transacional).
    registrar_auditoria(
        con, quem=usuario.email, acao="consulta_sql_executada",
        alvo="consultas/sql", depois={"sql": dados.sql.strip(), "linhas": len(rows)},
    )
    con.commit()
    nota = f"leitura · usuário read-only · {len(rows)} linha(s) · limite {LIMITE_PADRAO}"
    return ConsultaResposta(cols=cols, rows=rows, nota=nota)
