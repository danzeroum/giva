"""Categorizador (Módulo D — RF-26/27/28) — taxonomia das 18 categorias EFD.

Sugere a categoria macro **operacional** de um item, a partir do NCM e da
descrição. Determinístico por regras (PRD GIVA §12.5: v1 = regras, não IA),
auditável e reproduzível (RN6).

DECISÃO GIVA (registro de decisões §1): a taxonomia-alvo são as **18 categorias
do EFD** do escritório (doc `04-categorias-e-regras.md`), não a taxonomia
setorial por SH4 do enriquecedor-fiscal. As regras seguem o doc 04:

  Precedência (a primeira que casar decide):
    1. `regras_excecao` — NCM exato mapeado à mão (uso/curadoria) → confiança ALTA.
    2. Regra por **faixa de NCM** (capítulo/posição, §2.1) — prefixo mais
       específico vence.
    3. Regra por **palavra-chave na descrição** (§2.2) — fallback quando o NCM
       não resolve.
    4. Sem pista suficiente → **`Indefinido`** (nunca força — RN4), separando o
       motivo (`sem_match` vs `ambiguo`) para orientar o revisor (§2.3).

Campo de confiança (§2.3): ALTA (NCM e descrição concordam), MÉDIA (casou só
por NCM ou só por descrição), BAIXA (conflito NCM×descrição, regra ampla ou
ambiguidade — candidato a revisão manual).

A lista de categorias e as regras são **configuráveis em banco** (versionadas),
não hard-coded (doc 04, "base refinável"). A versão vigente vem do parâmetro
`categoria_versao_vigente` (RF-24), nunca 'a maior versão'.

A saída é sempre **sugestão operacional**, não classificação fiscal
(`sugestivo=True`, RN2) — o disclaimer segue no arquivo de saída (MontadorSaida).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

# Catch-all quando não há pista suficiente (doc 04, categoria 18).
CATEGORIA_INDEFINIDA = "Indefinido"

# Disclaimer obrigatório na saída (RN2) — exposto aqui para o MontadorSaida reusar.
DISCLAIMER_CATEGORIA = (
    "Categoria macro é sugestão interna/operacional — não substitui "
    "enquadramento fiscal (classificação oficial permanece análise humana)."
)


@dataclass(frozen=True)
class ProvenienciaCategoria:
    regra: str  # ex.: regra_ncm_categoria@1.0 | regra_palavra_categoria@1.0 | regras_excecao@1.0
    versao: str
    # excecao | ncm+descricao | ncm | ncm_conflito_descricao | descricao | ambiguo | sem_match
    caminho: str


@dataclass(frozen=True)
class ResultadoCategoria:
    categoria: str
    confianca: str  # alta | media | baixa (§2.3)
    proveniencia: ProvenienciaCategoria
    motivo_indefinido: str | None = None  # sem_match | ambiguo (só quando Indefinido)
    sugestivo: bool = True  # sugestão operacional, não classificação fiscal (RN2)
    # True quando o NCM aponta uma categoria e a descrição aponta OUTRA — sinal
    # de divergência de descrição (ex.: NCM de rolamento + descrição 'martelo').
    # É o que alimenta o status_descricao (divergência forte) na EtapaSimilaridade.
    conflito_descricao: bool = False


class RepositorioCategoria(Protocol):
    def versao_vigente(self) -> str:
        """Lê `categoria_versao_vigente` do parâmetro (RF-24)."""
        ...

    def buscar_excecao(self, ncm: str, versao: str) -> str | None:
        """Categoria de exceção para o NCM exato na versão, ou None."""
        ...

    def buscar_por_ncm(self, ncm: str, versao: str) -> str | None:
        """Categoria pela faixa de NCM (§2.1). O **prefixo mais específico**
        (mais longo) que casar decide; None se nenhum prefixo casar."""
        ...

    def buscar_por_palavra(self, descricao: str, versao: str) -> list[str]:
        """Categorias distintas cujas palavras-chave aparecem na descrição
        (§2.2, case-insensitive). Vazio se nenhuma casar; 2+ = ambiguidade."""
        ...


def _ncm_ausente(ncm: str | None) -> bool:
    """NCM em branco, None ou `00000000` conta como ausente (doc 04 §3) —
    cai para a regra por descrição, nunca inventa categoria pelo código nulo."""
    if not ncm:
        return True
    return set(ncm) == {"0"}


class Categorizador:
    def __init__(self, repositorio: RepositorioCategoria) -> None:
        self._repo = repositorio

    def categorizar(self, ncm: str | None, descricao: str | None) -> ResultadoCategoria:
        versao = self._repo.versao_vigente()
        ncm_util = None if _ncm_ausente(ncm) else ncm

        if ncm_util is not None:
            excecao = self._repo.buscar_excecao(ncm_util, versao)
            if excecao is not None:  # exceção curada vence tudo (precedência)
                return self._resultado(excecao, "alta", versao, "excecao")

        cat_ncm = (
            self._repo.buscar_por_ncm(ncm_util, versao) if ncm_util is not None else None
        )
        cats_desc = self._repo.buscar_por_palavra(descricao or "", versao)
        return self._resolver(cat_ncm, cats_desc, versao, ncm_ausente=ncm_util is None)

    def _resolver(
        self, cat_ncm: str | None, cats_desc: list[str], versao: str, *, ncm_ausente: bool
    ) -> ResultadoCategoria:
        # Confiança (Opção B — decisão do escritório): um sinal FORTE único já
        # dá Alta. O NCM é autoritativo — quando ele decide, a confiança é Alta
        # (a divergência com a descrição é sinalizada à parte, pela similaridade).
        distintas = set(cats_desc)
        if cat_ncm is not None:
            if cat_ncm in distintas:  # NCM e descrição concordam
                return self._resultado(cat_ncm, "alta", versao, "ncm+descricao")
            # NCM decide (Alta). Se a descrição apontou OUTRA categoria, há conflito
            # → sinaliza divergência de descrição (não rebaixa a confiança, Opção B).
            conflito = bool(distintas)
            return self._resultado(cat_ncm, "alta", versao, "ncm", conflito=conflito)

        if len(distintas) == 1:  # só descrição
            # NCM presente mas sem regra → sinal único forte (Alta);
            # NCM ausente (branco/00000000) → categoria veio só do texto (Média).
            conf = "media" if ncm_ausente else "alta"
            return self._resultado(next(iter(distintas)), conf, versao, "descricao")
        if len(distintas) > 1:  # bateu com 2+ categorias, sem desempate
            return self._indefinido("ambiguo", versao)
        return self._indefinido("sem_match", versao)  # nenhuma pista

    def _resultado(
        self, categoria: str, confianca: str, versao: str, caminho: str,
        *, conflito: bool = False,
    ) -> ResultadoCategoria:
        tabela = "regras_excecao" if caminho == "excecao" else _tabela_do_caminho(caminho)
        return ResultadoCategoria(
            categoria=categoria,
            confianca=confianca,
            proveniencia=ProvenienciaCategoria(f"{tabela}@{versao}", versao, caminho),
            conflito_descricao=conflito,
        )

    def _indefinido(self, motivo: str, versao: str) -> ResultadoCategoria:
        return ResultadoCategoria(
            categoria=CATEGORIA_INDEFINIDA,
            confianca="baixa",
            proveniencia=ProvenienciaCategoria(f"categoria@{versao}", versao, motivo),
            motivo_indefinido=motivo,
        )


def _tabela_do_caminho(caminho: str) -> str:
    """Qual tabela de regra decidiu, pela proveniência do caminho."""
    if caminho in ("ncm+descricao", "ncm"):
        return "regra_ncm_categoria"
    if caminho == "descricao":
        return "regra_palavra_categoria"
    return "categoria"
