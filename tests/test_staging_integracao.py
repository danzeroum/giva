"""Integração da sala de espera (exige Postgres). Verifica que uma carga em
staging não afeta a produção até ser promovida, que o diff descreve a mudança,
e que promover/rejeitar têm o efeito esperado."""

from __future__ import annotations

from giva.ncm.staging import (
    CargaNaoEmStagingError,
    carregar_staging,
    diff_carga,
    promover_carga,
    rejeitar_carga,
)

# Doc mínimo no formato do Classif. Contra o seed de demonstração (migration
# 0003: 84821000, 22030000, 94036000), este staging:
#   - altera 84821000 (descrição nova)
#   - adiciona 99999999 (novo)
#   - remove 22030000 e 94036000 (ausentes aqui)
_DOC = {
    "Nomenclaturas": [
        {
            "Codigo": "8482.10.00",
            "Descricao": "Rolamentos de esferas (redação nova de teste)",
            "Data_Inicio": "01/04/2022", "Data_Fim": "31/12/9999",
            "Tipo_Ato_Ini": "Res", "Numero_Ato_Ini": "272", "Ano_Ato_Ini": "2021",
        },
        {
            "Codigo": "9999.99.99",
            "Descricao": "Código totalmente novo",
            "Data_Inicio": "01/04/2022", "Data_Fim": "31/12/9999",
            "Tipo_Ato_Ini": "Res", "Numero_Ato_Ini": "272", "Ano_Ato_Ini": "2021",
        },
    ]
}


def _codigos_producao(con) -> set[str]:
    with con.cursor() as cur:
        cur.execute("SELECT codigo FROM ncm_vigente")
        return {r[0].strip() for r in cur.fetchall()}


def _carregar(con):
    return carregar_staging(
        con, _DOC, arquivo="teste", hash_arquivo="h", data_coleta="2026-07-01"
    )[0]


def test_staging_nao_afeta_producao_e_diff_descreve_mudanca(conexao):
    antes = _codigos_producao(conexao)
    carga_id = _carregar(conexao)
    # produção intacta enquanto em staging
    assert _codigos_producao(conexao) == antes
    diff = diff_carga(conexao, carga_id)
    assert diff.novos == 1 and "99999999" in diff.amostra_novos
    assert diff.alterados == 1 and "84821000" in diff.amostra_alterados
    assert diff.removidos == 2  # 22030000 e 94036000 do seed demo


def test_promover_troca_a_producao(conexao):
    carga_id = _carregar(conexao)
    promovidos = promover_carga(conexao, carga_id, por="tester")
    assert promovidos == 2
    assert _codigos_producao(conexao) == {"84821000", "99999999"}
    with conexao.cursor() as cur:
        cur.execute("SELECT status FROM carga WHERE id=%s", (carga_id,))
        assert cur.fetchone()[0] == "promovida"
        cur.execute("SELECT count(*) FROM ncm_vigente_staging WHERE carga_id=%s", (carga_id,))
        assert cur.fetchone()[0] == 0  # staging consumido


def test_rejeitar_preserva_producao(conexao):
    antes = _codigos_producao(conexao)
    carga_id = _carregar(conexao)
    rejeitar_carga(conexao, carga_id, por="tester")
    assert _codigos_producao(conexao) == antes  # produção intacta
    with conexao.cursor() as cur:
        cur.execute("SELECT status FROM carga WHERE id=%s", (carga_id,))
        assert cur.fetchone()[0] == "rejeitada"


def test_nao_promove_duas_vezes(conexao):
    carga_id = _carregar(conexao)
    promover_carga(conexao, carga_id, por="tester")
    try:
        promover_carga(conexao, carga_id, por="tester")
    except CargaNaoEmStagingError:
        return
    raise AssertionError("promover carga já promovida deveria falhar")
