"""RepositorioAliquota sobre psycopg — range join temporal em
`aliquota_icms_modal` (daterange @> período) cruzado com a proveniência da
carga. A exclusion constraint EXCLUDE USING gist garante no máximo uma
vigência por (uf, período); se vier mais de uma, é violação de invariante."""

from __future__ import annotations

from datetime import date
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

from giva.aliquota.resolvedor import VigenciaAliquota, VigenciaSobrepostaError

# Colunas repetidas nas duas consultas. Literais fixos (sem f-string/format e sem
# entrada do usuário) — os valores variáveis entram só por parâmetro (%(...)s).
_SQL_VIGENCIA = """
    SELECT a.uf,
           lower(a.vigencia)        AS vigencia_inicio,
           upper(a.vigencia)        AS vigencia_fim,
           a.aliquota_modal,
           a.fecp_percentual,
           a.fecp_incidencia,
           a.status_validacao,
           a.fonte_legal,
           a.fonte_compilada,
           c.data_coleta,
           c.id                      AS carga_id
      FROM aliquota_icms_modal a
      JOIN carga c ON c.id = a.carga_id
     WHERE a.uf = %(uf)s
       AND a.vigencia @> %(periodo)s::date
"""

_SQL_LISTAR_CORRENTES = """
    SELECT a.uf,
           lower(a.vigencia)        AS vigencia_inicio,
           upper(a.vigencia)        AS vigencia_fim,
           a.aliquota_modal,
           a.fecp_percentual,
           a.fecp_incidencia,
           a.status_validacao,
           a.fonte_legal,
           a.fonte_compilada,
           c.data_coleta,
           c.id                      AS carga_id
      FROM aliquota_icms_modal a
      JOIN carga c ON c.id = a.carga_id
     WHERE a.vigencia @> %(periodo)s::date
     ORDER BY a.uf
"""

_SQL_ATUALIZAR_STATUS = """
    UPDATE aliquota_icms_modal
       SET status_validacao = %(status_validacao)s
     WHERE uf = %(uf)s AND vigencia @> %(periodo)s::date
"""


def _vigencia(r: dict[str, Any]) -> VigenciaAliquota:
    return VigenciaAliquota(
        uf=r["uf"],
        vigencia_inicio=r["vigencia_inicio"],
        vigencia_fim=r["vigencia_fim"],
        aliquota_modal=r["aliquota_modal"],
        fecp_percentual=r["fecp_percentual"],
        fecp_incidencia=r["fecp_incidencia"],
        status_validacao=r["status_validacao"],
        fonte_legal=r["fonte_legal"],
        fonte_compilada=r["fonte_compilada"],
        data_coleta=r["data_coleta"],
        carga_id=r["carga_id"],
    )


class RepositorioAliquotaSQL:
    def __init__(self, conexao: Connection[Any]) -> None:
        self._con = conexao

    def buscar_vigencia(self, uf: str, periodo: date) -> VigenciaAliquota | None:
        with self._con.cursor(row_factory=dict_row) as cur:
            cur.execute(_SQL_VIGENCIA, {"uf": uf, "periodo": periodo})
            linhas = cur.fetchall()
        if not linhas:
            return None
        if len(linhas) > 1:  # a constraint EXCLUDE deveria impedir — invariante
            raise VigenciaSobrepostaError(uf, periodo, len(linhas))
        return _vigencia(linhas[0])

    def listar_vigencias_correntes(self, periodo: date) -> list[VigenciaAliquota]:
        """Todas as UFs com vigência cobrindo `periodo` (Bloco B — grid das
        27 UFs para validação fiscal)."""
        with self._con.cursor(row_factory=dict_row) as cur:
            cur.execute(_SQL_LISTAR_CORRENTES, {"periodo": periodo})
            return [_vigencia(r) for r in cur.fetchall()]

    def atualizar_status_validacao(
        self, uf: str, periodo: date, status_validacao: str
    ) -> bool:
        """Promove o `status_validacao` da vigência corrente da UF (Bloco B).
        Devolve False se não há vigência cobrindo `periodo` — nada a atualizar."""
        with self._con.cursor() as cur:
            cur.execute(
                _SQL_ATUALIZAR_STATUS,
                {"uf": uf, "periodo": periodo, "status_validacao": status_validacao},
            )
            return bool(cur.rowcount > 0)
