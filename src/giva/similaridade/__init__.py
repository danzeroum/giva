"""Módulo E — avaliação de similaridade de descrição (RF-29)."""

from giva.similaridade.avaliador import (
    AvaliadorSimilaridade,
    ProvenienciaSimilaridade,
    ResultadoSimilaridade,
)
from giva.similaridade.normalizacao import (
    normalizar_descricao,
    score_similaridade,
)

__all__ = [
    "AvaliadorSimilaridade",
    "ProvenienciaSimilaridade",
    "ResultadoSimilaridade",
    "normalizar_descricao",
    "score_similaridade",
]
