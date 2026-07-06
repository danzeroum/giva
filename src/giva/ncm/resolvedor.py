"""ResolutorNCM (Módulo B — RF-12/13), Sprint 2.

Resolve o status e a descrição de um NCM num período, consumindo a DT-01 e a
base `ncm_vigente`. Fase 1 (secao-1-ncm §1.2): o snapshot é só a redação
vigente; para períodos anteriores à `data_inicio` da redação, sinaliza
`descricao_vigente_periodo_nao_carregado` — computável por código (F4).

Correlação SH 2022 (`ncm_correlacao`) só é carregada na R1.5 (RF-13). Enquanto
vazia, a regra 1 da DT-01 (`codigo_alterado_pela_revisao_sh`) não dispara e um
código inexistente sai como `codigo_inexistente`. Comportamento **deliberado**
de Fase 1 — fixado por teste para que a mudança na R1.5 seja visível, não
acidental.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol

from giva.decisao.interpretador import avaliar
from giva.decisao.tabelas import DT01_STATUS_NCM


@dataclass(frozen=True)
class RedacaoVigente:
    """Redação vigente de um NCM em `ncm_vigente`, com proveniência da carga."""

    codigo: str
    descricao: str
    data_inicio: date
    ato_tipo: str | None
    ato_numero: str | None
    ato_ano: str | None
    data_coleta: date
    carga_id: int


class RepositorioNCM(Protocol):
    """Acesso às bases de NCM. Abstrai o SQL para o componente ser testável sem
    banco (fake em memória na unidade; psycopg na integração)."""

    def buscar_vigente(self, codigo: str) -> RedacaoVigente | None:
        """A redação vigente do `codigo` (8 dígitos, sem pontuação), ou None."""
        ...

    def existe_correlacao(self, codigo: str) -> bool:
        """True se o código consta como `codigo_anterior` em `ncm_correlacao`."""
        ...


@dataclass(frozen=True)
class ProvenienciaNCM:
    """Contrato do RNF-04 no nível de campo: de onde veio a decisão de NCM."""

    regra_dt: str  # ex.: DT-01_status_ncm@1.0#regra3
    ato_tipo: str | None
    ato_numero: str | None
    ato_ano: str | None
    data_inicio: date
    data_coleta: date
    carga_id: int


@dataclass(frozen=True)
class ResultadoNCM:
    status_ncm: str
    descricao: str | None
    proveniencia: ProvenienciaNCM | None


class ResolutorNCM:
    """Resolve status_ncm + descrição de (codigo, período) via DT-01."""

    def __init__(self, repositorio: RepositorioNCM) -> None:
        self._repo = repositorio

    def resolver(self, codigo: str, periodo: date) -> ResultadoNCM:
        vigente = self._repo.buscar_vigente(codigo)
        decisao = avaliar(DT01_STATUS_NCM, self._entradas(codigo, periodo, vigente))
        status: str = decisao.saidas["status_ncm"]
        if vigente is None:  # inexistente/correlacionado — sem descrição vigente
            return ResultadoNCM(status, None, None)
        return ResultadoNCM(
            status, vigente.descricao, _proveniencia(decisao.proveniencia, vigente)
        )

    def _entradas(
        self, codigo: str, periodo: date, vigente: RedacaoVigente | None
    ) -> dict[str, Any]:
        if vigente is None:
            return {
                "codigo_existe": False,
                "periodo_cobre_vigente": None,
                "tem_correlacao": self._repo.existe_correlacao(codigo),
            }
        return {
            "codigo_existe": True,
            "periodo_cobre_vigente": periodo >= vigente.data_inicio,
            "tem_correlacao": False,
        }


def _proveniencia(regra_dt: str, v: RedacaoVigente) -> ProvenienciaNCM:
    return ProvenienciaNCM(
        regra_dt=regra_dt,
        ato_tipo=v.ato_tipo,
        ato_numero=v.ato_numero,
        ato_ano=v.ato_ano,
        data_inicio=v.data_inicio,
        data_coleta=v.data_coleta,
        carga_id=v.carga_id,
    )
