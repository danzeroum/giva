"""Parser do snapshot vigente do Classif (Módulo A — ingestão, RF-12).

Fonte: endpoint público sem autenticação do Portal Único Siscomex
(`api/publico/nomenclatura/download/json?perfil=PUBLICO`). Fatos verificados
(secao-1-ncm F1–F4):

- O arquivo traz TODOS os níveis hierárquicos (capítulo 2 díg., posição 4,
  subposição 6, NCM 8) e o campo `Codigo` vem **pontuado** — os NCM de 8
  dígitos aparecem como `'0101.21.00'` (string de 10 caracteres). Por isso o
  filtro conta **dígitos**, nunca `len(str)`, e **não** completa 7→8.
- `Data_Fim` é 100% `'31/12/9999'` (sentinela → vigência aberta, não uma data).
- Datas em dd/mm/aaaa; parsing estrito, sem adivinhação de formato.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

_NAO_DIGITO = re.compile(r"\D")
_DATA_FIM_SENTINELA = "31/12/9999"  # snapshot vigente: nunca uma data real (F4)


class ErroClassif(Exception):
    """Base dos erros de parsing do Classif."""


class DataInvalidaError(ErroClassif):
    def __init__(self, valor: str, campo: str) -> None:
        super().__init__(
            f"Data {valor!r} no campo {campo!r} não está em dd/mm/aaaa — "
            f"parsing estrito, sem adivinhação de formato."
        )


@dataclass(frozen=True)
class RegistroNCM:
    codigo: str  # 8 dígitos, sem pontuação
    descricao: str
    vigencia_inicio: date
    vigencia_fim: date | None  # None quando 31/12/9999 (vigência aberta)
    ato_tipo: str | None
    ato_numero: str | None
    ato_ano: str | None


def apenas_digitos(codigo: str) -> str:
    return _NAO_DIGITO.sub("", codigo)


def eh_ncm_8_digitos(codigo: str) -> bool:
    """True só para NCM completo. Conta dígitos após remover a pontuação do
    Classif ('0101.21.00' → 8). Um filtro por `len(codigo)==8` casaria zero."""
    return len(apenas_digitos(codigo)) == 8


def _parse_data(valor: str, campo: str) -> date:
    partes = valor.split("/")
    if len(partes) != 3:
        raise DataInvalidaError(valor, campo)
    dia, mes, ano = partes
    try:
        return date(int(ano), int(mes), int(dia))
    except ValueError as e:
        raise DataInvalidaError(valor, campo) from e


def _vigencia_fim(valor: str) -> date | None:
    return None if valor == _DATA_FIM_SENTINELA else _parse_data(valor, "Data_Fim")


def _texto_ou_none(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def parsear_registros(doc: Mapping[str, Any]) -> Iterator[RegistroNCM]:
    """Gera apenas os NCM de 8 dígitos do documento, com o código normalizado
    (sem pontuação) e datas convertidas. Demais níveis são descartados."""
    for n in doc["Nomenclaturas"]:
        codigo_bruto = str(n["Codigo"])
        if not eh_ncm_8_digitos(codigo_bruto):
            continue
        yield RegistroNCM(
            codigo=apenas_digitos(codigo_bruto),
            descricao=str(n["Descricao"]),
            vigencia_inicio=_parse_data(str(n["Data_Inicio"]), "Data_Inicio"),
            vigencia_fim=_vigencia_fim(str(n["Data_Fim"])),
            ato_tipo=_texto_ou_none(n.get("Tipo_Ato_Ini")),
            ato_numero=_texto_ou_none(n.get("Numero_Ato_Ini")),
            ato_ano=_texto_ou_none(n.get("Ano_Ato_Ini")),
        )
