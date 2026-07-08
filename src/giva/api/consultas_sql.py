"""Defesa em profundidade do SQL livre de "Consultas prontas → Avançado (SQL)".

Este módulo é a **camada de aplicação** da defesa (camadas 2–4 do handoff); ele
não toca o banco — recebe o texto digitado e devolve uma consulta segura, ou
levanta `SqlNaoPermitidoError` com uma mensagem em linguagem de leigo. As demais
camadas ficam no roteador (`consultas.py`): usuário Postgres read-only dedicado
(camada 1), transação read-only + `statement_timeout` (camada 4) e auditoria de
cada execução (camada 5).

Regras (todas conservadoras — na dúvida, recusa):
  - uma única instrução, começando por SELECT (rejeita `;` extra, CTEs `WITH`,
    qualquer DML);
  - sem comentários (`--`, `/* */`, `#`) — poderiam esconder payload;
  - sem palavras de escrita/DDL nem `pg_*`/`information_schema`;
  - só tabelas da whitelist podem aparecer após FROM/JOIN;
  - `LIMIT` é imposto por fora (envelopando a consulta), independente do que o
    usuário escreveu.
"""

from __future__ import annotations

import re

# Whitelist de tabelas legíveis (exatamente a do handoff).
TABELAS_PERMITIDAS: frozenset[str] = frozenset(
    {
        "ncm_vigente",
        "ncm_historico",
        "aliquota_icms_modal",
        "carga",
        "regras_excecao",
        "regra_ncm_categoria",
        "regra_palavra_categoria",
        "categoria",
        "parametro",
        "auditoria",
        "lote",
        "lote_linha",
        "contestacao",
    }
)

LIMITE_PADRAO = 500

# Palavras que jamais aparecem numa leitura pura (escrita, DDL, controle de
# sessão/transação, cópia). Casadas como palavra inteira (\b) — "offset" não
# dispara "set", "created_em" não dispara "create".
_PROIBIDAS = (
    "insert", "update", "delete", "drop", "alter", "create", "truncate",
    "grant", "revoke", "copy", "call", "merge", "into", "vacuum", "analyze",
    "reindex", "lock", "listen", "notify", "set", "reset", "with", "do",
    "returning", "comment", "cluster", "refresh", "prepare", "execute",
)
_RE_PROIBIDAS = re.compile(r"\b(" + "|".join(_PROIBIDAS) + r")\b", re.IGNORECASE)
_RE_FONTES = re.compile(r"\b(?:from|join)\s+([a-zA-Z_][\w.]*)", re.IGNORECASE)
_RE_COMECA_SELECT = re.compile(r"^select\b", re.IGNORECASE)
_RE_COMENTARIO = re.compile(r"--|/\*|\*/|#")


class SqlNaoPermitidoError(ValueError):
    """SQL recusado pela política de leitura. A `mensagem` é amigável ao leigo."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


def preparar_consulta(sql: str, *, limite: int = LIMITE_PADRAO) -> str:
    """Valida `sql` e devolve uma consulta SELECT segura, com `LIMIT` imposto.

    Levanta `SqlNaoPermitidoError` (com mensagem de leigo) se algo não passar.
    """
    texto = (sql or "").strip()
    if not texto:
        raise SqlNaoPermitidoError("Escreva uma consulta SELECT.")

    if _RE_COMENTARIO.search(texto):
        raise SqlNaoPermitidoError("Comentários não são permitidos na consulta.")

    # Uma instrução só: tira um `;` final e recusa se sobrar algum no meio.
    texto = texto.rstrip(";").strip()
    if ";" in texto:
        raise SqlNaoPermitidoError("Uma consulta por vez, por favor (sem “;”).")

    if not _RE_COMECA_SELECT.match(texto):
        raise SqlNaoPermitidoError("Somente leitura: a consulta precisa começar com SELECT.")

    proibida = _RE_PROIBIDAS.search(texto)
    if proibida is not None:
        raise SqlNaoPermitidoError(
            f"Somente leitura: a palavra “{proibida.group(1).lower()}” não é permitida."
        )

    if re.search(r"pg_|information_schema", texto, re.IGNORECASE):
        raise SqlNaoPermitidoError("Tabelas internas do banco não podem ser consultadas.")

    fontes = [t.lower() for t in _RE_FONTES.findall(texto)]
    if not fontes:
        raise SqlNaoPermitidoError("A consulta precisa referenciar ao menos uma tabela (FROM).")
    for tabela in fontes:
        if tabela not in TABELAS_PERMITIDAS:
            disponiveis = " · ".join(sorted(TABELAS_PERMITIDAS))
            raise SqlNaoPermitidoError(
                f"Tabela “{tabela}” não é consultável. Disponíveis: {disponiveis}."
            )

    # LIMIT imposto por fora — vale mesmo se o usuário escreveu outro LIMIT.
    return f"SELECT * FROM ({texto}) AS giva_consulta LIMIT {int(limite)}"
