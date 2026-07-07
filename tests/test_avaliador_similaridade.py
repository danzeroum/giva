"""Divergência de descrição (v1): decidida por CONFLITO de categoria, não por
similaridade textual. O score Jaccard fica só como informação na proveniência."""

from __future__ import annotations

from giva.similaridade.avaliador import AvaliadorSimilaridade


def test_conflito_de_categoria_gera_divergencia_forte():
    r = AvaliadorSimilaridade().avaliar(
        "MARTELO DE BORRACHA", "Rolamentos de esferas", conflito_categoria=True
    )
    assert r.status_descricao == "requer_revisao"  # forte


def test_sem_conflito_e_nenhuma_divergencia():
    r = AvaliadorSimilaridade().avaliar(
        "ROTOR DE FACAS", "- Partes", conflito_categoria=False
    )
    assert r.status_descricao == "ok"  # nenhuma — mesmo com score textual baixo


def test_score_e_informativo_nao_decide_status():
    # score baixíssimo (0), mas sem conflito → nenhuma (o score não manda).
    r = AvaliadorSimilaridade().avaliar("abc", "xyz", conflito_categoria=False)
    assert r.status_descricao == "ok"
    assert r.proveniencia.score == "0.000"
