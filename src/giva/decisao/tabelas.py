"""Tabelas de decisão DT-01..DT-04 (PRD GIVA §4 / plano §4).

Estas definições são a versão embarcada inicial; em produção, as tabelas
vivem em `tabela_decisao` (JSONB, versionadas — migration 0002) e são
carregadas de lá. Manter este módulo e o banco em sincronia é parte do
Definition of Done de qualquer mudança de regra.

Convenção: a última regra de cada tabela é o catch-all.

DECISÃO GIVA (registro de decisões §3): a alíquota entregue é a **modal
nominal, sem FECP** (playbook §5). A DT-02 aqui NÃO tem o galho de
`fecp_incidencia` que existe no enriquecedor-fiscal — a fórmula liberada é
sempre `modal`. Os campos de FECP continuam na base (`aliquota_icms_modal`)
como referência/proveniência, mas não somam no valor entregue ao cliente.
"""

from __future__ import annotations

from giva.decisao.interpretador import (
    Diferente,
    Igual,
    MaiorIgualParametro,
    NaoNulo,
    Qualquer,
    Regra,
    TabelaDecisao,
)

# ---------------------------------------------------------------------------
# DT-01 — status_ncm
# Entradas: codigo_existe (bool) · periodo_cobre_vigente (bool | None)
#           · tem_correlacao (bool)
# ---------------------------------------------------------------------------
DT01_STATUS_NCM = TabelaDecisao(
    nome="DT-01_status_ncm",
    versao="1.0",
    regras=(
        Regra(
            numero=1,
            quando={"codigo_existe": Igual(False), "tem_correlacao": Igual(True)},
            entao={"status_ncm": "codigo_alterado_pela_revisao_sh"},
        ),
        Regra(
            numero=2,
            quando={"codigo_existe": Igual(False)},
            entao={"status_ncm": "codigo_inexistente"},
        ),
        Regra(
            numero=3,
            quando={"codigo_existe": Igual(True), "periodo_cobre_vigente": Igual(True)},
            entao={"status_ncm": "ok"},
        ),
        Regra(  # catch-all: existe, mas o período antecede a redação vigente
            numero=4,
            quando={"codigo_existe": Qualquer()},
            entao={"status_ncm": "descricao_vigente_periodo_nao_carregado"},
        ),
    ),
)

# ---------------------------------------------------------------------------
# DT-02 — alíquota interna (modal, sem FECP) e status_aliquota
# Entradas: vigencia_encontrada (bool) · status_validacao (str | None)
# Saída `formula_efetiva`: quem calcula é o ResolutorAliquota; a DT decide
# APENAS qual fórmula se aplica. Só existe a fórmula `modal` (decisão GIVA:
# entrega a modal nominal sem FECP — playbook §5).
# ---------------------------------------------------------------------------
DT02_ALIQUOTA = TabelaDecisao(
    nome="DT-02_aliquota",
    versao="1.0",
    regras=(
        Regra(
            numero=1,
            quando={"vigencia_encontrada": Igual(False)},
            entao={"status_aliquota": "periodo_sem_cobertura", "formula_efetiva": None},
        ),
        Regra(
            numero=2,
            quando={
                "vigencia_encontrada": Igual(True),
                "status_validacao": Diferente("validada"),
            },
            entao={"status_aliquota": "pendente_validacao_uf", "formula_efetiva": None},
        ),
        Regra(  # catch-all: vigência achada e validada → entrega a modal nominal
            numero=3,
            quando={"vigencia_encontrada": Qualquer()},
            entao={"status_aliquota": "ok", "formula_efetiva": "modal"},
        ),
    ),
)

# ---------------------------------------------------------------------------
# DT-03 — status_descricao (limiares T_ok/T_rev vêm da configuração — RF-24)
# Entrada: score (float 0..1). Mapeia o enum GIVA nenhuma|leve|forte:
#   ok = nenhuma · alerta_similaridade = leve · requer_revisao = forte (RN1).
# ---------------------------------------------------------------------------
DT03_STATUS_DESCRICAO = TabelaDecisao(
    nome="DT-03_status_descricao",
    versao="1.0",
    regras=(
        Regra(
            numero=1,
            quando={"score": MaiorIgualParametro("t_ok")},
            entao={"status_descricao": "ok"},
        ),
        Regra(
            numero=2,
            quando={"score": MaiorIgualParametro("t_rev")},
            entao={"status_descricao": "alerta_similaridade"},
        ),
        Regra(
            numero=3,
            quando={"score": Qualquer()},
            entao={"status_descricao": "requer_revisao"},
        ),
    ),
)

# ---------------------------------------------------------------------------
# DT-04 — status_linha (consolida falhas de normalização — RF-04)
# Entrada: motivo_falha (str | None)
# ---------------------------------------------------------------------------
DT04_STATUS_LINHA = TabelaDecisao(
    nome="DT-04_status_linha",
    versao="1.0",
    regras=(
        Regra(
            numero=1,
            quando={"motivo_falha": NaoNulo()},
            entao={"status_linha": "entrada_invalida"},
        ),
        Regra(
            numero=2,
            quando={"motivo_falha": Qualquer()},
            entao={"status_linha": "ok"},
        ),
    ),
)
