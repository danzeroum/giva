"""Carga do snapshot vigente do Classif em `ncm_vigente` (Sprint 2).

Fluxo mínimo do plano §5.2 para a Fase 1: registra a `carga` com proveniência
(§3.2 — nenhuma linha sem origem), insere os NCM de 8 dígitos e promove. O
staging completo e a tela de revisão humana ficam para quando houver UI (item 4
da orientação da S2). A carga não faz commit — quem chama controla a transação.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import date
from typing import Any

from psycopg import Connection

from giva.ncm.classif import parsear_posicoes, parsear_registros

_SQL_CARGA = """
    INSERT INTO carga
        (fonte, arquivo_bruto, hash_arquivo, data_coleta, promovido_em, promovido_por)
    VALUES ('classif_json', %(arquivo)s, %(hash)s, %(data_coleta)s, now(), 'carga-classif')
    RETURNING id
"""

_SQL_NCM = """
    INSERT INTO ncm_vigente
        (codigo, descricao, data_inicio, ato_tipo, ato_numero, ato_ano, carga_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""


def sha256_arquivo(caminho: str) -> str:
    """Hash do arquivo bruto para rastreabilidade (§3.2)."""
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def carregar_snapshot_vigente(
    con: Connection[Any],
    doc: Mapping[str, Any],
    *,
    arquivo: str,
    hash_arquivo: str,
    data_coleta: date,
) -> tuple[int, int]:
    """Insere a carga e os NCM de 8 dígitos de `doc`. Devolve (carga_id, n)."""
    with con.cursor() as cur:
        cur.execute(
            _SQL_CARGA,
            {"arquivo": arquivo, "hash": hash_arquivo, "data_coleta": data_coleta},
        )
        linha = cur.fetchone()
        if linha is None:  # RETURNING sempre devolve; guarda de invariante
            raise RuntimeError("INSERT INTO carga ... RETURNING não devolveu id")
        carga_id = int(linha[0])

        registros = list(parsear_registros(doc))
        cur.executemany(
            _SQL_NCM,
            [
                (
                    r.codigo,
                    r.descricao,
                    r.vigencia_inicio,
                    r.ato_tipo,
                    r.ato_numero,
                    r.ato_ano,
                    carga_id,
                )
                for r in registros
            ],
        )
    return carga_id, len(registros)


def carregar_posicoes(
    con: Connection[Any], doc: Mapping[str, Any], carga_id: int
) -> int:
    """Full refresh de `ncm_posicao` (subposições de 6 dígitos) a partir de `doc`,
    associadas à `carga_id`. Não faz commit. Devolve o número de subposições."""
    posicoes = list(parsear_posicoes(doc))
    with con.cursor() as cur:
        cur.execute("DELETE FROM ncm_posicao")
        cur.executemany(
            "INSERT INTO ncm_posicao (prefixo, descricao, carga_id) VALUES (%s, %s, %s)",
            [(prefixo, descricao, carga_id) for prefixo, descricao in posicoes],
        )
    return len(posicoes)
