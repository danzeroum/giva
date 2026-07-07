"""DT-02 no GIVA: alíquota modal SEM FECP. A tabela só libera a fórmula
`modal` — nunca `modal_mais_fecp` (decisão GIVA §3)."""

from __future__ import annotations

from giva.decisao.interpretador import avaliar
from giva.decisao.tabelas import DT02_ALIQUOTA


def _decidir(vigencia_encontrada: bool, status_validacao):
    return avaliar(
        DT02_ALIQUOTA,
        {
            "vigencia_encontrada": vigencia_encontrada,
            "status_validacao": status_validacao,
        },
    ).saidas


def test_sem_vigencia_periodo_sem_cobertura():
    s = _decidir(False, None)
    assert s["status_aliquota"] == "periodo_sem_cobertura"
    assert s["formula_efetiva"] is None


def test_vigencia_nao_validada_pendente():
    s = _decidir(True, "pendente_validacao")
    assert s["status_aliquota"] == "pendente_validacao_uf"
    assert s["formula_efetiva"] is None


def test_vigencia_validada_libera_modal():
    s = _decidir(True, "validada")
    assert s["status_aliquota"] == "ok"
    assert s["formula_efetiva"] == "modal"


def test_nunca_existe_formula_com_fecp():
    formulas = {
        r.entao.get("formula_efetiva") for r in DT02_ALIQUOTA.regras
    }
    assert "modal_mais_fecp" not in formulas
