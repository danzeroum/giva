"""Loop do worker de lotes (ADR-03) — `python -m giva.worker`.

Consome a fila continuamente: processa o próximo lote 'recebido' e, quando a
fila está vazia, dorme antes de tentar de novo. A cada `_CICLOS_RECLAIM`
voltas do loop, roda `reivindicar_presos` para destravar lotes 'processando'
órfãos (worker anterior morto no meio — Fase 2, progresso real).
"""

from __future__ import annotations

import time

import psycopg

from giva.config import dsn_psycopg
from giva.worker.fila import processar_proximo, reivindicar_presos

_ESPERA_FILA_VAZIA = 2.0
_CICLOS_RECLAIM = 30


def main() -> None:
    con = psycopg.connect(dsn_psycopg())
    ciclo = 0
    try:
        while True:
            ciclo += 1
            if ciclo % _CICLOS_RECLAIM == 0:
                reivindicar_presos(con)
            lote_id = processar_proximo(con)
            if lote_id is None:
                time.sleep(_ESPERA_FILA_VAZIA)
    finally:
        con.close()


if __name__ == "__main__":
    main()
