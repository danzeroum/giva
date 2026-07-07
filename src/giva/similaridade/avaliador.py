"""AvaliadorSimilaridade (Módulo E — RF-29).

Classifica a **divergência de descrição** entre a descrição informada e a oficial
do NCM. Decisão do escritório (v1): a divergência é medida por **conflito de
categoria** — o NCM aponta uma categoria e a descrição aponta outra (ex.: NCM de
rolamento + 'martelo'). A DT-03 decide o status a partir desse conflito.

O score textual (Jaccard) é mantido apenas como **informação** na proveniência
— ele NÃO decide o status. A similaridade por sobreposição de tokens não replica
o julgamento humano contra descrições tarifárias genéricas ('- Partes',
'-- Outros'); a semântica/IA fica para a v2 (PRD §12.5).
"""

from __future__ import annotations

from dataclasses import dataclass

from giva.decisao.interpretador import avaliar
from giva.decisao.tabelas import DT03_STATUS_DESCRICAO
from giva.similaridade.normalizacao import score_similaridade


@dataclass(frozen=True)
class ProvenienciaSimilaridade:
    regra: str  # DT-03_status_descricao@2.0#regraN
    versao: str
    score: str  # score Jaccard formatado (3 casas) — informativo, não decide


@dataclass(frozen=True)
class ResultadoSimilaridade:
    score: float
    status_descricao: str
    proveniencia: ProvenienciaSimilaridade


class AvaliadorSimilaridade:
    def avaliar(
        self,
        descricao_entrada: str,
        descricao_oficial: str,
        *,
        conflito_categoria: bool,
    ) -> ResultadoSimilaridade:
        score = score_similaridade(descricao_entrada, descricao_oficial)  # informativo
        decisao = avaliar(DT03_STATUS_DESCRICAO, {"conflito_categoria": conflito_categoria})
        return ResultadoSimilaridade(
            score=score,
            status_descricao=decisao.saidas["status_descricao"],
            proveniencia=ProvenienciaSimilaridade(decisao.proveniencia, "2.0", f"{score:.3f}"),
        )
