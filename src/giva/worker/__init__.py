"""Worker de lotes (ADR-03) — fila no Postgres e composição do pipeline."""

from giva.worker.composicao import pipeline_padrao
from giva.worker.fila import (
    enfileirar_lote,
    processar_proximo,
    reivindicar_presos,
)

__all__ = [
    "enfileirar_lote",
    "pipeline_padrao",
    "processar_proximo",
    "reivindicar_presos",
]
