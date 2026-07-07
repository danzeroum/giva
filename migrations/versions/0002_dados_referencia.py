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
    ("4808", "Material de embalagem"),   # papelão ondulado (embalagem)
    ("2207", "Produto químico"),         # álcool etílico (uso industrial)
    ("3923", "Material de embalagem"),   # embalagem de plástico
    ("82", "Ferramentas"),               # cap. 82 — ferramentas manuais
    ("8481", "Material de manutenção"),  # torneiras/válvulas de uso geral
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
        "lamina", "chave de impacto", "martelo",
    ],
    "Material de limpeza": [
        "papel higienico", "toalha de papel", "sabonete", "detergente",
        "saco de lixo", "palha de aco", "vassoura", "fibra",
        # 'luva' e 'saco plastico' também apontam limpeza — de propósito: com EPI
        # e Embalagem, o termo sozinho vira AMBÍGUO (Indefinido-ambíguo, Baixa),
        # que é o comportamento correto de fronteira (doc 04 §3 — não decidir só).
        "luva", "saco plastico",
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

# --- Alíquotas modais — histórico decenal, NOMINAIS sem FECP (decisão GIVA §3) -
# 11 UFs do seed do playbook §7 entram VALIDADAS, com as viradas verificadas em
# fonte oficial (RJ/PR/RS/GO/CE). As demais 16 UFs entram pendentes: em produção
# o sistema responde REQUER VALIDAÇÃO MANUAL (RN4 — nunca chutar), até a varredura
# oficial de cada estado.
# Cada tupla validada: (uf, inicio, fim|None, modal, fonte_legal).
VALIDADAS = [
    ("SP", "2016-01-01", None, "18.0", "RICMS/SP (Dec. 45.490/2000), art. 52, I"),
    ("MG", "2016-01-01", None, "18.0", "RICMS/MG, art. 42"),
    ("SC", "2016-01-01", None, "17.0", "RICMS/SC, art. 26"),
    ("ES", "2016-01-01", None, "17.0", "RICMS/ES"),
    ("BA", "2016-01-01", None, "18.0", "Playbook §7 (2016–2021)"),
    ("AL", "2016-01-01", None, "18.0", "Playbook §7 (2016–2021)"),
    ("RJ", "2016-01-01", "2024-03-20", "18.0", "Lei nº 2.657/96, art. 14, I"),
    ("RJ", "2024-03-20", None, "20.0", "Lei nº 10.253/2023 (virada 20/03/2024)"),
    ("PR", "2016-01-01", "2023-03-13", "18.0", "RICMS/PR"),
    ("PR", "2023-03-13", None, "19.0", "Lei nº 21.308/2022 (virada 13/03/2023)"),
    ("RS", "2016-01-01", "2021-01-01", "18.0", "RICMS/RS"),
    ("RS", "2021-01-01", "2022-01-01", "17.5", "Lei nº 15.576/2020 (17,5% em 2021)"),
    ("RS", "2022-01-01", None, "17.0", "Lei nº 15.576/2020 (17% a partir de 2022)"),
    ("GO", "2016-01-01", "2024-04-01", "17.0", "RICMS/GO"),
    ("GO", "2024-04-01", None, "19.0", "Lei nº 22.460/2023 (virada 01/04/2024)"),
    ("CE", "2016-01-01", "2024-01-01", "18.0", "RICMS/CE"),
    ("CE", "2024-01-01", None, "20.0", "Lei nº 18.305/2023 (virada 01/01/2024)"),
]

# 16 UFs fora do seed — modal de referência (SimTax 2026), status pendente.
PENDENTES = {
    "AC": "19.0", "AM": "20.0", "AP": "18.0", "DF": "20.0", "MA": "23.0",
    "MS": "17.0", "MT": "17.0", "PA": "19.0", "PB": "20.0", "PE": "20.5",
    "PI": "22.5", "RN": "20.0", "RO": "19.5", "RR": "20.0", "SE": "19.0",
    "TO": "20.0",
}

_FONTE_COMPILADA = "Playbook §7 (viradas verificadas em fonte oficial) / SimTax 2026"


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

    for uf, inicio, fim, modal, fonte_legal in VALIDADAS:
        limite = "NULL" if fim is None else "%s"
        params = (
            [uf, inicio] + ([] if fim is None else [fim])
            + [modal, fonte_legal, _FONTE_COMPILADA, carga_id]
        )
        con.exec_driver_sql(
            "INSERT INTO aliquota_icms_modal "
            "(uf, vigencia, aliquota_modal, fecp_incidencia, fonte_legal, "
            " fonte_compilada, status_validacao, carga_id) "
            f"VALUES (%s, daterange(%s, {limite}, '[)'), %s, 'a_validar', %s, %s, "
            "'validada', %s)",
            tuple(params),
        )
    for uf, modal in PENDENTES.items():
        con.exec_driver_sql(
            "INSERT INTO aliquota_icms_modal "
            "(uf, vigencia, aliquota_modal, fecp_incidencia, fonte_compilada, "
            " status_validacao, carga_id) "
            "VALUES (%s, daterange('2016-01-01', NULL, '[)'), %s, 'a_validar', %s, "
            "'pendente_validacao', %s)",
            (uf, modal, _FONTE_COMPILADA, carga_id),
        )

    # Limiares da divergência de descrição (RF-24) — calibrados com a amostra
    # real (planilha-teste/gabarito): a descrição oficial passou a ser a de
    # subposição (mais descritiva), então a régua desce de 0,85/0,60.
    for nome, valor in (
        ("t_ok", 0.34),
        ("t_rev", 0.15),
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
