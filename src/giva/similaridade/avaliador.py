"""AvaliadorSimilaridade (Módulo E — RF-29), Sprint 3.

Compara a descrição de entrada com a descrição oficial do NCM e classifica a
divergência em três níveis via DT-03. Os limiares T_ok/T_rev vêm da tabela
`parametro` em runtime (RF-24) — se ausentes, a avaliação falha explícita
(`ParametroAusenteError`, já lançado pelo interpretador). NUNCA constantes.

Calibração (portão 7.1): até a amostra de ~500 descrições rotulada chegar, o
componente roda com os defaults da migration 0002 (t_ok=0.85, t_rev=0.60) e o
portão fica formalmente pendente — bloqueia o piloto, não o desenvolvimento.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from giva.decisao.interpretador import avaliar
from giva.decisao.tabelas import DT03_STATUS_DESCRICAO
from giva.similaridade.normalizacao import score_similaridade


class RepositorioParametros(Protocol):
    def thresholds_similaridade(self) -> dict[str, float]:
        """{'t_ok': ..., 't_rev': ...} da tabela `parametro`. Chaves ausentes
        fazem a DT-03 falhar explícito na avaliação (RF-24)."""
        ...


@dataclass(frozen=True)
class ProvenienciaSimilaridade:
    regra: str  # DT-03_status_descricao@1.0#regraN
    versao: str
    score: str  # score formatado (3 casas), determinístico


@dataclass(frozen=True)
class ResultadoSimilaridade:
    score: float
    status_descricao: str
    proveniencia: ProvenienciaSimilaridade


class AvaliadorSimilaridade:
    def __init__(self, repositorio: RepositorioParametros) -> None:
        self._repo = repositorio

    def avaliar(self, descricao_entrada: str, descricao_oficial: str) -> ResultadoSimilaridade:
        score = score_similaridade(descricao_entrada, descricao_oficial)
        thresholds = self._repo.thresholds_similaridade()  # ausência → DT falha explícito
        decisao = avaliar(DT03_STATUS_DESCRICAO, {"score": score}, thresholds)
        return ResultadoSimilaridade(
            score=score,
            status_descricao=decisao.saidas["status_descricao"],
            proveniencia=ProvenienciaSimilaridade(decisao.proveniencia, "1.0", f"{score:.3f}"),
        )
