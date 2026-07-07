"""Composição do pipeline padrão sobre uma conexão psycopg (raiz de composição).

Reúne os cinco componentes com seus repositórios SQL. É aqui — na borda — que
os componentes são ligados; eles seguem sem se conhecer.
"""

from __future__ import annotations

from typing import Any

from psycopg import Connection

from giva.aliquota.repositorio_sql import RepositorioAliquotaSQL
from giva.aliquota.resolvedor import ResolutorAliquota
from giva.categoria.categorizador import Categorizador
from giva.categoria.repositorio_sql import RepositorioCategoriaSQL
from giva.ncm.repositorio_sql import RepositorioNCMSQL
from giva.ncm.resolvedor import ResolutorNCM
from giva.pipeline.etapas import (
    EtapaAliquota,
    EtapaCategoria,
    EtapaNCM,
    EtapaNormalizacao,
    EtapaSimilaridade,
)
from giva.pipeline.pipeline import Pipeline
from giva.similaridade.avaliador import AvaliadorSimilaridade


def pipeline_padrao(con: Connection[Any], *, aceita_nao_validada: bool = False) -> Pipeline:
    return Pipeline(
        [
            EtapaNormalizacao(),
            EtapaNCM(ResolutorNCM(RepositorioNCMSQL(con))),
            EtapaAliquota(
                ResolutorAliquota(
                    RepositorioAliquotaSQL(con), aceita_nao_validada=aceita_nao_validada
                )
            ),
            EtapaCategoria(Categorizador(RepositorioCategoriaSQL(con))),
            EtapaSimilaridade(AvaliadorSimilaridade()),
        ]
    )
