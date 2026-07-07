"""Modelo da linha em processamento no pipeline (plano §2 C3).

`LinhaLote` acumula, ao longo das etapas, o que cada componente produz. Os
componentes não se conhecem — só leem/escrevem campos desta estrutura. Os
valores originais ficam intocados em `originais` (RF-04/RF-30).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class LinhaLote:
    numero: int
    originais: dict[str, str]  # todas as colunas originais, preservadas na ordem

    # valores brutos das 4 colunas mínimas (resolvidos pelo leitor)
    bruto_ncm: str | None
    bruto_periodo: str | None
    bruto_uf: str | None
    bruto_descricao: str | None

    # preenchidos pelas etapas de normalização
    ncm: str | None = None
    periodo: date | None = None
    uf: str | None = None
    status_linha: str = ""
    motivo_falha: str | None = None

    # saídas de enriquecimento (nome do campo → valor já formatado)
    enriquecimento: dict[str, str] = field(default_factory=dict)
    # proveniência por grupo de campo (RNF-04) — serializada com chaves ordenadas
    proveniencia: dict[str, Any] = field(default_factory=dict)
    # regra/versão de cada DT disparada (insumo do process mining §5.3)
    regras_disparadas: dict[str, str] = field(default_factory=dict)

    @property
    def valida(self) -> bool:
        return self.status_linha == "ok"
