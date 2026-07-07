"""Ponta a ponta do pipeline com repositórios fake (sem banco): entrada CSV →
cadeia de etapas → CSV enriquecido. Verifica as decisões GIVA na saída:
alíquota modal (sem coluna de efetiva/FECP), confiança de categoria e
preservação das colunas originais."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from giva.aliquota.resolvedor import ResolutorAliquota, VigenciaAliquota
from giva.categoria.categorizador import Categorizador
from giva.ncm.resolvedor import RedacaoVigente, ResolutorNCM
from giva.pipeline.etapas import (
    EtapaAliquota,
    EtapaCategoria,
    EtapaNCM,
    EtapaNormalizacao,
    EtapaSimilaridade,
)
from giva.pipeline.leitor import ler_csv
from giva.pipeline.pipeline import Pipeline
from giva.saida.montador import COLUNAS_ENRIQUECIMENTO, construir_resumo, montar_csv
from giva.similaridade.avaliador import AvaliadorSimilaridade
from tests.test_categorizador import FakeRepo as FakeCategoria


class FakeNCM:
    def buscar_redacao_periodo(self, codigo: str, periodo: date):
        return None  # sem histórico carregado no fake → cai na vigente

    def buscar_posicao(self, prefixo6: str):
        return None

    def buscar_vigente(self, codigo: str):
        if codigo == "84821000":
            return RedacaoVigente(
                codigo="84821000",
                descricao="Rolamentos de esferas",
                data_inicio=date(2022, 4, 1),
                ato_tipo="Resolução", ato_numero="272", ato_ano="2021",
                data_coleta=date(2026, 7, 1),
                carga_id=1,
            )
        return None

    def existe_correlacao(self, codigo: str) -> bool:
        return False


class FakeAliquota:
    def buscar_vigencia(self, uf: str, periodo: date):
        if uf == "SP":
            return VigenciaAliquota(
                uf="SP",
                vigencia_inicio=date(2026, 1, 1),
                vigencia_fim=None,
                aliquota_modal=Decimal("18.0"),
                fecp_percentual=Decimal("2.0"),
                fecp_incidencia="produtos_selecionados",
                status_validacao="validada",
                fonte_legal="RICMS/SP art. 52, I",
                fonte_compilada="SimTax 2026",
                data_coleta=date(2026, 7, 1),
                carga_id=1,
            )
        return None


def _pipeline():
    categoria = FakeCategoria(
        ncm=[("8482", "Peça de máquina")],
        palavra=[("rolamento", "Peça de máquina")],
    )
    return Pipeline([
        EtapaNormalizacao(),
        EtapaNCM(ResolutorNCM(FakeNCM())),
        EtapaAliquota(ResolutorAliquota(FakeAliquota())),
        EtapaCategoria(Categorizador(categoria)),
        EtapaSimilaridade(AvaliadorSimilaridade()),
    ])


_CSV = (
    "NCM,Periodo,Descricao,UF,Centro de Custo\n"
    "8482.10.00,03/2026,Rolamento rigido de esferas,SP,CC-01\n"
    "xyz,03/2026,item ruim,SP,CC-02\n"
)


def test_linha_valida_entrega_modal_categoria_e_confianca():
    lote = ler_csv(_CSV)
    linhas = _pipeline().processar(lote.linhas)
    boa = linhas[0]
    assert boa.status_linha == "ok"
    assert boa.enriquecimento["descricao_oficial_ncm"] == "Rolamentos de esferas"
    assert boa.enriquecimento["aliquota_icms_interna"] == "18.0"
    assert boa.enriquecimento["categoria_macro"] == "Peça de máquina"
    assert boa.enriquecimento["confianca_categorizacao"] == "alta"


def test_linha_invalida_nao_derruba_lote():
    lote = ler_csv(_CSV)
    linhas = _pipeline().processar(lote.linhas)
    ruim = linhas[1]
    assert ruim.status_linha == "entrada_invalida"
    assert "aliquota_icms_interna" not in ruim.enriquecimento


def test_saida_preserva_originais_e_nao_tem_coluna_de_efetiva():
    lote = ler_csv(_CSV)
    linhas = _pipeline().processar(lote.linhas)
    csv_saida = montar_csv(lote.colunas_originais, linhas)
    cabecalho = csv_saida.splitlines()[0]
    # colunas originais preservadas (inclui a extra "Centro de Custo")
    assert cabecalho.startswith("NCM,Periodo,Descricao,UF,Centro de Custo")
    # decisão GIVA §3: entrega modal, sem coluna de alíquota efetiva/FECP
    assert "aliquota_icms_interna" in COLUNAS_ENRIQUECIMENTO
    assert "aliquota_efetiva" not in COLUNAS_ENRIQUECIMENTO


def test_resumo_carrega_disclaimer():
    lote = ler_csv(_CSV)
    linhas = _pipeline().processar(lote.linhas)
    resumo = construir_resumo(linhas)
    assert "não substitui" in resumo["disclaimer"]
    assert resumo["linhas"] == 2
