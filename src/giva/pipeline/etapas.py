"""Etapas do pipeline — adaptadores que ligam cada componente à `LinhaLote`.

Cada etapa lê o que precisa e escreve o que produz; os componentes não se
conhecem (composição do C3).

Nenhuma etapa fiscal contém `if` de regra: a decisão vem sempre de uma DT
(DT-04 para status_linha, DT-01/DT-02 dentro dos resolvedores). Os `if` aqui
são apenas guardas de fluxo (linha inválida não segue).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from giva.aliquota.resolvedor import ResolutorAliquota
from giva.categoria.categorizador import Categorizador
from giva.decisao.interpretador import avaliar
from giva.decisao.tabelas import DT04_STATUS_LINHA
from giva.ncm.resolvedor import ResolutorNCM
from giva.normalizacao.normalizador import (
    ResultadoNormalizacao,
    normalizar_ncm,
    normalizar_periodo,
    normalizar_uf,
)
from giva.pipeline.modelo import LinhaLote
from giva.similaridade.avaliador import AvaliadorSimilaridade


class Etapa(Protocol):
    def processar(self, linha: LinhaLote) -> None: ...


def _fmt_decimal(valor: Decimal) -> str:
    """Formato canônico (1 casa) — '18.0' sempre, nunca '18' nem '18.00'
    (determinismo, RNF-04)."""
    return f"{valor:.1f}"


class EtapaNormalizacao:
    """Normaliza NCM/período/UF e consolida `status_linha` via DT-04 (RF-04).

    Precedência do motivo de falha: NCM → período → UF (a descrição não é
    normalizada; entra no AvaliadorSimilaridade)."""

    def processar(self, linha: LinhaLote) -> None:
        ncm = normalizar_ncm(linha.bruto_ncm)
        periodo = normalizar_periodo(linha.bruto_periodo)
        uf = normalizar_uf(linha.bruto_uf)

        linha.ncm = ncm.valor if isinstance(ncm.valor, str) else None
        linha.periodo = periodo.valor if not isinstance(periodo.valor, str) else None
        linha.uf = uf.valor if isinstance(uf.valor, str) else None

        motivo = _primeiro_motivo(ncm, periodo, uf)
        linha.motivo_falha = motivo
        decisao = avaliar(DT04_STATUS_LINHA, {"motivo_falha": motivo})
        linha.status_linha = decisao.saidas["status_linha"]
        linha.regras_disparadas["DT-04"] = decisao.proveniencia
        linha.enriquecimento["status_linha"] = linha.status_linha
        if motivo is not None:  # motivo específico por linha (HU-02)
            linha.proveniencia["linha"] = {"motivo_falha": motivo}


def _primeiro_motivo(*resultados: ResultadoNormalizacao) -> str | None:
    for r in resultados:  # ordem dos argumentos = precedência
        if r.motivo_falha is not None:
            return r.motivo_falha
    return None


class EtapaNCM:
    """Resolve descrição oficial e status_ncm (RF-12/13) via ResolutorNCM."""

    def __init__(self, resolvedor: ResolutorNCM) -> None:
        self._resolvedor = resolvedor

    def processar(self, linha: LinhaLote) -> None:
        # roda mesmo com NCM ausente (linha.ncm None): o resolvedor devolve
        # `ncm_ausente` e a categoria virá da descrição (doc 04 §3).
        if not linha.valida or linha.periodo is None:
            return
        r = self._resolvedor.resolver(linha.ncm, linha.periodo)
        linha.enriquecimento["descricao_oficial_ncm"] = r.descricao or ""
        linha.enriquecimento["status_ncm"] = r.status_ncm
        if r.proveniencia is not None:
            p = r.proveniencia
            linha.regras_disparadas["DT-01"] = p.regra_dt
            linha.proveniencia["ncm"] = {
                "regra": p.regra_dt,
                "ato_tipo": p.ato_tipo or "",
                "ato_numero": p.ato_numero or "",
                "ato_ano": p.ato_ano or "",
                "data_inicio": p.data_inicio.isoformat(),
                "data_coleta": p.data_coleta.isoformat(),
                "carga_id": str(p.carga_id),
            }


class EtapaAliquota:
    """Resolve a alíquota interna (modal, sem FECP) e status_aliquota
    (RF-20/21/22). Decisão GIVA §3: entrega a modal nominal."""

    def __init__(self, resolvedor: ResolutorAliquota) -> None:
        self._resolvedor = resolvedor

    def processar(self, linha: LinhaLote) -> None:
        if not linha.valida or linha.uf is None or linha.periodo is None:
            return
        r = self._resolvedor.resolver(linha.uf, linha.periodo)
        linha.enriquecimento["status_aliquota"] = r.status_aliquota
        if r.aliquota_interna is not None:
            linha.enriquecimento["aliquota_icms_interna"] = _fmt_decimal(r.aliquota_interna)
        if r.provisorio:
            linha.enriquecimento["observacao_aliquota"] = "valor provisório (homologação)"
        if r.proveniencia is not None:
            p = r.proveniencia
            linha.regras_disparadas["DT-02"] = p.regra_dt
            linha.enriquecimento["fonte_aliquota"] = p.fonte_legal or p.fonte_compilada
            linha.proveniencia["aliquota"] = {
                "regra": p.regra_dt,
                "fonte_legal": p.fonte_legal or "",
                "fonte_compilada": p.fonte_compilada,
                "vigencia_inicio": p.vigencia_inicio.isoformat(),
                "vigencia_fim": p.vigencia_fim.isoformat() if p.vigencia_fim else "",
                "data_coleta": p.data_coleta.isoformat(),
                "carga_id": str(p.carga_id),
            }


class EtapaCategoria:
    """Sugere a categoria macro (RF-26/27/28) via Categorizador das 18
    categorias EFD — a partir do NCM e da descrição (doc 04)."""

    def __init__(self, categorizador: Categorizador) -> None:
        self._categorizador = categorizador

    def processar(self, linha: LinhaLote) -> None:
        if not linha.valida:
            return
        r = self._categorizador.categorizar(linha.ncm, linha.bruto_descricao)
        linha.enriquecimento["categoria_macro"] = r.categoria
        linha.enriquecimento["confianca_categorizacao"] = r.confianca
        proveniencia = {
            "regra": r.proveniencia.regra,
            "versao": r.proveniencia.versao,
            "caminho": r.proveniencia.caminho,
            "sugestivo": "true" if r.sugestivo else "false",
            "conflito": "true" if r.conflito_descricao else "false",
        }
        if r.motivo_indefinido is not None:
            proveniencia["motivo_indefinido"] = r.motivo_indefinido
        linha.proveniencia["categoria"] = proveniencia


class EtapaSimilaridade:
    """Compara a descrição de entrada com a oficial do NCM (RF-29) via DT-03.
    Só roda se a redação oficial foi resolvida — sem ela não há o que comparar."""

    def __init__(self, avaliador: AvaliadorSimilaridade) -> None:
        self._avaliador = avaliador

    def processar(self, linha: LinhaLote) -> None:
        oficial = linha.enriquecimento.get("descricao_oficial_ncm")
        if not linha.valida or not oficial or linha.bruto_descricao is None:
            return
        # divergência = conflito de categoria NCM×descrição (decisão do escritório).
        conflito = linha.proveniencia.get("categoria", {}).get("conflito") == "true"
        r = self._avaliador.avaliar(
            linha.bruto_descricao, oficial, conflito_categoria=conflito
        )
        linha.enriquecimento["status_descricao"] = r.status_descricao
        linha.regras_disparadas["DT-03"] = r.proveniencia.regra
        linha.proveniencia["descricao"] = {
            "regra": r.proveniencia.regra,
            "versao": r.proveniencia.versao,
            "score": r.proveniencia.score,
        }
