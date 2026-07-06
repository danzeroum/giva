"""Seed de DEMONSTRAÇÃO da base de NCM (period-aware) — NÃO é a base de produção.

A base real de NCM vem do Classif/Siscomex (ingestão automatizada — fase da base
histórica; ver docs/roadmap.md). Este seed é um punhado de códigos, marcado
`fonte='seed_demo_ncm'`, que existe só para:
- demonstrar o lookup por período (descrição DA ÉPOCA vs. atual) — critério de
  aceite nº 1;
- exercitar a correlação SH 2022 (`codigo_alterado_pela_revisao_sh`);
- dar ao pipeline de demonstração códigos que resolvem.

Regra RN4 continua valendo em produção: nada de valor entra sem fonte
rastreável. Um deploy real substitui este seed pela carga do Classif.

Revision ID: 0003
"""
from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade() -> None:
    con = op.get_bind()
    carga_id = con.exec_driver_sql(
        "INSERT INTO carga (fonte, arquivo_bruto, hash_arquivo, data_coleta, "
        "promovido_em, promovido_por) VALUES "
        "('seed_demo_ncm','migration_0003','seed-demo-0003','2026-07-01', now(), 'migration') "
        "RETURNING id"
    ).scalar_one()

    # Redação vigente (snapshot Classif) de alguns códigos.
    vigentes = [
        ("84821000", "Rolamentos de esferas", "2022-04-01", "Resolução", "272", "2021"),
        ("22030000", "Cervejas de malte", "2022-04-01", "Resolução", "272", "2021"),
        ("94036000", "Outros móveis de madeira", "2022-04-01", "Resolução", "272", "2021"),
    ]
    for codigo, descricao, inicio, ato_t, ato_n, ato_a in vigentes:
        con.exec_driver_sql(
            "INSERT INTO ncm_vigente (codigo, descricao, data_inicio, ato_tipo, "
            "ato_numero, ato_ano, carga_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (codigo, descricao, inicio, ato_t, ato_n, ato_a, carga_id),
        )

    # Histórico bitemporal: 84821000 teve redação diferente ANTES da revisão SH
    # 2022 (Gecex 272/2021, vigência 01/04/2022). Duas janelas contíguas, sem
    # sobreposição (EXCLUDE gist garante) — o lookup por período escolhe a certa.
    historico = [
        ("84821000", "2017-01-01", "2022-04-01",
         "Rolamentos de esferas (redação anterior à revisão SH 2022)",
         "Resolução", "125", "2016"),
        ("84821000", "2022-04-01", None,
         "Rolamentos de esferas", "Resolução", "272", "2021"),
    ]
    for codigo, ini, fim, descricao, ato_t, ato_n, ato_a in historico:
        limite = "NULL" if fim is None else "%s"
        params = [codigo, ini] + ([] if fim is None else [fim]) + [
            descricao, ato_t, ato_n, ato_a, carga_id
        ]
        con.exec_driver_sql(
            "INSERT INTO ncm_historico (codigo, vigencia, descricao, ato_tipo, "
            f"ato_numero, ato_ano, carga_id) VALUES (%s, daterange(%s, {limite}, '[)'), "
            "%s,%s,%s,%s,%s)",
            tuple(params),
        )

    # Correlação SH 2022: um código extinto que virou outro — o resolvedor marca
    # `codigo_alterado_pela_revisao_sh` em vez de `codigo_inexistente`.
    con.exec_driver_sql(
        "INSERT INTO ncm_correlacao (codigo_anterior, codigo_novo, "
        "vigencia_transicao, carga_id) VALUES ('84829900','84824000','2022-04-01',%s)",
        (carga_id,),
    )


def downgrade() -> None:
    con = op.get_bind()
    for tabela in ("ncm_historico", "ncm_correlacao", "ncm_vigente"):
        con.exec_driver_sql(
            f"DELETE FROM {tabela} WHERE carga_id IN "
            "(SELECT id FROM carga WHERE fonte='seed_demo_ncm')"
        )
    con.exec_driver_sql("DELETE FROM carga WHERE fonte='seed_demo_ncm'")
