"""Schema da operação (API + worker): usuário/RBAC, progresso de lote,
contestação e origem de exceção. Consolida numa migration o que dá suporte à
camada HTTP (ADR-07) e ao worker de fila (ADR-03).

- `usuario` + seed de 3 contas de dev (analista/operador/admin, argon2). As
  credenciais de seed são **exclusivas de desenvolvimento** — troque antes de
  expor a API.
- `lote.total_linhas`/`linhas_processadas` (progresso por chunk do worker) +
  `nome_arquivo` (nome original mostrado na tela "Meus lotes").
- `lote_linha.uf` (filtro por UF na revisão de pendências).
- `contestacao` ("Discordo desta linha").
- `regras_excecao`: origem (manual vs contestação), autor e data.

Reprodutível do zero (RNF-04).

Revision ID: 0004
"""
from alembic import op
from argon2 import PasswordHasher

revision = "0004"
down_revision = "0003"

_SENHA_DEV = "dev123456"  # só para as 3 contas de seed — nunca em produção


def upgrade() -> None:
    op.execute("""
    CREATE TABLE usuario (
        id         bigserial PRIMARY KEY,
        email      text NOT NULL UNIQUE,
        senha_hash text NOT NULL,
        papel      text NOT NULL CHECK (papel IN ('analista','operador','admin')),
        criado_em  timestamptz NOT NULL DEFAULT now()
    )""")
    hasher = PasswordHasher()
    hash_dev = hasher.hash(_SENHA_DEV).replace("'", "''")
    for email, papel in (
        ("analista@dev.local", "analista"),
        ("operador@dev.local", "operador"),
        ("admin@dev.local", "admin"),
    ):
        op.execute(
            f"INSERT INTO usuario (email, senha_hash, papel) "
            f"VALUES ('{email}', '{hash_dev}', '{papel}')"
        )

    op.execute("ALTER TABLE lote ADD COLUMN total_linhas integer")
    op.execute(
        "ALTER TABLE lote ADD COLUMN linhas_processadas integer NOT NULL DEFAULT 0"
    )
    op.execute("ALTER TABLE lote ADD COLUMN nome_arquivo text")
    op.execute("ALTER TABLE lote_linha ADD COLUMN uf text")

    op.execute("""
    CREATE TABLE contestacao (
        id            bigserial PRIMARY KEY,
        lote_id       bigint NOT NULL REFERENCES lote(id),
        numero_linha  int NOT NULL,
        autor_id      bigint NOT NULL REFERENCES usuario(id),
        tipo          text NOT NULL,
        texto         text NOT NULL,
        status        text NOT NULL CHECK (status IN ('aberta','resolvida')) DEFAULT 'aberta',
        resolucao     text,
        criado_em     timestamptz NOT NULL DEFAULT now(),
        resolvido_em  timestamptz,
        FOREIGN KEY (lote_id, numero_linha) REFERENCES lote_linha (lote_id, numero)
    )""")
    op.execute("CREATE INDEX ix_contestacao_lote ON contestacao (lote_id)")

    op.execute("ALTER TABLE regras_excecao ADD COLUMN origem_tipo text")
    op.execute(
        "ALTER TABLE regras_excecao ADD COLUMN origem_contestacao_id bigint "
        "REFERENCES contestacao(id)"
    )
    op.execute(
        "ALTER TABLE regras_excecao ADD COLUMN autor_id bigint REFERENCES usuario(id)"
    )
    op.execute(
        "ALTER TABLE regras_excecao ADD COLUMN criado_em timestamptz "
        "NOT NULL DEFAULT now()"
    )


def downgrade() -> None:
    for col in ("criado_em", "autor_id", "origem_contestacao_id", "origem_tipo"):
        op.execute(f"ALTER TABLE regras_excecao DROP COLUMN {col}")
    op.execute("DROP TABLE IF EXISTS contestacao CASCADE")
    op.execute("ALTER TABLE lote_linha DROP COLUMN uf")
    op.execute("ALTER TABLE lote DROP COLUMN nome_arquivo")
    op.execute("ALTER TABLE lote DROP COLUMN linhas_processadas")
    op.execute("ALTER TABLE lote DROP COLUMN total_linhas")
    op.execute("DROP TABLE IF EXISTS usuario CASCADE")
