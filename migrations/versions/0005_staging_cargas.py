"""Sala de espera das cargas de NCM (Fase 5): staging → revisão → promoção.

Antes, carregar e promover eram a mesma operação (a `carga` nascia com
`promovido_em = now()`). Aqui separa-se:

- `carga.status` ∈ `{staging, promovida, rejeitada}` — o ciclo de vida.
- `ncm_vigente_staging` — onde a carga fica ANTES de virar produção. O motor de
  enriquecimento continua lendo só `ncm_vigente` (produção), então nada em
  staging afeta resultado até ser promovido (revisão humana antes de valer).

Cargas já existentes (seeds) recebem `status='promovida'` (default) — elas já
estavam em produção.

Revision ID: 0005
"""
from alembic import op

revision = "0005"
down_revision = "0004"


def upgrade() -> None:
    op.execute(
        "ALTER TABLE carga ADD COLUMN status text NOT NULL DEFAULT 'promovida' "
        "CHECK (status IN ('staging','promovida','rejeitada'))"
    )
    op.execute("ALTER TABLE carga ADD COLUMN rejeitado_em timestamptz")
    op.execute("ALTER TABLE carga ADD COLUMN rejeitado_por text")

    op.execute("""
    CREATE TABLE ncm_vigente_staging (
        carga_id    bigint NOT NULL REFERENCES carga(id) ON DELETE CASCADE,
        codigo      char(8) NOT NULL,
        descricao   text NOT NULL,
        data_inicio date NOT NULL,
        ato_tipo    text, ato_numero text, ato_ano text,
        PRIMARY KEY (carga_id, codigo)
    )""")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ncm_vigente_staging CASCADE")
    op.execute("ALTER TABLE carga DROP COLUMN rejeitado_por")
    op.execute("ALTER TABLE carga DROP COLUMN rejeitado_em")
    op.execute("ALTER TABLE carga DROP COLUMN status")
