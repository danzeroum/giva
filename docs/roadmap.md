# GIVA — Roadmap de construção

Ordenado por dependência e valor. O **caminho crítico é a base de dados
histórica** (Fase 2) — motor e UI se constroem em dias; a base é semanas.

## Fase 0 — Fundação ✅ (este scaffold)
- Estrutura do repo, `pyproject`, Docker/Compose (VPS), CI, `.env.example`.
- Motor de tabelas de decisão (DT-01..04) + interpretador.
- Config 12-factor.

## Fase 1 — Motor de enriquecimento ✅ (este scaffold)
- Normalização de NCM/período/UF (armadilhas de planilha real).
- Resolução de NCM vigente (Classif) + status temporal.
- Alíquota interna modal por UF/período (sem FECP).
- Categorizador das 18 categorias EFD (NCM + palavra-chave + `Indefinido` +
  confiança).
- Similaridade de descrição (DT-03) e montador de saída (CSV/`.xlsx` + disclaimer).
- Migrations 0001 (schema) + 0002 (18 categorias, regras, 27 UFs modais 2026).

## Fase 2 — Base histórica (🔴 caminho crítico — o que o produto promete)
1. **NCM histórico bitemporal:** carregar `ncm_historico` e `ncm_correlacao`
   (revisão SH 2022 — Gecex 272/2021) a partir do export do Classif; ligar o
   resolvedor para responder a **descrição de época**, não só a vigente.
2. **Histórico decenal das alíquotas modais:** vigências por UF ao longo de
   ~10 anos (viradas 2023–2026), cada linha com fonte oficial → `validada`.
3. **Varredura oficial UF a UF** (playbook): promover `pendente_validacao` a
   `validada` com URL citável do próprio estado.
4. **Exceções por NCM** (bebidas, cesta básica, supérfluos) — camada 2.
5. **Conjunto-ouro (~50 linhas)** verificado contra fonte oficial como fixture
   de regressão; importar a planilha-teste + gabarito do pacote GIVA.

## Fase 3 — API HTTP + worker de fila ✅
- `src/giva/api/` (FastAPI, JWT, RBAC — ADR-07) e `src/giva/worker/` (ADR-03).
- Fluxo do analista verificado ponta a ponta: login → upload → processamento →
  download `.xlsx`. Bloco B (validação de UF, parâmetros, exceções, contestações)
  funcional. Migration 0004 (usuario/RBAC, contestação, progresso de lote).

## Fase 4 — Frontend V-VORTEX ✅
- Tokens light + dark (Safira/Papel/Bronze), tipografia Newsreader/Archivo/
  Fragment Mono (fallback de sistema; woff2 self-hosted entram depois).
- Fluxo do analista completo (upload → acompanhamento → revisão → prévia/download)
  com disclaimer da categoria; Bloco B como stubs marcados; modo demo.
- `npm ci` + eslint + tsc + vite build verdes; job de CI dedicado.

## Fase 5 — Operação da base (em andamento)
- ✅ **Ingestão real do Classif**: `python -m giva.rotinas.ingestao_classif`
  carrega `ncm_vigente` do snapshot oficial versionado (~10,5 mil NCMs), com
  proveniência (hash + data de coleta declarada pelo próprio documento). Full
  refresh do vigente numa transação. Substitui o seed de demonstração.
- ✅ **Proteção de injeção de fórmula na prévia do front** (A6) — paridade com
  o `MontadorSaida` do backend.
- ⬜ **Histórico decenal das alíquotas modais** por UF (viradas 2023–2026) com
  **validação oficial UF a UF** (playbook) — promover `pendente_validacao` a
  `validada` com URL citável. É o que falta para a cobertura de produção.
- ⬜ **NCM histórico/correlação** a partir do export "Alterações Históricas" do
  Classif (hoje só o seed de demonstração da migration 0003).
- ⬜ **`versao_base` por execução** (reprodutibilidade ponta a ponta — RN6).
- ⬜ **Agendador** (APScheduler): Classif semanal, modais mensal, com item de
  revisão humana antes de promover a produção.
