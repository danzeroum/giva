"""Schema núcleo (plano §3.3): bases de referência com vigências bitemporais,
exclusion constraints de não sobreposição, lotes e auditoria.

Diferença para o enriquecedor-fiscal: a categorização usa a taxonomia das 18
categorias EFD (doc 04), com regras por faixa de NCM e por palavra-chave —
tabelas `categoria`, `regra_ncm_categoria`, `regra_palavra_categoria` no lugar
de `sh4_categoria`.

Revision ID: 0001
"""
from alembic import op

revision = "0001"
down_revision = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.execute("""
    CREATE TABLE carga (
        id            bigserial PRIMARY KEY,
        fonte         text NOT NULL,  -- classif_json | classif_export_hist | seed_referencia
        arquivo_bruto text NOT NULL,              -- arquivo arquivado (rastreabilidade §3.2)
        hash_arquivo  text NOT NULL,
        data_coleta   date NOT NULL,
        criado_em     timestamptz NOT NULL DEFAULT now(),
        promovido_em  timestamptz,                -- NULL = staging/quarentena
        promovido_por text
    )""")

    op.execute("""
    CREATE TABLE ncm_vigente (
        codigo       char(8) PRIMARY KEY,
        descricao    text NOT NULL,
        data_inicio  date NOT NULL,               -- início da redação vigente (Classif)
        ato_tipo     text, ato_numero text, ato_ano text,
        carga_id     bigint NOT NULL REFERENCES carga(id)
    )""")

    op.execute("""
    CREATE TABLE ncm_historico (
        codigo    char(8) NOT NULL,
        vigencia  daterange NOT NULL,
        descricao text NOT NULL,
        ato_tipo  text, ato_numero text, ato_ano text,
        carga_id  bigint NOT NULL REFERENCES carga(id),
        PRIMARY KEY (codigo, vigencia),
        EXCLUDE USING gist (codigo WITH =, vigencia WITH &&)   -- não sobreposição (§3.3)
    )""")

    op.execute("""
    CREATE TABLE ncm_correlacao (
        codigo_anterior char(8) NOT NULL,
        codigo_novo     char(8) NOT NULL,
        vigencia_transicao date NOT NULL,          -- 2022-04-01 para a revisão SH 2022
        carga_id        bigint NOT NULL REFERENCES carga(id),
        PRIMARY KEY (codigo_anterior, codigo_novo)
    )""")

    # Decisão GIVA §3: alíquota entregue é a modal nominal, sem FECP (playbook §5).
    # Os campos de FECP ficam na base como referência/proveniência, não somam.
    op.execute("""
    CREATE TABLE aliquota_icms_modal (
        uf               char(2) NOT NULL,
        vigencia         daterange NOT NULL,
        aliquota_modal   numeric(4,1) NOT NULL CHECK (aliquota_modal BETWEEN 0 AND 30),
        fecp_percentual  numeric(4,1) CHECK (fecp_percentual BETWEEN 0 AND 5),
        fecp_incidencia  text NOT NULL CHECK (fecp_incidencia IN
                          ('ampla','produtos_selecionados','inexistente','a_validar')),
        fonte_legal      text,
        fonte_compilada  text NOT NULL,
        status_validacao text NOT NULL CHECK (status_validacao IN
                          ('validada','confirmada_fonte_secundaria',
                           'divergencia_entre_fontes','pendente_validacao')),
        observacoes      text,
        carga_id         bigint NOT NULL REFERENCES carga(id),
        PRIMARY KEY (uf, vigencia),
        EXCLUDE USING gist (uf WITH =, vigencia WITH &&)
    )""")

    # Taxonomia das 18 categorias EFD (doc 04) — configurável e versionada.
    op.execute("""
    CREATE TABLE categoria (
        nome    text NOT NULL,
        ordem   int  NOT NULL,                     -- ordem de exibição/precedência de curadoria
        versao  text NOT NULL,
        PRIMARY KEY (nome, versao)
    )""")

    # Regra por faixa de NCM (§2.1): prefixo (capítulo/posição) → categoria.
    # O prefixo mais específico (mais longo) que casar decide (Categorizador).
    op.execute("""
    CREATE TABLE regra_ncm_categoria (
        prefixo   text NOT NULL,                   -- 2..8 dígitos do NCM
        categoria text NOT NULL,
        versao    text NOT NULL,
        PRIMARY KEY (prefixo, versao),
        FOREIGN KEY (categoria, versao) REFERENCES categoria(nome, versao)
    )""")

    # Regra por palavra-chave na descrição (§2.2, fallback quando o NCM não resolve).
    op.execute("""
    CREATE TABLE regra_palavra_categoria (
        palavra   text NOT NULL,                   -- gatilho (armazenado em minúsculas)
        categoria text NOT NULL,
        versao    text NOT NULL,
        PRIMARY KEY (palavra, versao),
        FOREIGN KEY (categoria, versao) REFERENCES categoria(nome, versao)
    )""")

    # Exceção por NCM exato (curadoria/uso) — vence as regras acima.
    op.execute("""
    CREATE TABLE regras_excecao (
        ncm           char(8) NOT NULL,
        categoria     text NOT NULL,
        justificativa text NOT NULL,
        versao        text NOT NULL,
        PRIMARY KEY (ncm, versao),
        FOREIGN KEY (categoria, versao) REFERENCES categoria(nome, versao)
    )""")

    op.execute("""
    CREATE TABLE tabela_decisao (
        nome    text NOT NULL,
        versao  text NOT NULL,
        regras  jsonb NOT NULL,
        vigente boolean NOT NULL DEFAULT false,
        PRIMARY KEY (nome, versao)
    )""")

    op.execute("""
    CREATE TABLE parametro (
        nome  text PRIMARY KEY,                    -- t_ok, t_rev, categoria_versao_vigente (RF-24)
        valor jsonb NOT NULL,
        atualizado_em timestamptz NOT NULL DEFAULT now()
    )""")

    op.execute("""
    CREATE TABLE lote (
        id         bigserial PRIMARY KEY,
        status     text NOT NULL CHECK (status IN ('recebido','processando','concluido','erro')),
        arquivo_entrada text NOT NULL,
        arquivo_saida   text,
        criado_por text NOT NULL,
        criado_em  timestamptz NOT NULL DEFAULT now(),
        concluido_em timestamptz,
        resumo     jsonb
    )""")

    op.execute("""
    CREATE TABLE lote_linha (
        lote_id   bigint NOT NULL REFERENCES lote(id),
        numero    int NOT NULL,
        originais jsonb NOT NULL,                 -- valores como vieram (colunas *_original)
        enriquecido jsonb,
        statuses  jsonb,
        proveniencia jsonb,                       -- por campo (RNF-04)
        regras_disparadas jsonb,                  -- insumo do process mining (§5.3)
        PRIMARY KEY (lote_id, numero)
    )""")

    op.execute("""
    CREATE TABLE auditoria (
        id       bigserial PRIMARY KEY,
        quem     text NOT NULL,
        quando   timestamptz NOT NULL DEFAULT now(),
        acao     text NOT NULL,
        alvo     text NOT NULL,
        antes    jsonb,
        depois   jsonb
    )""")

    op.execute("CREATE INDEX ix_ncm_hist_codigo ON ncm_historico (codigo)")
    op.execute("CREATE INDEX ix_aliquota_uf ON aliquota_icms_modal (uf)")
    op.execute("CREATE INDEX ix_lote_linha_lote ON lote_linha (lote_id)")


def downgrade() -> None:
    for t in ("auditoria","lote_linha","lote","parametro","tabela_decisao",
              "regras_excecao","regra_palavra_categoria","regra_ncm_categoria","categoria",
              "aliquota_icms_modal","ncm_correlacao","ncm_historico","ncm_vigente","carga"):
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
