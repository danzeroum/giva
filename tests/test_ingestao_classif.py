"""Unidade da ingestão do Classif — a data de coleta vem da marca do próprio
documento (nunca `date.today()`, para não quebrar a reprodutibilidade RNF-04)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from giva.rotinas.ingestao_classif import _data_coleta


def test_data_coleta_le_marca_do_documento():
    doc = {"Data_Ultima_Atualizacao_NCM": "Vigente em 02/07/2026"}
    assert _data_coleta(doc, Path("/inexistente.json")) == date(2026, 7, 2)


def test_data_coleta_cai_no_mtime_quando_marca_ausente(tmp_path):
    arquivo = tmp_path / "snap.json"
    arquivo.write_text("{}", encoding="utf-8")
    # sem marca no doc → usa mtime do arquivo (uma data válida, não estoura)
    assert isinstance(_data_coleta({}, arquivo), date)
