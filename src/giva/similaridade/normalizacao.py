"""Normalização conservadora de descrições (RF-29 / HU-06).

Remove **apenas** marcadores hierárquicos (traços/bullets do Classif), pontuação
e caixa. **Preserva negações e qualificadores** — 'exceto' e o conteúdo de
parênteses viram tokens, nunca são descartados: 'ferramentas exceto martelos'
≠ 'ferramentas martelos' é distinção fiscal, não ruído. Sem remoção de
stopwords, justamente para não engolir 'exceto'.
"""

from __future__ import annotations

import re

_ACENTOS = str.maketrans("áàâãéêíóôõúüç", "aaaaeeiooouuc")
_NAO_ALFANUM = re.compile(r"[^\w\s]")  # pontuação/parênteses viram separador; o conteúdo fica


def normalizar_descricao(texto: str) -> list[str]:
    """Tokens normalizados, preservando qualificadores. Determinístico."""
    base = texto.lower().translate(_ACENTOS)
    base = _NAO_ALFANUM.sub(" ", base)
    return [token for token in base.split() if token]


def score_similaridade(entrada: str, oficial: str) -> float:
    """Jaccard sobre os conjuntos de tokens — simétrico e determinístico."""
    a = set(normalizar_descricao(entrada))
    b = set(normalizar_descricao(oficial))
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
