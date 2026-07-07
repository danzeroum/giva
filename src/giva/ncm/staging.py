"""Sala de espera das cargas de NCM (Fase 5): staging → diff → promover/rejeitar.

Uma carga ingerida do Classif entra em `ncm_vigente_staging` com
`carga.status='staging'` — o motor de enriquecimento continua lendo só
`ncm_vigente` (produção), então nada aqui afeta resultado até ser **promovido**
por um humano (revisão antes de valer — princípio da base de referência).

Fluxo:
1. `carregar_staging` — ingere para staging (não toca produção).
2. `diff_carga` — mostra o que muda vs. a produção atual (novos/removidos/alterados).
3. `promover_carga` — troca a produção pelo conteúdo do staging (numa transação).
   `rejeitar_carga` — descarta o staging e marca a carga como rejeitada.

Nenhuma função faz commit — quem chama controla a transação (mesma convenção de
`ncm/carga.py`).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

from giva.ncm.classif import parsear_registros


class ErroStaging(Exception):
    """Base dos erros da sala de espera."""


class CargaNaoEncontradaError(ErroStaging):
    def __init__(self, carga_id: int) -> None:
        super().__init__(f"Carga {carga_id} não encontrada.")


class CargaNaoEmStagingError(ErroStaging):
    """Promover/rejeitar exige status 'staging' — já promovida/rejeitada não volta."""

    def __init__(self, carga_id: int, status: str) -> None:
        super().__init__(
            f"Carga {carga_id} está em status {status!r}; só cargas em 'staging' "
            f"podem ser promovidas ou rejeitadas."
        )


_SQL_CARGA_STAGING = """
    INSERT INTO carga
        (fonte, arquivo_bruto, hash_arquivo, data_coleta, status)
    VALUES ('classif_json', %(arquivo)s, %(hash)s, %(data_coleta)s, 'staging')
    RETURNING id
"""

_SQL_STAGING = """
    INSERT INTO ncm_vigente_staging
        (carga_id, codigo, descricao, data_inicio, ato_tipo, ato_numero, ato_ano)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""


def carregar_staging(
    con: Connection[Any],
    doc: Mapping[str, Any],
    *,
    arquivo: str,
    hash_arquivo: str,
    data_coleta: date,
) -> tuple[int, int]:
    """Ingere os NCM de 8 dígitos de `doc` para o staging (não toca produção).
    Devolve (carga_id, n)."""
    with con.cursor() as cur:
        cur.execute(
            _SQL_CARGA_STAGING,
            {"arquivo": arquivo, "hash": hash_arquivo, "data_coleta": data_coleta},
        )
        linha = cur.fetchone()
        if linha is None:
            raise RuntimeError("INSERT INTO carga ... RETURNING não devolveu id")
        carga_id = int(linha[0])

        registros = list(parsear_registros(doc))
        cur.executemany(
            _SQL_STAGING,
            [
                (carga_id, r.codigo, r.descricao, r.vigencia_inicio,
                 r.ato_tipo, r.ato_numero, r.ato_ano)
                for r in registros
            ],
        )
    return carga_id, len(registros)


@dataclass(frozen=True)
class DiffCarga:
    """Resumo do que a carga em staging muda em relação à produção atual."""

    carga_id: int
    total_producao: int
    total_staging: int
    novos: int
    removidos: int
    alterados: int
    amostra_novos: list[str] = field(default_factory=list)
    amostra_removidos: list[str] = field(default_factory=list)
    amostra_alterados: list[str] = field(default_factory=list)


def _descricoes(con: Connection[Any], sql: str, params: dict[str, Any]) -> dict[str, str]:
    with con.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return {r["codigo"]: r["descricao"] for r in cur.fetchall()}


def diff_carga(con: Connection[Any], carga_id: int, *, amostra: int = 20) -> DiffCarga:
    """Compara o staging da carga com a produção (`ncm_vigente`)."""
    _exigir_status(con, carga_id, "staging")
    producao = _descricoes(con, "SELECT codigo, descricao FROM ncm_vigente", {})
    staging = _descricoes(
        con,
        "SELECT codigo, descricao FROM ncm_vigente_staging WHERE carga_id = %(id)s",
        {"id": carga_id},
    )
    novos = sorted(set(staging) - set(producao))
    removidos = sorted(set(producao) - set(staging))
    alterados = sorted(
        c for c in (set(staging) & set(producao)) if staging[c] != producao[c]
    )
    return DiffCarga(
        carga_id=carga_id,
        total_producao=len(producao),
        total_staging=len(staging),
        novos=len(novos),
        removidos=len(removidos),
        alterados=len(alterados),
        amostra_novos=novos[:amostra],
        amostra_removidos=removidos[:amostra],
        amostra_alterados=alterados[:amostra],
    )


def promover_carga(con: Connection[Any], carga_id: int, por: str) -> int:
    """Troca a produção (`ncm_vigente`) pelo conteúdo do staging desta carga,
    numa transação. Marca a carga como promovida e consome o staging. Devolve o
    número de códigos promovidos. Não faz commit."""
    _exigir_status(con, carga_id, "staging")
    with con.cursor() as cur:
        cur.execute("DELETE FROM ncm_vigente")
        cur.execute(
            "INSERT INTO ncm_vigente "
            "(codigo, descricao, data_inicio, ato_tipo, ato_numero, ato_ano, carga_id) "
            "SELECT codigo, descricao, data_inicio, ato_tipo, ato_numero, ato_ano, carga_id "
            "FROM ncm_vigente_staging WHERE carga_id = %(id)s",
            {"id": carga_id},
        )
        promovidos = cur.rowcount
        cur.execute(
            "UPDATE carga SET status='promovida', promovido_em=now(), "
            "promovido_por=%(por)s WHERE id=%(id)s",
            {"por": por, "id": carga_id},
        )
        cur.execute("DELETE FROM ncm_vigente_staging WHERE carga_id=%(id)s", {"id": carga_id})
    return int(promovidos)


def rejeitar_carga(con: Connection[Any], carga_id: int, por: str) -> None:
    """Descarta o staging da carga e marca-a como rejeitada. Não faz commit."""
    _exigir_status(con, carga_id, "staging")
    with con.cursor() as cur:
        cur.execute(
            "UPDATE carga SET status='rejeitada', rejeitado_em=now(), "
            "rejeitado_por=%(por)s WHERE id=%(id)s",
            {"por": por, "id": carga_id},
        )
        cur.execute("DELETE FROM ncm_vigente_staging WHERE carga_id=%(id)s", {"id": carga_id})


def _exigir_status(con: Connection[Any], carga_id: int, esperado: str) -> None:
    with con.cursor() as cur:
        cur.execute("SELECT status FROM carga WHERE id=%(id)s", {"id": carga_id})
        linha = cur.fetchone()
    if linha is None:
        raise CargaNaoEncontradaError(carga_id)
    if linha[0] != esperado:
        raise CargaNaoEmStagingError(carga_id, str(linha[0]))
