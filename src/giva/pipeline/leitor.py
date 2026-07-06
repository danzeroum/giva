"""LeitorPlanilha (RF-01/RF-02) — entrada CSV.

Mapeia cabeçalhos de forma tolerante (acentos/variações) às 4 colunas mínimas
(NCM, Período, Descrição, UF). Falta de qualquer uma → rejeita o lote inteiro
com a coluna ausente nomeada (HU-01: não processa parcialmente). Preserva TODAS
as colunas originais, na ordem, para a saída.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from giva.pipeline.modelo import LinhaLote

# canônico → variações aceitas de cabeçalho (comparadas sem acento/caixa)
_ALIASES: dict[str, frozenset[str]] = {
    "ncm": frozenset({"ncm", "codigo", "codigo ncm", "cod ncm"}),
    "periodo": frozenset({"periodo", "data", "competencia", "mes", "mes/ano", "referencia"}),
    "descricao": frozenset({"descricao", "produto", "desc", "descricao do produto"}),
    "uf": frozenset({"uf", "estado", "unidade federativa"}),
}

_ACENTOS = str.maketrans("áàâãéêíóôõúüç", "aaaaeeiooouuc")


class ColunaAusenteError(Exception):
    """Uma coluna mínima não foi encontrada — o lote é rejeitado inteiro."""

    def __init__(self, ausentes: list[str]) -> None:
        self.ausentes = ausentes
        super().__init__(
            f"Colunas mínimas ausentes: {', '.join(ausentes)}. "
            f"O lote não é processado parcialmente (HU-01)."
        )


@dataclass(frozen=True)
class Lote:
    colunas_originais: list[str]
    linhas: list[LinhaLote]


def _canonizar(cabecalho: str) -> str:
    return " ".join(cabecalho.strip().lower().translate(_ACENTOS).split())


def _mapear_colunas(colunas: list[str]) -> dict[str, str]:
    """Resolve {campo canônico → nome real da coluna}. Erra se faltar alguma."""
    mapa: dict[str, str] = {}
    for real in colunas:
        canon = _canonizar(real)
        for campo, aliases in _ALIASES.items():
            if canon in aliases and campo not in mapa:
                mapa[campo] = real
    ausentes = [campo for campo in _ALIASES if campo not in mapa]
    if ausentes:
        raise ColunaAusenteError(ausentes)
    return mapa


def ler_csv(texto: str) -> Lote:
    leitor = csv.DictReader(io.StringIO(texto))
    colunas = leitor.fieldnames
    if not colunas:
        raise ColunaAusenteError(list(_ALIASES))
    colunas_originais = list(colunas)
    mapa = _mapear_colunas(colunas_originais)

    linhas: list[LinhaLote] = []
    for numero, registro in enumerate(leitor, start=1):
        originais = {c: (registro.get(c) or "") for c in colunas_originais}
        linhas.append(
            LinhaLote(
                numero=numero,
                originais=originais,
                bruto_ncm=originais[mapa["ncm"]],
                bruto_periodo=originais[mapa["periodo"]],
                bruto_uf=originais[mapa["uf"]],
                bruto_descricao=originais[mapa["descricao"]],
            )
        )
    return Lote(colunas_originais=colunas_originais, linhas=linhas)
