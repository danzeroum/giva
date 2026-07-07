"""Fixtures compartilhadas. `conexao` dá uma conexão psycopg para os testes de
integração e é **pulada** quando não há `DATABASE_URL` (unidade roda sem banco).
Cada teste roda numa transação revertida no fim — não polui o banco."""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

import pytest


@pytest.fixture
def conexao() -> Iterator[Any]:
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("teste de integração exige DATABASE_URL (Postgres)")
    import psycopg

    from giva.config import dsn_psycopg

    con = psycopg.connect(dsn_psycopg())
    try:
        yield con
    finally:
        con.rollback()  # desfaz tudo o que o teste fez
        con.close()
