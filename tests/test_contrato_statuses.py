"""Contrato front↔backend: todo status que uma DT pode emitir precisa ter
cor/rótulo em `frontend/src/data/statuses.json`. Um status novo numa DT sem
entrada no JSON quebra o CI, não a interface.

O front PODE ter status a mais (reservados/para exibição — ex.:
`alerta_similaridade`, o nível 'leve' que a DT-03 v2 ainda não emite mas que um
refinamento futuro pode voltar a usar). O invariante crítico é a inclusão:
`das_dts ⊆ do_front`."""

from __future__ import annotations

import json
from pathlib import Path

from giva.decisao.statuses import statuses_possiveis

_JSON = (
    Path(__file__).resolve().parents[1]
    / "frontend" / "src" / "data" / "statuses.json"
)
_JSON_PACOTE = (
    Path(__file__).resolve().parents[1]
    / "src" / "giva" / "decisao" / "data" / "statuses.json"
)


def test_todo_status_das_dts_tem_cor_no_front():
    do_front = set(json.loads(_JSON.read_text(encoding="utf-8")).keys())
    das_dts = statuses_possiveis()
    faltando = das_dts - do_front
    assert not faltando, f"status emitidos por DT sem entrada no front: {faltando}"


def test_copia_empacotada_identica_ao_front():
    """`giva.decisao.statuses` lê `data/statuses.json` — uma cópia empacotada
    dentro do pacote (sobrevive a `pip install .` fora do checkout, ver
    `pyproject.toml`) — não o arquivo do front diretamente. Uma divergência
    aqui faz o backend instalado (Docker) mostrar cor/rótulo diferente do que
    o front exibe."""
    assert _JSON_PACOTE.read_text(encoding="utf-8") == _JSON.read_text(encoding="utf-8"), (
        f"{_JSON_PACOTE} divergiu de {_JSON} — copie o conteúdo atualizado do "
        "front para a cópia empacotada."
    )
