"""Worker de lotes (ADR-03) — fila no próprio Postgres, sem broker externo.

Concorrência: `FOR UPDATE SKIP LOCKED` deixa N workers consumirem sem se pisar.

Progresso real (Fase 2): o claim é uma transação curta, commitada de imediato
— o `status='processando'` fica visível a qualquer conexão a partir daí (o
`WHERE status = 'recebido'` do `_SQL_CLAIM` já basta pra outro worker não
pegar o mesmo lote de novo, sem precisar segurar o lock além do claim). O
processamento roda em chunks de `_CHUNK_TAM` linhas, cada um persistido e
commitado por si — é isso que torna `linhas_processadas` visível a uma
conexão externa fazendo polling enquanto o lote ainda está em andamento.

Retomabilidade: se o worker cai no meio, o lote fica 'processando' com
`linhas_processadas` parcial — órfão. `reivindicar_presos` reseta esses
lotes para 'recebido' e zera `linhas_processadas`; o reprocessamento sempre
recomeça do zero, nunca retoma do meio no meio do arquivo. Isso é seguro
porque a persistência já é idempotente por `(lote_id, numero)` (ON CONFLICT
DO UPDATE) — reprocessar linhas já feitas não duplica nem corrompe nada, só
custa tempo (aceitável dado o volume do RNF-01).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from psycopg import Connection
from psycopg.types.json import Jsonb

from giva.armazenamento import caminho_saida
from giva.pipeline.leitor import ler_csv
from giva.pipeline.modelo import LinhaLote
from giva.pipeline.persistencia_sql import persistir_linhas
from giva.pipeline.pipeline import Pipeline
from giva.saida.montador import construir_resumo, montar_xlsx

ConstrutorPipeline = Callable[[Connection[Any]], Pipeline]

_CHUNK_TAM = 500

_SQL_ENFILEIRAR = """
    INSERT INTO lote (status, arquivo_entrada, criado_por)
    VALUES ('recebido', %(arquivo)s, %(criado_por)s)
    RETURNING id
"""

_SQL_CLAIM = """
    SELECT id, arquivo_entrada FROM lote
     WHERE status = 'recebido'
     ORDER BY criado_em
     FOR UPDATE SKIP LOCKED
     LIMIT 1
"""

_SQL_PRESOS = "SELECT id FROM lote WHERE status = 'processando' FOR UPDATE SKIP LOCKED"


def enfileirar_lote(con: Connection[Any], *, arquivo_entrada: str, criado_por: str) -> int:
    """Registra um lote 'recebido'. O chamador controla o commit."""
    with con.cursor() as cur:
        cur.execute(_SQL_ENFILEIRAR, {"arquivo": arquivo_entrada, "criado_por": criado_por})
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("INSERT INTO lote ... RETURNING não devolveu id")
        return int(row[0])


def _reivindicar(con: Connection[Any]) -> tuple[int, str] | None:
    """Claim curto: reivindica o próximo lote 'recebido' e já commita o
    'processando', antes de processar uma linha sequer."""
    with con.transaction(), con.cursor() as cur:
        cur.execute(_SQL_CLAIM)
        reivindicado = cur.fetchone()
        if reivindicado is None:
            return None
        lote_id, arquivo = int(reivindicado[0]), str(reivindicado[1])
        cur.execute("UPDATE lote SET status = 'processando' WHERE id = %s", (lote_id,))
    return lote_id, arquivo


def processar_proximo(
    con: Connection[Any], construir_pipeline: ConstrutorPipeline | None = None
) -> int | None:
    """Reivindica e processa o próximo lote 'recebido'. Devolve o id
    processado, ou None se a fila estiver vazia.

    Não é mais uma única transação atômica (ver docstring do módulo): o claim,
    cada chunk e a conclusão commitam em separado, para que o progresso seja
    visível de fora enquanto o lote ainda está sendo processado."""
    construtor = construir_pipeline or _pipeline_padrao
    reivindicado = _reivindicar(con)
    if reivindicado is None:
        return None
    lote_id, arquivo = reivindicado

    lote = ler_csv(Path(arquivo).read_text(encoding="utf-8"))
    total = len(lote.linhas)
    with con.transaction(), con.cursor() as cur:
        cur.execute("UPDATE lote SET total_linhas = %s WHERE id = %s", (total, lote_id))

    pipeline = construtor(con)
    processadas: list[LinhaLote] = []
    for inicio in range(0, total, _CHUNK_TAM):
        bloco_processado = pipeline.processar(lote.linhas[inicio : inicio + _CHUNK_TAM])
        processadas.extend(bloco_processado)
        with con.transaction():
            persistir_linhas(con, lote_id, bloco_processado)
            with con.cursor() as cur:
                cur.execute(
                    "UPDATE lote SET linhas_processadas = linhas_processadas + %s "
                    "WHERE id = %s",
                    (len(bloco_processado), lote_id),
                )

    resumo = construir_resumo(processadas)
    saida = caminho_saida(lote_id)
    Path(saida).write_bytes(montar_xlsx(lote.colunas_originais, processadas))
    with con.transaction(), con.cursor() as cur:
        cur.execute(
            "UPDATE lote SET status = 'concluido', concluido_em = now(), "
            "resumo = %s, arquivo_saida = %s WHERE id = %s",
            (Jsonb(resumo), saida, lote_id),
        )
    return lote_id


def reivindicar_presos(con: Connection[Any]) -> list[int]:
    """Reseta para 'recebido' (e zera `linhas_processadas`) lotes
    'processando' órfãos (sem lock de worker vivo) — o reprocessamento sempre
    recomeça do zero. Um worker ativo segura o lock do seu lote, então
    SKIP LOCKED o ignora — só sobram os presos de fato."""
    with con.transaction(), con.cursor() as cur:
        cur.execute(_SQL_PRESOS)
        ids = [int(r[0]) for r in cur.fetchall()]
        for lote_id in ids:
            cur.execute(
                "UPDATE lote SET status = 'recebido', linhas_processadas = 0 "
                "WHERE id = %s",
                (lote_id,),
            )
    return ids


def _pipeline_padrao(con: Connection[Any]) -> Pipeline:
    from giva.worker.composicao import pipeline_padrao

    return pipeline_padrao(con)
