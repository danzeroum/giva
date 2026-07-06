"""RepositorioNCM sobre psycopg — consulta `ncm_vigente` e `ncm_correlacao`.

Join com `carga` para a `data_coleta` da proveniência (RNF-04). O código é
armazenado com 8 dígitos sem pontuação (ver carga), então a consulta usa o
mesmo formato normalizado.
"""

from __future__ import annotations

from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

from giva.ncm.resolvedor import RedacaoVigente

_SQL_VIGENTE = """
    SELECT n.codigo, n.descricao, n.data_inicio,
           n.ato_tipo, n.ato_numero, n.ato_ano,
           c.data_coleta, n.carga_id
      FROM ncm_vigente n
      JOIN carga c ON c.id = n.carga_id
     WHERE n.codigo = %(codigo)s
"""

_SQL_CORRELACAO = "SELECT 1 FROM ncm_correlacao WHERE codigo_anterior = %(codigo)s LIMIT 1"


class RepositorioNCMSQL:
    """Implementação de `RepositorioNCM` sobre uma conexão psycopg."""

    def __init__(self, conexao: Connection[Any]) -> None:
        self._con = conexao

    def buscar_vigente(self, codigo: str) -> RedacaoVigente | None:
        with self._con.cursor(row_factory=dict_row) as cur:
            cur.execute(_SQL_VIGENTE, {"codigo": codigo})
            r = cur.fetchone()
        if r is None:
            return None
        return RedacaoVigente(
            codigo=r["codigo"],
            descricao=r["descricao"],
            data_inicio=r["data_inicio"],
            ato_tipo=r["ato_tipo"],
            ato_numero=r["ato_numero"],
            ato_ano=r["ato_ano"],
            data_coleta=r["data_coleta"],
            carga_id=r["carga_id"],
        )

    def existe_correlacao(self, codigo: str) -> bool:
        with self._con.cursor() as cur:
            cur.execute(_SQL_CORRELACAO, {"codigo": codigo})
            return cur.fetchone() is not None
