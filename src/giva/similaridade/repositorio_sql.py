"""RepositorioParametros sobre psycopg — lê os thresholds da tabela `parametro`.

Só devolve as chaves que existem; a ausência de t_ok/t_rev vira falha explícita
na DT-03 (RF-24), não um default silencioso.
"""

from __future__ import annotations

from typing import Any

from psycopg import Connection

_SQL = "SELECT nome, valor FROM parametro WHERE nome IN ('t_ok', 't_rev')"


class RepositorioParametrosSQL:
    def __init__(self, conexao: Connection[Any]) -> None:
        self._con = conexao

    def thresholds_similaridade(self) -> dict[str, float]:
        with self._con.cursor() as cur:
            cur.execute(_SQL)
            return {str(nome): float(valor) for nome, valor in cur.fetchall()}
