"""Interpretador de tabelas de decisão (ADR-04, plano de desenvolvimento §4).

Toda lógica condicional fiscal do sistema vive em tabelas de decisão
avaliadas por este interpretador. O código de domínio NÃO contém `if` fiscal.

Hit policy: **First** — a primeira regra que casa vence; a última regra de
toda tabela deve ser um catch-all. Se nenhuma regra casar, o interpretador
falha explicitamente (nunca silenciosamente).

Condições seguem o padrão Strategy: cada tipo de condição sabe avaliar-se
contra um valor de entrada. Novos tipos entram sem alterar o interpretador
(aberto para extensão, fechado para modificação).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol


class Condicao(Protocol):
    """Contrato de uma condição de coluna de entrada (Strategy)."""

    def atende(self, valor: Any, parametros: Mapping[str, Any]) -> bool:
        """Retorna True se `valor` satisfaz a condição."""
        ...


@dataclass(frozen=True)
class Qualquer:
    """Curinga: casa com qualquer valor (célula '-' de uma decision table)."""

    def atende(self, valor: Any, parametros: Mapping[str, Any]) -> bool:
        return True


@dataclass(frozen=True)
class Igual:
    esperado: Any

    def atende(self, valor: Any, parametros: Mapping[str, Any]) -> bool:
        return bool(valor == self.esperado)


@dataclass(frozen=True)
class Diferente:
    esperado: Any

    def atende(self, valor: Any, parametros: Mapping[str, Any]) -> bool:
        return bool(valor != self.esperado)


@dataclass(frozen=True)
class Em:
    aceitos: tuple[Any, ...]

    def atende(self, valor: Any, parametros: Mapping[str, Any]) -> bool:
        return valor in self.aceitos


@dataclass(frozen=True)
class EhNulo:
    def atende(self, valor: Any, parametros: Mapping[str, Any]) -> bool:
        return valor is None


@dataclass(frozen=True)
class NaoNulo:
    def atende(self, valor: Any, parametros: Mapping[str, Any]) -> bool:
        return valor is not None


@dataclass(frozen=True)
class MaiorIgualParametro:
    """Compara a entrada com um parâmetro de negócio (RF-24).

    Os limiares (ex.: T_ok, T_rev da DT-03) NÃO são constantes de código:
    chegam em `parametros` na avaliação, vindos da tabela de configuração.
    """

    nome_parametro: str

    def atende(self, valor: Any, parametros: Mapping[str, Any]) -> bool:
        if valor is None:
            return False
        if self.nome_parametro not in parametros:
            raise ParametroAusenteError(self.nome_parametro)
        return bool(valor >= parametros[self.nome_parametro])


@dataclass(frozen=True)
class Regra:
    numero: int
    quando: Mapping[str, Condicao]
    entao: Mapping[str, Any]

    def casa(self, entradas: Mapping[str, Any], parametros: Mapping[str, Any]) -> bool:
        return all(
            condicao.atende(entradas.get(coluna), parametros)
            for coluna, condicao in self.quando.items()
        )


@dataclass(frozen=True)
class TabelaDecisao:
    nome: str
    versao: str
    regras: Sequence[Regra]


@dataclass(frozen=True)
class ResultadoDecisao:
    """Saídas da regra vencedora + proveniência da decisão (§9: cada linha
    registra qual regra/versão disparou)."""

    saidas: Mapping[str, Any]
    tabela: str
    versao: str
    regra_numero: int
    proveniencia: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "proveniencia", f"{self.tabela}@{self.versao}#regra{self.regra_numero}"
        )


class ErroDecisao(Exception):
    """Base dos erros do interpretador."""


class SemRegraAplicavelError(ErroDecisao):
    """Nenhuma regra casou — a tabela está sem catch-all ou a entrada é
    inválida. Falha explícita, nunca resultado silencioso."""

    def __init__(self, tabela: TabelaDecisao, entradas: Mapping[str, Any]) -> None:
        super().__init__(
            f"Nenhuma regra de '{tabela.nome}@{tabela.versao}' casou com as "
            f"entradas {dict(entradas)!r}. Toda tabela deve terminar em catch-all."
        )


class ParametroAusenteError(ErroDecisao):
    def __init__(self, nome: str) -> None:
        super().__init__(
            f"Parâmetro de negócio '{nome}' não fornecido na avaliação "
            f"(RF-24: parâmetros vêm da configuração, não do código)."
        )


def avaliar(
    tabela: TabelaDecisao,
    entradas: Mapping[str, Any],
    parametros: Mapping[str, Any] | None = None,
) -> ResultadoDecisao:
    """Avalia `entradas` contra a tabela. Hit policy First.

    Complexidade O(R × C) com R regras e C colunas — trivial para as
    tabelas fiscais (≤ 10 regras); nenhuma otimização se justifica aqui.
    """
    params = parametros or {}
    for regra in tabela.regras:
        if regra.casa(entradas, params):
            return ResultadoDecisao(
                saidas=dict(regra.entao),
                tabela=tabela.nome,
                versao=tabela.versao,
                regra_numero=regra.numero,
            )
    raise SemRegraAplicavelError(tabela, entradas)
