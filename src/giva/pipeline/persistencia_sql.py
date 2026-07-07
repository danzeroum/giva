"""Persistência do lote e das linhas (§3.2, §5.3) via psycopg.

Registra, por linha, `originais`, `enriquecido`, `statuses`, `proveniencia` e
`regras_disparadas` — este último é o insumo do process mining do §5.3, gravado
desde já para não exigir retrofit caro depois. Não faz commit: quem chama
controla a transação (o worker futuro reusa isto sem mudança).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from psycopg import Connection
from psycopg.types.json import Jsonb

from giva.pipeline.modelo import LinhaLote

_SQL_ABRIR = """
    INSERT INTO lote (status, arquivo_entrada, criado_por)
    VALUES ('processando', %(arquivo)s, %(criado_por)s)
    RETURNING id
"""

_SQL_LINHA = """
    INSERT INTO lote_linha
        (lote_id, numero, originais, enriquecido, statuses,
         proveniencia, regras_disparadas, uf)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (lote_id, numero) DO UPDATE SET
        originais = EXCLUDED.originais,
        enriquecido = EXCLUDED.enriquecido,
        statuses = EXCLUDED.statuses,
        proveniencia = EXCLUDED.proveniencia,
        regras_disparadas = EXCLUDED.regras_disparadas,
        uf = EXCLUDED.uf
"""

_SQL_CONCLUIR = """
    UPDATE lote
       SET status = 'concluido', arquivo_saida = %(saida)s,
           concluido_em = now(), resumo = %(resumo)s
     WHERE id = %(id)s
"""


def abrir_lote(con: Connection[Any], *, arquivo_entrada: str, criado_por: str) -> int:
    with con.cursor() as cur:
        cur.execute(_SQL_ABRIR, {"arquivo": arquivo_entrada, "criado_por": criado_por})
        linha = cur.fetchone()
        if linha is None:
            raise RuntimeError("INSERT INTO lote ... RETURNING não devolveu id")
        return int(linha[0])


def _statuses(linha: LinhaLote) -> dict[str, str]:
    """`status_linha` é atributo de `LinhaLote`, não uma chave de
    `enriquecimento` — checar `"status_linha" in linha.enriquecimento` (como
    antes) nunca era verdadeiro, então a coluna `statuses` persistida nunca
    trazia esse campo. `status_descricao` também faltava aqui (Fase 3:
    `GET /lotes/{id}/linhas` lê esta coluna para computar o pior status por
    linha — sem os dois, o farol mostrado divergia do resumo agregado, que lê
    `LinhaLote` fresco em vez desta coluna)."""
    statuses = {"status_linha": linha.status_linha}
    for chave in ("status_ncm", "status_aliquota", "status_descricao"):
        if chave in linha.enriquecimento:
            statuses[chave] = linha.enriquecimento[chave]
    return statuses


def persistir_linhas(
    con: Connection[Any], lote_id: int, linhas: Sequence[LinhaLote]
) -> None:
    with con.cursor() as cur:
        cur.executemany(
            _SQL_LINHA,
            [
                (
                    lote_id,
                    linha.numero,
                    Jsonb(linha.originais),
                    Jsonb(linha.enriquecimento),
                    Jsonb(_statuses(linha)),
                    Jsonb(linha.proveniencia),
                    Jsonb(linha.regras_disparadas),
                    linha.uf,
                )
                for linha in linhas
            ],
        )


def concluir_lote(
    con: Connection[Any], lote_id: int, *, arquivo_saida: str, resumo: dict[str, Any]
) -> None:
    with con.cursor() as cur:
        cur.execute(
            _SQL_CONCLUIR,
            {"id": lote_id, "saida": arquivo_saida, "resumo": json.dumps(resumo)},
        )
