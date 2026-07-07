"""Descrição de POSIÇÃO/subposição do NCM (6 dígitos) — o nível público estável
usado como referência da divergência de descrição (gabarito: 'descricao_oficial
= descrição de POSIÇÃO NCM'). Carregada do Classif junto com o vigente.

Não passa pela sala de espera: são rótulos estruturais estáveis (mudam pouco),
carregados direto pela rotina de ingestão. O motor usa a subposição como
descrição oficial quando não há a redação de época (8 dígitos por período).

Revision ID: 0006
"""
from alembic import op

revision = "0006"
down_revision = "0005"


def upgrade() -> None:
    op.execute("""
    CREATE TABLE ncm_posicao (
        prefixo   char(6) PRIMARY KEY,       -- subposição (6 dígitos, sem pontuação)
        descricao text NOT NULL,
        carga_id  bigint NOT NULL REFERENCES carga(id)
    )""")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ncm_posicao CASCADE")
