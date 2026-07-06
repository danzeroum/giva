"""Log de auditoria (§3.2) — toda ação sensível do Bloco B grava antes/depois.

A tabela `auditoria` existe desde a migration 0001, mas ficou sem nenhum
gravador até a Fase 4: aprovar uma UF, mudar um parâmetro do motor, criar uma
exceção de categoria ou encaminhar uma contestação passam a registrar aqui —
`quem` (email do usuário autenticado), `acao`, `alvo` e o estado antes/depois.
"""

from __future__ import annotations

from typing import Any

from psycopg import Connection
from psycopg.types.json import Jsonb

_SQL = """
    INSERT INTO auditoria (quem, acao, alvo, antes, depois)
    VALUES (%s, %s, %s, %s, %s)
"""


def registrar(
    con: Connection[Any],
    *,
    quem: str,
    acao: str,
    alvo: str,
    antes: dict[str, Any] | None = None,
    depois: dict[str, Any] | None = None,
) -> None:
    con.execute(
        _SQL,
        (
            quem,
            acao,
            alvo,
            Jsonb(antes) if antes is not None else None,
            Jsonb(depois) if depois is not None else None,
        ),
    )
