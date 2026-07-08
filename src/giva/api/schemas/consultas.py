"""Schemas do módulo "Consultas prontas" (Bloco B — Banco de dados).

Todo resultado tabular usa o mesmo envelope genérico (`ConsultaResposta`), para
o front renderizar qualquer consulta com o mesmo componente e copiar TSV para o
Excel sem conhecer o formato de cada uma.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ConsultaResposta(BaseModel):
    cols: list[str]
    rows: list[list[Any]]
    nota: str


class SqlRequest(BaseModel):
    sql: str
