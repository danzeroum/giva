"""RepositorioCategoria sobre psycopg — `parametro`, `regras_excecao`,
`regra_ncm_categoria`, `regra_palavra_categoria`. A versão vigente vem do
parâmetro `categoria_versao_vigente` (RF-24)."""

from __future__ import annotations

from typing import Any

from psycopg import Connection

# Palavras-chave são casadas sem acento/caixa: descrições reais vêm em grafias
# mistas ("ÓLEO"/"oleo"/"Óleo"). As palavras no banco são gravadas já em
# minúsculas e sem acento (migration 0002); a descrição é normalizada aqui com o
# mesmo mapa do leitor de planilha.
_ACENTOS = str.maketrans("áàâãéêíóôõúüç", "aaaaeeiooouuc")


def _sem_acento(texto: str) -> str:
    return texto.lower().translate(_ACENTOS)


_SQL_VERSAO = "SELECT valor FROM parametro WHERE nome = 'categoria_versao_vigente'"

_SQL_EXCECAO = (
    "SELECT categoria FROM regras_excecao WHERE ncm = %(ncm)s AND versao = %(versao)s"
)

# Prefixo de NCM mais específico (mais longo) que casa com o código decide (§2.1).
_SQL_POR_NCM = """
    SELECT categoria FROM regra_ncm_categoria
     WHERE versao = %(versao)s
       AND left(%(ncm)s, length(prefixo)) = prefixo
     ORDER BY length(prefixo) DESC
     LIMIT 1
"""

# Palavras-chave cuja ocorrência aparece na descrição (§2.2). `palavra` já vem
# em minúsculas e sem acento no banco; `descricao` é normalizada no repositório.
_SQL_POR_PALAVRA = """
    SELECT DISTINCT categoria FROM regra_palavra_categoria
     WHERE versao = %(versao)s
       AND position(palavra IN %(descricao)s) > 0
     ORDER BY categoria
"""


class RepositorioCategoriaSQL:
    def __init__(self, conexao: Connection[Any]) -> None:
        self._con = conexao

    def versao_vigente(self) -> str:
        with self._con.cursor() as cur:
            cur.execute(_SQL_VERSAO)
            row = cur.fetchone()
        if row is None:
            raise RuntimeError(
                "parâmetro 'categoria_versao_vigente' ausente — migration 0002 "
                "não aplicada?"
            )
        return str(row[0])  # jsonb "1.0" → psycopg devolve a str "1.0"

    def buscar_excecao(self, ncm: str, versao: str) -> str | None:
        with self._con.cursor() as cur:
            cur.execute(_SQL_EXCECAO, {"ncm": ncm, "versao": versao})
            row = cur.fetchone()
        return str(row[0]) if row is not None else None

    def buscar_por_ncm(self, ncm: str, versao: str) -> str | None:
        with self._con.cursor() as cur:
            cur.execute(_SQL_POR_NCM, {"ncm": ncm, "versao": versao})
            row = cur.fetchone()
        return str(row[0]) if row is not None else None

    def buscar_por_palavra(self, descricao: str, versao: str) -> list[str]:
        with self._con.cursor() as cur:
            cur.execute(
                _SQL_POR_PALAVRA,
                {"descricao": _sem_acento(descricao), "versao": versao},
            )
            return [str(r[0]) for r in cur.fetchall()]
