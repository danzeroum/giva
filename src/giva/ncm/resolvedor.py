"""ResolutorNCM (Módulo B — RF-12/13/14).

Resolve o status e a **descrição de época** de um NCM num período, consumindo a
DT-01 e as bases `ncm_historico` (bitemporal) e `ncm_vigente`.

Precedência (period-aware — o coração do GIVA, critério de aceite nº 1):
1. **`ncm_historico`** — se houver uma redação cuja vigência cobre o período
   informado, ela responde: a descrição **da época**, não a atual. É o que
   permite o uso retrospectivo (um NCM de 2017 pode ter descrição diferente da
   de 2024).
2. **`ncm_vigente`** (fallback) — quando o histórico ainda não cobre aquela
   janela: se o período for ≥ `data_inicio` da redação vigente, responde a
   vigente (`ok`); se anterior, sinaliza
   `descricao_vigente_periodo_nao_carregado` (não inventa a de época).
3. Código inexistente → `codigo_inexistente`, ou
   `codigo_alterado_pela_revisao_sh` se houver correlação SH (`ncm_correlacao`).

O `if` que escolhe histórico vs. vigente é guarda de *disponibilidade de dado*,
não regra fiscal — a decisão de status continua saindo da DT-01.
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


@dataclass(frozen=True)
class RedacaoPeriodo:
    """Redação de um NCM vigente NAQUELE período, vinda de `ncm_historico`
    (bitemporal). `vigencia_inicio`/`vigencia_fim` delimitam a janela em que
    esta redação valeu; `vigencia_fim=None` = ainda vigente."""

    codigo: str
    descricao: str
    vigencia_inicio: date
    vigencia_fim: date | None
    ato_tipo: str | None
    ato_numero: str | None
    ato_ano: str | None
    data_coleta: date
    carga_id: int


class RepositorioNCM(Protocol):
    """Acesso às bases de NCM. Abstrai o SQL para o componente ser testável sem
    banco (fake em memória na unidade; psycopg na integração)."""

    def buscar_redacao_periodo(self, codigo: str, periodo: date) -> RedacaoPeriodo | None:
        """A redação de `ncm_historico` cuja vigência cobre `periodo`, ou None
        se o histórico não cobrir aquela janela (cai para a vigente)."""
        ...

    def buscar_posicao(self, prefixo6: str) -> str | None:
        """Descrição da subposição (6 dígitos) — nível público estável usado como
        referência quando não há a redação de época. None se não houver."""
        ...

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

    def resolver(self, codigo: str | None, periodo: date) -> ResultadoNCM:
        if codigo is None:  # NCM ausente (branco/00000000) — categoria vem da descrição
            decisao = avaliar(DT01_STATUS_NCM, {"codigo_ausente": True})
            return ResultadoNCM(decisao.saidas["status_ncm"], None, None)

        historica = self._repo.buscar_redacao_periodo(codigo, periodo)
        if historica is not None:  # descrição DA ÉPOCA — precedência (RF-14)
            decisao = avaliar(DT01_STATUS_NCM, _entradas_historico())
            return ResultadoNCM(
                decisao.saidas["status_ncm"],
                historica.descricao,
                _proveniencia_periodo(decisao.proveniencia, historica),
            )

        posicao = self._repo.buscar_posicao(codigo[:6])
        if posicao is not None:  # subposição estável (gabarito: descrição de POSIÇÃO)
            decisao = avaliar(DT01_STATUS_NCM, _entradas_historico())  # nível estável → ok
            return ResultadoNCM(decisao.saidas["status_ncm"], posicao, None)

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


def _entradas_historico() -> dict[str, Any]:
    """Redação de época encontrada = código existe e o período é coberto por ela
    (DT-01 regra 3 → ok)."""
    return {"codigo_existe": True, "periodo_cobre_vigente": True, "tem_correlacao": False}


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


def _proveniencia_periodo(regra_dt: str, r: RedacaoPeriodo) -> ProvenienciaNCM:
    """Proveniência da redação de época: `data_inicio` = início da janela de
    vigência histórica que respondeu."""
    return ProvenienciaNCM(
        regra_dt=regra_dt,
        ato_tipo=r.ato_tipo,
        ato_numero=r.ato_numero,
        ato_ano=r.ato_ano,
        data_inicio=r.vigencia_inicio,
        data_coleta=r.data_coleta,
        carga_id=r.carga_id,
    )
