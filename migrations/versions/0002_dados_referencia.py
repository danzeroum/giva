"""Dados de referência (trilha de dados, plano §3.3): taxonomia das 18
categorias EFD + regras de enquadramento (doc 04) + parâmetros + seed das
alíquotas modais das 27 UFs (2026, modal nominal sem FECP — decisão GIVA §3).

Tudo aqui é *dado versionado*, não schema. Versão da taxonomia = '1.0'.

Revision ID: 0002
"""
import json

from alembic import op

revision = "0002"
down_revision = "0001"

VERSAO = "1.0"

# --- 18 categorias EFD (doc 04 §1), ordenadas por volume do trabalho real -----
CATEGORIAS = [
    "Material de manutenção",
    "Peça de máquina",
    "Material elétrico",
    "Material de limpeza",
    "EPI",
    "Material de escritório e informática",
    "Gás",
    "Produto químico",
    "Ferramentas",
    "Combustível e lubrificante",
    "Material de construção",
    "Serviço",
    "Alimentação",
    "Material de embalagem",
    "Brindes",
    "Material de jardinagem",
    "Material de laboratório",
    "Indefinido",
]

# --- Regras por faixa de NCM (doc 04 §2.1) — prefixo mais longo vence ---------
# Prefixos amplos (capítulo) convivem com posições específicas: p.ex. "84" cai
# em Peça de máquina, mas "8471" (informática) sobrepõe por ser mais específico.
REGRAS_NCM = [
    ("84", "Peça de máquina"),           # cap. 84 — máquinas mecânicas
    ("8482", "Peça de máquina"),         # rolamentos
    ("8483", "Peça de máquina"),         # transmissão
    ("8484", "Peça de máquina"),         # juntas/vedações
    ("8477", "Peça de máquina"),         # máquinas p/ borracha/plástico
    ("8443", "Material de escritório e informática"),  # impressão
    ("8471", "Material de escritório e informática"),  # informática
    ("85", "Material elétrico"),         # cap. 85 — material elétrico
    ("8536", "Material elétrico"),       # aparelhagem
    ("8516", "Material elétrico"),       # resistências
    ("8544", "Material elétrico"),       # cabos/fios
    ("8517", "Material de escritório e informática"),  # telefonia
    ("8518", "Material de escritório e informática"),  # áudio/headset
    ("48", "Material de escritório e informática"),    # cap. 48 — papel (genérico)
    ("4818", "Material de limpeza"),     # higiênico/toalha
    ("3401", "Material de limpeza"),     # sabões
    ("3402", "Material de limpeza"),     # tensoativos
    ("32", "Produto químico"),           # tintas/pigmentos
    ("35", "Produto químico"),           # colas
    ("38", "Produto químico"),           # químicos diversos
    ("2207", "Produto químico"),         # álcool etílico (uso industrial)
    ("3923", "Material de embalagem"),   # embalagem de plástico
    ("82", "Ferramentas"),               # cap. 82 — ferramentas manuais
    ("9017", "Material de escritório e informática"),  # régua/desenho
    ("9603", "Material de limpeza"),     # vassoura/escova
    ("9608", "Material de escritório e informática"),  # canetas
    ("9612", "Material de escritório e informática"),  # ribbon
    ("2804", "Gás"),                     # oxigênio/nitrogênio/argônio
    ("2711", "Gás"),                     # GLP e gases de petróleo
    ("2710", "Combustível e lubrificante"),  # óleos de petróleo
    ("2523", "Material de construção"),  # cimento
]

# --- Regras por palavra-chave (doc 04 §2.2) — gravadas em minúsculas SEM acento
# (o repositório normaliza a descrição do mesmo jeito antes de casar).
_PALAVRAS = {
    "EPI": [
        "luva", "botina", "oculos de seguranca", "capacete",
        "protetor auricular", "mascara respirat", "filtro respirat", "cinta lombar",
    ],
    "Peça de máquina": [
        "rolamento", "acoplamento", "selo mecanico", "rotor", "eixo",
        "bucha", "vedacao", "engrenagem",
    ],
    "Material elétrico": [
        "disjuntor", "rele", "terminal", "led", "temporizador",
        "resistencia", "fita isolante", "tomada", "cabo",
    ],
    "Ferramentas": [
        "chave de fenda", "chave allen", "mandril", "alicate",
        "lamina", "chave de impacto",
    ],
    "Material de limpeza": [
        "papel higienico", "toalha de papel", "sabonete", "detergente",
        "saco de lixo", "palha de aco", "vassoura", "fibra",
    ],
    "Material de escritório e informática": [
        "papel a4", "caneta", "etiqueta", "mouse", "teclado",
        "headset", "regua", "ribbon", "mouse pad",
    ],
    "Gás": ["oxigenio", "acetileno", "nitrogenio", "argonio", "glp", "gas"],
    "Combustível e lubrificante": [
        "graxa", "oleo", "lubrificante", "desengraxante", "silicone aerossol",
    ],
    "Produto químico": [
        "alcool", "thinner", "tinta", "cola", "silicone acetico",
        "fixador", "solvente",
    ],
    "Material de construção": ["cimento", "areia", "pedra", "tijolo", "granito"],
    "Alimentação": ["cafe", "acucar", "adocante", "agua", "restaurante"],
    "Material de embalagem": [
        "balde", "copo descartavel", "big bag", "papelao ondulado",
        "fitilho", "saco plastico",
    ],
    "Serviço": [
        "frete", "servico", "manutencao de veiculo", "hospedagem",
        "sedex", "despesas com",
    ],
    "Brindes": ["cracha", "camisa promocional", "brinde", "ovo de pascoa"],
    "Material de laboratório": [
        "bequer", "proveta", "erlenmeyer", "pipeta", "mufla", "navicula",
    ],
    "Material de manutenção": [
        "solda", "eletrodo", "abracadeira", "vareta", "perfil de borracha",
        "barra de latao", "tubo", "valvula",
    ],
    "Material de jardinagem": ["jardinagem", "jardim"],
}

# --- Seed das alíquotas modais 2026 (27 UFs) — modal nominal, sem FECP ---------
# (uf, aliquota_modal, fecp_percentual|None, fecp_incidencia, status_validacao,
#  fonte_legal|None). Base: SimTax — Tabela ICMS 2026 (fonte compilada); a modal
#  é o valor entregue (decisão GIVA §3). Nenhuma UF está 'validada' — em produção
#  cai em 'pendente_validacao_uf' até a varredura oficial (playbook).
ALIQUOTAS = [
    ("AC", "19.0", None, "a_validar", "pendente_validacao", None),
    ("AL", "20.5", "1.0", "ampla", "confirmada_fonte_secundaria", "Lei estadual nº 9.776/2025"),
    ("AM", "20.0", None, "a_validar", "pendente_validacao", None),
    ("AP", "18.0", None, "a_validar", "pendente_validacao", None),
    ("BA", "20.5", "2.0", "produtos_selecionados", "confirmada_fonte_secundaria", None),
    ("CE", "20.0", "2.0", "produtos_selecionados", "pendente_validacao", None),
    ("DF", "20.0", "2.0", "produtos_selecionados", "pendente_validacao", None),
    ("ES", "17.0", None, "a_validar", "pendente_validacao", None),
    ("GO", "19.0", "2.0", "produtos_selecionados", "pendente_validacao", None),
    ("MA", "23.0", "2.0", "a_validar", "confirmada_fonte_secundaria", None),
    ("MG", "18.0", "2.0", "produtos_selecionados", "confirmada_fonte_secundaria", None),
    ("MS", "17.0", None, "a_validar", "pendente_validacao", None),
    ("MT", "17.0", None, "a_validar", "pendente_validacao", None),
    ("PA", "19.0", None, "a_validar", "pendente_validacao", None),
    ("PB", "20.0", "2.0", "a_validar", "pendente_validacao", None),
    ("PE", "20.5", "2.0", "a_validar", "divergencia_entre_fontes", None),
    ("PI", "22.5", "2.0", "a_validar", "divergencia_entre_fontes", None),
    ("PR", "19.5", "2.0", "produtos_selecionados", "confirmada_fonte_secundaria", None),
    ("RJ", "20.0", "2.0", "ampla", "confirmada_fonte_secundaria",
     "Lei nº 2.657/96, art. 14, I + LC nº 210/2023 (FECP)"),
    ("RN", "20.0", "2.0", "a_validar", "pendente_validacao", None),
    ("RO", "19.5", None, "a_validar", "pendente_validacao", None),
    ("RR", "20.0", None, "a_validar", "pendente_validacao", None),
    ("RS", "17.0", "2.0", "produtos_selecionados", "confirmada_fonte_secundaria", None),
    ("SC", "17.0", None, "a_validar", "confirmada_fonte_secundaria", None),
    ("SE", "19.0", "1.0", "ampla", "pendente_validacao", None),
    ("SP", "18.0", "2.0", "produtos_selecionados", "confirmada_fonte_secundaria",
     "RICMS/SP (Dec. 45.490/2000), art. 52, I"),
    ("TO", "20.0", None, "a_validar", "pendente_validacao", None),
]

_FONTE_COMPILADA = "SimTax — Tabela ICMS 2026 (abr/2026, atual. mai/2026)"


def upgrade() -> None:
    con = op.get_bind()

    # Carga de proveniência para categorias e alíquotas do seed.
    carga_id = con.exec_driver_sql(
        "INSERT INTO carga (fonte, arquivo_bruto, hash_arquivo, data_coleta, "
        "promovido_em, promovido_por) VALUES "
        "('seed_referencia','migration_0002','seed-0002','2026-07-01', now(), 'migration') "
        "RETURNING id"
    ).scalar_one()

    for ordem, nome in enumerate(CATEGORIAS, start=1):
        con.exec_driver_sql(
            "INSERT INTO categoria (nome, ordem, versao) VALUES (%s, %s, %s)",
            (nome, ordem, VERSAO),
        )

    for prefixo, categoria in REGRAS_NCM:
        con.exec_driver_sql(
            "INSERT INTO regra_ncm_categoria (prefixo, categoria, versao) "
            "VALUES (%s, %s, %s)",
            (prefixo, categoria, VERSAO),
        )

    for categoria, palavras in _PALAVRAS.items():
        for palavra in palavras:
            con.exec_driver_sql(
                "INSERT INTO regra_palavra_categoria (palavra, categoria, versao) "
                "VALUES (%s, %s, %s)",
                (palavra, categoria, VERSAO),
            )

    for uf, modal, fecp, incid, validacao, fonte_legal in ALIQUOTAS:
        con.exec_driver_sql(
            "INSERT INTO aliquota_icms_modal "
            "(uf, vigencia, aliquota_modal, fecp_percentual, fecp_incidencia, "
            " fonte_legal, fonte_compilada, status_validacao, carga_id) "
            "VALUES (%s, daterange(%s, NULL, '[)'), %s, %s, %s, %s, %s, %s, %s)",
            (uf, "2026-01-01", modal, fecp, incid, fonte_legal,
             _FONTE_COMPILADA, validacao, carga_id),
        )

    for nome, valor in (
        ("t_ok", 0.85),
        ("t_rev", 0.60),
        ("categoria_versao_vigente", VERSAO),
    ):
        con.exec_driver_sql(
            "INSERT INTO parametro (nome, valor) VALUES (%s, %s)",
            (nome, json.dumps(valor)),
        )


def downgrade() -> None:
    con = op.get_bind()
    for tabela in (
        "regra_palavra_categoria", "regra_ncm_categoria", "regras_excecao",
        "categoria", "aliquota_icms_modal", "parametro",
    ):
        con.exec_driver_sql(f"DELETE FROM {tabela}")
    con.exec_driver_sql(
        "DELETE FROM carga WHERE fonte = 'seed_referencia'"
    )
