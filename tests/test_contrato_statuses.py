"""Contrato front↔backend: o conjunto de status emitidos pelas DT-01..04 tem de
ser exatamente o declarado em `frontend/src/data/statuses.json` (cor/rótulo).
Um status novo numa DT sem entrada no JSON quebra o CI, não a interface."""

from __future__ import annotations

import json
from pathlib import Path

from giva.decisao.statuses import statuses_possiveis

_JSON = (
    Path(__file__).resolve().parents[1]
    / "frontend" / "src" / "data" / "statuses.json"
)


def test_dts_e_front_declaram_o_mesmo_conjunto_de_status():
    do_front = set(json.loads(_JSON.read_text(encoding="utf-8")).keys())
    das_dts = statuses_possiveis()
    assert das_dts == do_front, (
        f"faltando no front: {das_dts - do_front}; "
        f"sobrando no front: {do_front - das_dts}"
    )
