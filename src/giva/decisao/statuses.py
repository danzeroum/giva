"""Enumeração dos status que as DTs podem emitir — fonte do contrato com o
front-end (`frontend/src/data/statuses.json`).

Os status nascem aqui (colunas de saída das DTs). O teste de contrato compara
esta enumeração com o JSON do front e falha em divergência, para que um status
novo numa DT futura quebre o CI em vez de aparecer sem cor/rótulo na interface.

`farol_de`/`pior_status` também leem esse mesmo JSON — é o único lugar onde a
cor de um status é decidida, reusado pelo `MontadorSaida` (formatação do
`.xlsx`) para não duplicar a paleta que já existe no front. A leitura é feita
de `data/statuses.json`, uma cópia empacotada dentro do próprio pacote `giva`
(ver `pyproject.toml: [tool.setuptools.package-data]`) — não do arquivo em
`frontend/` diretamente, que não existe mais uma vez que `giva` é instalado
fora do checkout (ex.: `pip install .` num container Docker). O teste de
contrato garante que as duas cópias nunca divirjam.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

from giva.decisao.tabelas import (
    DT01_STATUS_NCM,
    DT02_ALIQUOTA,
    DT03_STATUS_DESCRICAO,
    DT04_STATUS_LINHA,
)

# Colunas de saída que são status (o resto — ex.: formula_efetiva — não é farol).
_COLUNAS_STATUS = frozenset(
    {"status_ncm", "status_aliquota", "status_descricao", "status_linha"}
)

_JSON_FRONT = Path(__file__).resolve().parent / "data" / "statuses.json"
_SEVERIDADE = {"verde": 1, "amarelo": 2, "vermelho": 3}


def statuses_possiveis() -> set[str]:
    """Todos os valores distintos de status_* declarados nas DT-01..04."""
    tabelas = (DT01_STATUS_NCM, DT02_ALIQUOTA, DT03_STATUS_DESCRICAO, DT04_STATUS_LINHA)
    valores: set[str] = set()
    for tabela in tabelas:
        for regra in tabela.regras:
            for coluna, valor in regra.entao.items():
                if coluna in _COLUNAS_STATUS and isinstance(valor, str):
                    valores.add(valor)
    return valores


@lru_cache(maxsize=1)
def _mapa_farol() -> dict[str, str]:
    bruto: dict[str, dict[str, str]] = json.loads(_JSON_FRONT.read_text(encoding="utf-8"))
    return {chave: info["farol"] for chave, info in bruto.items()}


def farol_de(status_key: str) -> str:
    """Cor (verde/amarelo/vermelho) de um status, pelo contrato com o front —
    'verde' para chave desconhecida (mesmo fallback conservador que caberia
    ao `StatusBadge` do front)."""
    return _mapa_farol().get(status_key, "verde")


def pior_status(chaves: Iterable[str]) -> str:
    """A mais severa das chaves de status informadas (vermelho > amarelo >
    verde), espelhando `piorStatus` de `frontend/src/data/statuses.ts`.
    'ok' se `chaves` vier vazio."""
    validas = [chave for chave in chaves if chave]
    if not validas:
        return "ok"
    return max(validas, key=lambda chave: _SEVERIDADE.get(farol_de(chave), 0))
