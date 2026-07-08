"""Papel Postgres read-only para o SQL livre de "Consultas prontas" (camada 1
da defesa em profundidade — ver giva.api.consultas_sql / routers/consultas.py).

Cria o papel `giva_readonly` com **apenas SELECT** nas tabelas da whitelist e
USAGE no schema. Idempotente: pode rodar em bancos onde o papel já existe.

O papel nasce NOLOGIN e SEM senha — nenhum segredo entra no versionamento. Para
usá-lo em produção, o operador cria um usuário de login e o vincula:

    CREATE ROLE giva_ro LOGIN PASSWORD '...';   -- senha fora do VCS
    GRANT giva_readonly TO giva_ro;

e aponta READONLY_DATABASE_URL para `giva_ro`. Sem READONLY_DATABASE_URL, o app
cai no DSN principal (config.dsn_readonly) — as outras camadas (SELECT-only,
whitelist, LIMIT, read-only tx, statement_timeout, auditoria) seguem valendo.

Revision ID: 0007
"""
from alembic import op

revision = "0007"
down_revision = "0006"

# Espelha giva.api.consultas_sql.TABELAS_PERMITIDAS (whitelist do handoff).
_TABELAS = (
    "ncm_vigente", "ncm_historico", "aliquota_icms_modal", "carga",
    "regras_excecao", "regra_ncm_categoria", "regra_palavra_categoria",
    "categoria", "parametro", "auditoria", "lote", "lote_linha", "contestacao",
)


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'giva_readonly') THEN
            CREATE ROLE giva_readonly NOLOGIN;
          END IF;
        END $$;
        """
    )
    op.execute("GRANT USAGE ON SCHEMA public TO giva_readonly")
    for tabela in _TABELAS:
        # `tabela` é constante fixa deste módulo (nunca entrada de usuário).
        op.execute(f"GRANT SELECT ON {tabela} TO giva_readonly")  # nosec B608


def downgrade() -> None:
    for tabela in _TABELAS:
        op.execute(f"REVOKE SELECT ON {tabela} FROM giva_readonly")  # nosec B608
    op.execute("REVOKE USAGE ON SCHEMA public FROM giva_readonly")
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'giva_readonly') THEN
            DROP ROLE giva_readonly;
          END IF;
        END $$;
        """
    )
