"""Integração das Consultas prontas (exige Postgres — pulado sem DATABASE_URL).

Chama as funções das rotas diretamente (elas recebem `usuario`/`con`), sem
subir o servidor. Verifica o envelope genérico {cols, rows, nota} e o caminho
feliz + a recusa do SQL livre contra o banco real (seed das migrations).
"""

from __future__ import annotations

from typing import Any

import pytest

from giva.api.routers import consultas
from giva.api.schemas.consultas import SqlRequest
from giva.api.seguranca import UsuarioToken

_OPERADOR = UsuarioToken(id=1, email="op@giva.test", papel="operador")


def test_saude_devolve_as_seis_bases(conexao: Any) -> None:
    r = consultas.consulta_saude(_OPERADOR, conexao)
    assert r.cols == ["base", "cobertura", "situação"]
    bases = [linha[0] for linha in r.rows]
    assert "ncm_vigente" in bases
    assert "aliquota_icms_modal" in bases
    assert len(r.rows) == 6


def test_sql_livre_le_tabela_permitida(conexao: Any) -> None:
    r = consultas.consulta_sql(SqlRequest(sql="SELECT count(*) FROM carga"), _OPERADOR, conexao)
    assert r.rows and isinstance(r.rows[0][0], int)
    assert "read-only" in r.nota


def test_sql_livre_recusa_escrita(conexao: Any) -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        consultas.consulta_sql(SqlRequest(sql="DELETE FROM carga"), _OPERADOR, conexao)
    assert exc.value.status_code == 400


def test_regras_exige_ncm_minimo(conexao: Any) -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        consultas.consulta_regras(_OPERADOR, conexao, ncm="12")
    assert exc.value.status_code == 400
