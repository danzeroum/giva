"""GET /saude — health check (conecta e roda SELECT 1)."""

from __future__ import annotations

from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends

from giva.api.deps import get_conexao

router = APIRouter(tags=["saude"])


@router.get("/saude")
def saude(con: Annotated[psycopg.Connection, Depends(get_conexao)]) -> dict[str, str]:
    con.execute("SELECT 1")
    return {"status": "ok"}
