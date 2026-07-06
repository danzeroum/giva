"""ResolutorAliquota (Módulo C — RF-20/21/22).

Resolve a alíquota interna de ICMS de uma UF num período. Consome a DT-02
(a decisão de *qual status* e *se libera valor* vive na tabela de decisão) e a
base `aliquota_icms_modal`.

DECISÃO GIVA (registro de decisões §3): entrega a **alíquota modal nominal,
sem FECP** (playbook §5). Diferente do enriquecedor-fiscal, não há fórmula
`modal_mais_fecp` — o valor entregue é sempre `aliquota_modal`. Os campos de
FECP da base seguem disponíveis na proveniência como referência, mas não somam.

RF-22 — produção vs. homologação: uma vigência **não validada nunca responde
com alíquota em produção**. A política é injetada no construtor
(`aceita_nao_validada`), decidida na borda da aplicação — o componente
permanece puro e testável nos dois modos, sem ler ambiente global.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Protocol

from giva.decisao.interpretador import avaliar
from giva.decisao.tabelas import DT02_ALIQUOTA


class ErroAliquota(Exception):
    """Base dos erros do resolvedor de alíquota."""


class VigenciaSobrepostaError(ErroAliquota):
    """Mais de uma vigência para (uf, período). A exclusion constraint de
    `aliquota_icms_modal` (EXCLUDE USING gist) deveria tornar isto impossível;
    se chegou aqui, é violação de invariante do banco — falha explícita, nunca
    'pega a primeira'."""

    def __init__(self, uf: str, periodo: date, quantidade: int) -> None:
        super().__init__(
            f"{quantidade} vigências encontradas para (uf={uf!r}, "
            f"período={periodo.isoformat()}); a constraint EXCLUDE garante no "
            f"máximo uma. Invariante do banco violada."
        )


@dataclass(frozen=True)
class VigenciaAliquota:
    """Uma linha de `aliquota_icms_modal` já cruzada com a proveniência da
    carga (`carga.data_coleta`, `carga_id`). É o que o repositório devolve.
    Os campos de FECP ficam disponíveis para referência/proveniência, mas o
    valor entregue pelo GIVA é sempre a `aliquota_modal` nominal."""

    uf: str
    vigencia_inicio: date
    vigencia_fim: date | None
    aliquota_modal: Decimal
    fecp_percentual: Decimal | None
    fecp_incidencia: str
    status_validacao: str
    fonte_legal: str | None
    fonte_compilada: str
    data_coleta: date
    carga_id: int


class RepositorioAliquota(Protocol):
    """Acesso à base de alíquotas. Abstrai o SQL para o componente ser testável
    sem banco (fake em memória na unidade; psycopg na integração)."""

    def buscar_vigencia(self, uf: str, periodo: date) -> VigenciaAliquota | None:
        """A única vigência de `uf` que cobre `periodo`, ou None se não houver.
        DEVE levantar `VigenciaSobrepostaError` se encontrar mais de uma."""
        ...


@dataclass(frozen=True)
class ProvenienciaAliquota:
    """Contrato do RNF-04 no nível de campo: de onde veio a decisão de alíquota."""

    regra_dt: str  # ex.: DT-02_aliquota@1.0#regra3
    fonte_legal: str | None
    fonte_compilada: str
    vigencia_inicio: date
    vigencia_fim: date | None
    data_coleta: date
    carga_id: int


@dataclass(frozen=True)
class ResultadoAliquota:
    status_aliquota: str
    # alíquota interna nominal (modal, sem FECP) — o valor entregue (RF-30).
    aliquota_interna: Decimal | None
    proveniencia: ProvenienciaAliquota | None  # None quando não há vigência
    provisorio: bool = False  # True: valor exibido só em homologação (RF-22)


class ResolutorAliquota:
    """Resolve a alíquota interna de (uf, período) via DT-02 + base de modais."""

    def __init__(
        self, repositorio: RepositorioAliquota, *, aceita_nao_validada: bool = False
    ) -> None:
        self._repo = repositorio
        self._aceita_nao_validada = aceita_nao_validada

    def resolver(self, uf: str, periodo: date) -> ResultadoAliquota:
        vigencia = self._repo.buscar_vigencia(uf, periodo)
        decisao = avaliar(DT02_ALIQUOTA, _entradas(vigencia))
        status: str = decisao.saidas["status_aliquota"]
        formula: str | None = decisao.saidas["formula_efetiva"]

        if vigencia is None:  # periodo_sem_cobertura — sem proveniência possível
            return ResultadoAliquota(status, None, None)

        proveniencia = _proveniencia(decisao.proveniencia, vigencia)

        if formula is not None:  # validada: a DT liberou a modal
            return ResultadoAliquota(status, vigencia.aliquota_modal, proveniencia)

        # formula None ⇒ vigência achada, porém não validada (RF-22).
        if self._aceita_nao_validada:  # homologação: exibe o provisório, marcado
            return ResultadoAliquota(
                status, vigencia.aliquota_modal, proveniencia, provisorio=True
            )

        return ResultadoAliquota(status, None, proveniencia)  # produção: retém


def _entradas(vigencia: VigenciaAliquota | None) -> dict[str, Any]:
    if vigencia is None:
        return {"vigencia_encontrada": False, "status_validacao": None}
    return {
        "vigencia_encontrada": True,
        "status_validacao": vigencia.status_validacao,
    }


def _proveniencia(regra_dt: str, v: VigenciaAliquota) -> ProvenienciaAliquota:
    return ProvenienciaAliquota(
        regra_dt=regra_dt,
        fonte_legal=v.fonte_legal,
        fonte_compilada=v.fonte_compilada,
        vigencia_inicio=v.vigencia_inicio,
        vigencia_fim=v.vigencia_fim,
        data_coleta=v.data_coleta,
        carga_id=v.carga_id,
    )
