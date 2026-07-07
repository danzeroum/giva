"""Normalização da entrada (RF-02/RF-03, plano §3 e checklist de handoff).

Armadilhas codificadas aqui — não "otimizar" sem ler o plano:
- NCM perde zeros à ESQUERDA no Excel ("1012100" → "01012100"). Nunca
  completar à direita: isso produziria outro código válido (erro silencioso).
- Período normaliza para o primeiro dia do menor grão informado.
- O valor original é sempre preservado pelo chamador em coluna `*_original`.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

_UFS_VALIDAS = frozenset(
    "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split()
)

_NOME_PARA_UF = {
    "acre": "AC", "alagoas": "AL", "amazonas": "AM", "amapa": "AP", "bahia": "BA",
    "ceara": "CE", "distrito federal": "DF", "espirito santo": "ES", "goias": "GO",
    "maranhao": "MA", "minas gerais": "MG", "mato grosso do sul": "MS",
    "mato grosso": "MT", "para": "PA", "paraiba": "PB", "pernambuco": "PE",
    "piaui": "PI", "parana": "PR", "rio de janeiro": "RJ",
    "rio grande do norte": "RN", "rondonia": "RO", "roraima": "RR",
    "rio grande do sul": "RS", "santa catarina": "SC", "sergipe": "SE",
    "sao paulo": "SP", "tocantins": "TO",
}

_ACENTOS = str.maketrans("áàâãéêíóôõúüç", "aaaaeeiooouuc")


@dataclass(frozen=True)
class ResultadoNormalizacao:
    valor: str | date | None
    motivo_falha: str | None = None
    # NCM ausente (branco/`00000000`): NÃO é falha de linha (doc 04 §3). A linha
    # segue — categoria vem da descrição e a alíquota resolve por UF+período —,
    # só o NCM fica sem resolver. `ausente` distingue isso de um NCM malformado
    # (esse sim é `motivo_falha` → entrada_invalida).
    ausente: bool = False

    @property
    def valido(self) -> bool:
        return self.motivo_falha is None


def normalizar_ncm(bruto: object) -> ResultadoNormalizacao:
    """'8471.30.12' → '84713012'; '1012100' → '01012100' (zeros à ESQUERDA).
    Branco e `00000000` → **ausente** (não falha): cai para a regra por
    descrição (doc 04 §3). Não numérico / comprimento inválido → falha."""
    if bruto is None:
        return ResultadoNormalizacao(None, ausente=True)
    texto = re.sub(r"[.\s\-]", "", str(bruto).strip())
    if not texto:
        return ResultadoNormalizacao(None, ausente=True)
    if not texto.isdigit():
        return ResultadoNormalizacao(
            None, f"NCM contém caracteres não numéricos: '{bruto}'"
        )
    if len(texto) > 8:
        return ResultadoNormalizacao(
            None, f"NCM com {len(texto)} dígitos (máximo 8): '{bruto}'"
        )
    if len(texto) < 6:
        return ResultadoNormalizacao(
            None,
            f"NCM com apenas {len(texto)} dígitos — confira se o valor está "
            f"truncado além da perda de zeros à esquerda: '{bruto}'",
        )
    normalizado = texto.zfill(8)
    if set(normalizado) == {"0"}:  # 00000000 = ausente (não é NCM real, doc 04 §3)
        return ResultadoNormalizacao(None, ausente=True)
    return ResultadoNormalizacao(normalizado)


# Tabela de formatos aceitos: padrão → construtor de date a partir dos grupos.
# Normaliza para o primeiro dia do menor grão informado (plano §3 / RF-03).
_FORMATOS_PERIODO: tuple[tuple[str, Callable[[re.Match[str]], date]], ...] = (
    (r"^(\d{4})$", lambda m: date(int(m[1]), 1, 1)),
    (r"^(\d{1,2})/(\d{4})$", lambda m: date(int(m[2]), int(m[1]), 1)),
    (r"^(\d{4})-(\d{1,2})$", lambda m: date(int(m[1]), int(m[2]), 1)),
    (r"^(\d{4})-(\d{1,2})-(\d{1,2})$", lambda m: date(int(m[1]), int(m[2]), int(m[3]))),
    (r"^(\d{1,2})/(\d{1,2})/(\d{4})$", lambda m: date(int(m[3]), int(m[2]), int(m[1]))),
)


def normalizar_periodo(bruto: object) -> ResultadoNormalizacao:
    """'2025' → 2025-01-01 · '03/2025' → 2025-03-01 · '2025-03' → 2025-03-01
    · '2025-03-15' → 2025-03-15."""
    if bruto is None:
        return ResultadoNormalizacao(None, "Período ausente")
    if isinstance(bruto, date):
        return ResultadoNormalizacao(bruto)
    texto = str(bruto).strip()
    for padrao, construir in _FORMATOS_PERIODO:
        m = re.match(padrao, texto)
        if not m:
            continue
        try:
            return ResultadoNormalizacao(construir(m))
        except ValueError:
            return ResultadoNormalizacao(None, f"Período com data inválida: '{bruto}'")
    return ResultadoNormalizacao(None, f"Período em formato não reconhecido: '{bruto}'")


def normalizar_uf(bruto: object) -> ResultadoNormalizacao:
    """'sp' → 'SP' · 'São Paulo' → 'SP'."""
    if bruto is None:
        return ResultadoNormalizacao(None, "UF ausente")
    texto = str(bruto).strip()
    if not texto:
        return ResultadoNormalizacao(None, "UF ausente")
    sigla = texto.upper()
    if sigla in _UFS_VALIDAS:
        return ResultadoNormalizacao(sigla)
    nome = " ".join(texto.lower().translate(_ACENTOS).split())
    if nome in _NOME_PARA_UF:
        return ResultadoNormalizacao(_NOME_PARA_UF[nome])
    return ResultadoNormalizacao(None, f"UF não reconhecida: '{bruto}'")
