"""Pipeline de enriquecimento — uma sequência ordenada de etapas (C3).

Contrato: recebe o lote já aberto (as linhas). O caminho é síncrono; o worker
assíncrono da ADR-03 (lotes grandes) reusa o mesmo `processar` sem mudança,
apenas variando quem abre o lote e persiste.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from giva.pipeline.etapas import Etapa
from giva.pipeline.modelo import LinhaLote


class Pipeline:
    def __init__(self, etapas: Sequence[Etapa]) -> None:
        self._etapas = tuple(etapas)

    def processar(self, linhas: Iterable[LinhaLote]) -> list[LinhaLote]:
        processadas = list(linhas)
        for linha in processadas:
            for etapa in self._etapas:
                etapa.processar(linha)
        return processadas
