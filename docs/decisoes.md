# GIVA — Registro de decisões de produto

O GIVA nasce da convergência de duas linhagens que divergiam entre si:

- a **arquitetura de engenharia** do `enriquecedor-fiscal` (Python + FastAPI +
  PostgreSQL, motor de tabelas de decisão, vigências bitemporais, Alembic,
  worker, CI) — madura e de alta qualidade;
- a **especificação de produto** do pacote GIVA (PRD, escopo, playbook de
  alíquotas, doc das 18 categorias).

Onde as duas concordam (nunca inventar valor, proveniência por campo,
preservação das colunas originais, precisão decimal, vigências temporais,
processamento local), o GIVA herda o enriquecedor sem mudança. Onde divergiam,
estas são as decisões tomadas — cada uma com o motivo e o que muda no código.

---

## 1. Taxonomia de categorias — **18 categorias EFD** (docs GIVA)

**Decisão.** A taxonomia-alvo são as **18 categorias operacionais do EFD**
(doc `04-categorias-e-regras.md`): Material de manutenção, Peça de máquina,
Material elétrico, Material de limpeza, EPI, Material de escritório e
informática, Gás, Produto químico, Ferramentas, Combustível e lubrificante,
Material de construção, Serviço, Alimentação, Material de embalagem, Brindes,
Material de jardinagem, Material de laboratório e **`Indefinido`** (catch-all).

**Como funciona** (`src/giva/categoria/categorizador.py`, determinístico —
PRD §12.5): precedência (1) exceção por NCM exato → (2) regra por **faixa de
NCM** (prefixo mais específico vence) → (3) **palavra-chave** na descrição →
(4) `Indefinido` (separando `sem_match` de `ambiguo`). Cada linha recebe
`confianca_categorizacao` = **alta** (NCM e descrição concordam) · **média**
(só NCM ou só descrição) · **baixa** (conflito NCM×descrição / ambíguo — vai
para revisão). Categorias e regras são **configuráveis em banco e versionadas**
(tabelas `categoria`, `regra_ncm_categoria`, `regra_palavra_categoria`,
`regras_excecao`), nunca hard-coded.

**O que muda vs. enriquecedor.** Substitui a taxonomia setorial por faixa SH4
(17 categorias, cobertura total por invariante, só por NCM). Aqui a cobertura
total não é garantida por construção — `Indefinido` é o piso honesto quando não
há pista (RN4).

## 2. Fonte de NCM — **Classif/Siscomex** (enriquecedor)

**Decisão.** A base de NCM vem do **JSON público do Classif/Siscomex**
(máquina-legível), não da TIPI (PDF/DOCX). O histórico é modelado em
`ncm_historico` (bitemporal, `daterange` com exclusion constraint).

**Motivo.** O Classif é fonte oficial verificável e automatizável; a TIPI exige
um ETL de PDF que os próprios docs do GIVA marcam como "esforço não estimado".
Diverge do PRD GIVA (que dizia TIPI "DECIDIDO"), com justificativa técnica —
recomenda-se atualizar o PRD, não o código. A TIPI pode entrar como
validação cruzada numa fase futura.

## 3. Alíquota entregue — **modal nominal, sem FECP** (playbook)

**Decisão.** O valor entregue é a **alíquota modal nominal**, sem somar
FECP/FCP (playbook §5). A coluna de saída é `aliquota_icms_interna`.

**Como funciona.** A DT-02 (`src/giva/decisao/tabelas.py`) tem só a fórmula
`modal` — não existe o galho `modal_mais_fecp` do enriquecedor. Os campos de
FECP seguem na base `aliquota_icms_modal` como **referência/proveniência**, mas
não somam no número entregue.

**O que muda vs. enriquecedor.** Deixa de entregar `aliquota_efetiva`
(modal + FECP quando incidência ampla). Uma coluna a menos, número mais simples,
alinhado ao padrão do playbook.

## 4. Identidade visual — **Design System V-VORTEX** (docs GIVA)

**Decisão.** O frontend segue o **Design System V-VORTEX v2.3**, temas **light e
dark**: fundo Safira `#0A1A2E` / Papel `#F4F1EA`, Bronze `#B98A4B` semântico
(ação/alerta), verde `#3FB68B` sucesso, terracota `#C0563D` erro; tipografia
Newsreader (títulos), Archivo (interface), Fragment Mono (códigos/alíquotas).

**O que muda vs. enriquecedor.** Abandona a marca "Farol Fiscal" (navy/dourado,
IBM Plex, só light). Implementação na fase de frontend (ver roadmap).

## 5. Hospedagem — **VPS como forma inicial**

**Decisão.** Deploy inicial em **VPS** (Docker Compose: `db` → `migrate` →
`api` → `worker` → `frontend`), como no enriquecedor. **Importante:** isso não
afrouxa a LGPD — o caminho de enriquecimento continua 100% local por dentro
(RNF-01/02): nenhum dado de cliente sai para API externa; a única fonte externa
é a atualização da base pública (Classif), que não carrega dado de cliente. A
migração para "local no escritório" permanece possível sem mudança de
arquitetura.

---

## Herdado do enriquecedor sem mudança (regras de ouro)

- **RN4 — nunca inventar valor:** sem correspondência → status "requer revisão"
  fundamentado (`periodo_sem_cobertura`, `pendente_validacao_uf`,
  `codigo_inexistente`, `entrada_invalida`).
- **RN5 — colunas originais preservadas** intactas + proteção contra injeção de
  fórmula na saída.
- **Precisão fiscal com `Decimal`** (nunca float; `numeric(4,1)` no banco).
- **Vigências como `daterange` semiaberto** com `EXCLUDE USING gist` (não
  sobreposição garantida no banco).
- **Proveniência por registro** (`carga` com hash/data_coleta; proveniência por
  campo na saída).
- **Regras fiscais como dados** (tabelas de decisão versionadas — nenhum `if`
  fiscal fora de `decisao/`).
