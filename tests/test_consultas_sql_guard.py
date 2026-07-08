"""Defesa em profundidade do SQL livre — camada de aplicação (sem banco).

Estes testes cobrem a parte crítica de segurança de `POST /consultas/sql`: o
validador puro `preparar_consulta`. Rodam sem Postgres (unidade), logo valem em
qualquer CI. As demais camadas (usuário read-only, read-only tx, timeout) são
verificadas na integração/produção.
"""

from __future__ import annotations

import pytest

from giva.api.consultas_sql import (
    LIMITE_PADRAO,
    TABELAS_PERMITIDAS,
    SqlNaoPermitidoError,
    preparar_consulta,
)


def test_select_valido_em_tabela_da_whitelist_passa_e_ganha_limit() -> None:
    saida = preparar_consulta("SELECT codigo FROM ncm_vigente")
    assert saida == (
        f"SELECT * FROM (SELECT codigo FROM ncm_vigente) AS giva_consulta LIMIT {LIMITE_PADRAO}"
    )


def test_limit_e_imposto_mesmo_com_limit_maior_do_usuario() -> None:
    saida = preparar_consulta("SELECT * FROM carga LIMIT 100000")
    # O LIMIT do usuário fica DENTRO do envelope; o cap externo é o que vale.
    assert saida.endswith(f"AS giva_consulta LIMIT {LIMITE_PADRAO}")
    assert "LIMIT 100000" in saida  # preservado no interno, mas envolvido


def test_join_entre_tabelas_permitidas_passa() -> None:
    sql = "SELECT v.codigo FROM ncm_vigente v JOIN carga c ON c.id = v.carga_id"
    assert preparar_consulta(sql).startswith("SELECT * FROM (")


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "   ",
        "UPDATE carga SET status = 'x'",
        "DELETE FROM carga",
        "INSERT INTO carga (fonte) VALUES ('x')",
        "DROP TABLE carga",
        "TRUNCATE carga",
        "ALTER TABLE carga ADD COLUMN x int",
        "GRANT SELECT ON carga TO x",
        "SELECT * FROM carga; DROP TABLE carga",
        "SELECT * FROM carga; SELECT * FROM carga",
        "WITH x AS (DELETE FROM carga RETURNING *) SELECT * FROM x",
        "SELECT * FROM carga -- comentário",
        "SELECT * FROM carga /* comentário */",
        "SELECT * FROM pg_roles",
        "SELECT * FROM information_schema.tables",
        "SELECT 1",
        "SELECT * FROM usuario",
        "SELECT * FROM segredos",
        "SELECT * INTO nova FROM carga",
    ],
)
def test_recusa_perigoso_ou_fora_da_whitelist(sql: str) -> None:
    with pytest.raises(SqlNaoPermitidoError):
        preparar_consulta(sql)


def test_case_insensitive() -> None:
    assert preparar_consulta("select * from CARGA").startswith("SELECT * FROM (")
    with pytest.raises(SqlNaoPermitidoError):
        preparar_consulta("DeLeTe FROM carga")


def test_mensagem_e_amigavel_para_leigo() -> None:
    with pytest.raises(SqlNaoPermitidoError) as exc:
        preparar_consulta("SELECT * FROM usuario")
    # cita a tabela e lista as disponíveis
    assert "usuario" in exc.value.mensagem
    assert "ncm_vigente" in exc.value.mensagem


def test_whitelist_bate_com_o_handoff() -> None:
    assert TABELAS_PERMITIDAS == {
        "ncm_vigente", "ncm_historico", "aliquota_icms_modal", "carga",
        "regras_excecao", "regra_ncm_categoria", "regra_palavra_categoria",
        "categoria", "parametro", "auditoria", "lote", "lote_linha", "contestacao",
    }
