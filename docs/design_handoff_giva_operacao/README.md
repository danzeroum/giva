# Handoff: GIVA — Bloco B (Operação) + Consultas prontas + Ajuda

## Visão geral

Este pacote documenta o redesign completo da **área de Operação do GIVA** (repositório `danzeroum/giva`), prototipado e validado com foco em **usuários leigos vindos de planilha**. Cobre:

1. As 5 telas do Bloco B (hoje stubs em `frontend/src/screens/B*.tsx`) implementadas de verdade contra a API existente.
2. Um **módulo novo de consultas ao banco** ("Consultas prontas") com 6 consultas guiadas + SQL livre somente leitura — requer endpoints novos no backend.
3. Uma **camada de ajuda**: manual prático, tour guiado com auto-abertura na primeira visita, e tooltips explicativos em todos os controles.
4. Uma **revisão completa de linguagem**: todo jargão técnico foi substituído por texto de leigo (tabela de-para na seção "Copywriting").

## Sobre os arquivos de design

`GIVA Operação.dc.html` é uma **referência de design em HTML** — um protótipo funcional que mostra aparência e comportamento pretendidos. **Não é código de produção.** A tarefa é recriar estas telas no frontend existente do repo (**React 18 + TypeScript + Vite + CSS Modules + zustand + lucide-react**), seguindo os padrões já estabelecidos (`Sidebar.tsx`, `TopBar.tsx`, `StatusBadge.tsx`, `stub.module.css` etc.), e implementar os endpoints novos no backend **FastAPI + psycopg** seguindo o padrão de `src/giva/api/routers/operacao.py`.

## Fidelidade

**Alta (hifi).** O protótipo usa os tokens reais do Design System V-VORTEX v2.3 já presentes no repo (`frontend/src/styles/tokens.css`) — cores, raios, sombras e tipografia são os finais. Recrie a UI com precisão usando `var(--token)`; **nenhum hex de marca fora de tokens.css** (regra do repo). Os textos (copy) foram validados com usuário e devem ser usados literalmente.

---

## Princípio de UX que governa tudo

O usuário-alvo só usou planilha a vida toda. Regras aplicadas no protótipo e obrigatórias na implementação:

- **Zero jargão**: nunca exibir "staging", "diff", "promover", "carga", "commit", "SQL" (exceto na opção "Avançado (SQL)").
- **Rótulos dizem a consequência**: "Aprovar e aplicar", "Descartar", "Tem certeza? Confirmar" — não verbos técnicos.
- **Cor nunca sozinha**: todo selo de status tem dot + texto (padrão `StatusBadge` já existente).
- **Ponte com o Excel**: todo resultado tabular tem "Copiar p/ Excel" (TSV no clipboard).
- **Nada muda sem confirmação**, e tudo que muda aparece na trilha de auditoria com quem/quando.

---

## Telas

### 1. Shell (TopBar + Sidebar)

Mantém a estrutura existente do repo, com mudanças:

- **TopBar**: adicionar botão **"? Ajuda"** (fundo `--accent-soft`, borda `--accent-line`, radius 9px, 30px de altura) antes do toggle de tema, com dropdown: "Tour guiado (2 min)" e "Manual prático".
- **Sidebar** — renomear itens do Bloco B e adicionar grupos:
  - Grupo "Base & motor": Atualizações da base (badge = nº em staging) · Alíquotas por estado (badge = nº divergências) · Ajustes do sistema · Correções de categoria · Contestações (badge = nº abertas).
  - Grupo "Banco de dados": Consultas prontas.
  - Grupo "Ajuda": Manual prático · Tour guiado.
- Item ativo: fundo `--accent-soft`, peso 600. Badges: pill 17-18px, fundo `--accent`, texto `--accent-ink`.

### 2. B1 — Atualizações da base (`screens/B1.tsx`)

**Propósito**: revisar e aprovar/descartar cargas em staging (endpoints já existem: `GET /cargas`, `GET /cargas/{id}/diff`, `POST /cargas/{id}/promover`, `POST /cargas/{id}/rejeitar`).

- Card-tabela (`--card`, borda `--line`, radius 14px, sombra `--sh-card`): colunas Fonte · Arquivo (Fragment Mono 12px) · Coleta · Status · ações.
- Selo de status: amarelo "aguardando aprovação" (staging) / verde "aprovada · {promovido_por}".
- Botão **⋯** (28×28, radius 8) só em linhas staging → menu suspenso (radius 10, sombra `--sh-pop`, min-width 180px): "Ver o que muda" · "Aprovar e aplicar" (verde) · "Descartar" (vermelho).
- **Painel de diff expandido** (linha extra na tabela, fundo `--surface`, radius 10):
  - Título "O QUE MUDA SE VOCÊ APROVAR" (11px, uppercase, `--text-muted`).
  - Pills de contagem: `+N novos` (verde-bg/tx) · `N alterados` (amarelo) · `−N removidos` (vermelho).
  - Tabela de amostra: NCM (mono) · Mudança (`+ novo` verde / `~ alterado` amarelo / `− removido` vermelho, peso 600) · "Antes → depois".
  - Botões: "Aprovar e aplicar" (primário Bronze: fundo `--accent`, texto `--accent-ink`, radius 9) e "Descartar" (secundário: borda `--line`, fundo `--card`).
  - Nota ao lado: "Tudo é aplicado de uma vez e fica registrado — dá para saber depois quem aprovou e quando."
- **Confirmação em 2 passos**: o 1º clique em Aprovar abre o diff e troca o rótulo para "Tem certeza? Confirmar"; só o 2º clique chama a API.

### 3. B2 — Alíquotas por estado (`screens/B2.tsx`)

**Propósito**: conferir/validar a alíquota modal por UF (`GET /ufs`, `PUT /ufs/{uf}`).

- Subtítulo: "A alíquota de ICMS que o GIVA usa para cada estado. Clique no selo para marcar o que você já conferiu na fonte oficial."
- Tabela: UF (mono, 600) · Alíquota interna (mono) · Vigência ("desde 2024-01") · Validação (selo-botão) · Fonte.
- **O selo de status É o controle**: botão-pill com dot + rótulo + caret ▾; clique abre menu com as 4 opções, cada uma com seu dot colorido:
  - `validada` → verde "conferida na fonte oficial"
  - `confirmada_fonte_secundaria` → amarelo "conferida em fonte secundária"
  - `divergencia_entre_fontes` → vermelho "fontes não batem — conferir"
  - `pendente_validacao` → cinza "ainda não conferida"
- Selecionar opção → `PUT /ufs/{uf}` com o status_validacao do contrato (os rótulos leigos são só de exibição; **manter o enum do backend**).

### 4. B3 — Ajustes do sistema (`screens/B3.tsx`)

**Propósito**: editar parâmetros do motor (`GET/PUT /parametros`, `GET /parametros/{nome}/historico`).

- Título "Ajustes do sistema"; subtítulo "Controles de como o GIVA analisa as planilhas. Cada mudança fica registrada com quem alterou e quando."
- Um card por parâmetro com **três níveis de texto**:
  1. Rótulo humano (14px, 600) + nome técnico ao lado (Fragment Mono 10.5px, `--text-faint`);
  2. Descrição leiga (12.5px, `--text-soft`);
  3. Efeito prático (11.5px, `--text-muted`, borda esquerda 2px `--accent-line`, padding-left 8px).
- Copy exata dos 4 parâmetros (usar literalmente — está no protótipo): `t_ok` "Rigor da comparação de descrições", `t_rev` "Limite para exigir revisão humana", `categoria_versao_vigente` "Versão do mapa de categorias", `expurgo_lotes_meses` "Tempo de guarda dos arquivos (meses)".
- Input à direita (110px, mono, alinhado à direita). Botão "Salvar" (primário) **só aparece quando o valor mudou**.
- Botão "Histórico" expande a lista de alterações (quando · quem · antes → depois) vinda de `/parametros/{nome}/historico`.

### 5. B4 — Correções de categoria (`screens/B4.tsx`)

**Propósito**: exceções NCM→categoria (`GET/POST /excecoes`).

- Título "Correções de categoria"; subtítulo "Quando um código NCM cai na categoria errada, corrija aqui — a correção vale para todos os próximos processamentos. Versão em uso: v4 (jun/2026)".
- Botão primário "Nova correção" → painel inline (borda `--accent-line`): NCM (8 dígitos, mono) · Categoria (select com as 18 categorias EFD, buscar de `categoria` no banco) · Motivo (obrigatório) · "Salvar correção".
- Validações com mensagem em pill vermelho: "NCM precisa de 8 dígitos." / "Justificativa é obrigatória." (mapear para "Motivo é obrigatório.")
- Tabela: NCM (formatado 0000.00.00, mono) · Categoria (600) · Justificativa · Origem ("curadoria" | "contestação #N") · Criada em.

### 6. B5 — Contestações (`screens/B5.tsx`)

**Propósito**: fila de contestações (`GET /contestacoes`, `PUT /contestacoes/{id}/encaminhar`).

- Subtítulo: "Dúvidas e discordâncias que os analistas apontaram nas planilhas. Responda ou corrija a base direto daqui."
- Um card por contestação: #id (mono) · tipo (600) · "lote N · linha N · data" · texto · selo (amarelo "aberta" / verde "resolvida").
- Resolvidas mostram a resolução em faixa verde ("Resolução: …").
- Abertas: botão "Encaminhar ▾" → menu: "Corrigir a categoria" (destino `excecao`) · "Mandar conferir a alíquota do estado" (destino `validacao_uf`) · "Responder e resolver" (destino `resposta`).
- Escolha abre formulário inline: p/ exceção, campos NCM + Categoria; sempre campo "Resolução" (obrigatório) + botões "Resolver" / "Cancelar". Chama `PUT /contestacoes/{id}/encaminhar`.

### 7. Consultas prontas (tela nova — ex.: `screens/Consultas.tsx`)

**Propósito**: perguntas frequentes à base, com resultado tabular copiável. **Requer endpoints novos** (ver seção Backend).

- Layout: rail esquerdo 210px com a lista de consultas (mesmo estilo dos itens da sidebar; cada item tem rótulo + sub-rótulo 11px `--text-faint`) + área direita (card de parâmetros em cima, card de resultado embaixo).
- As 7 consultas (rótulo · sub · parâmetros):
  1. **Buscar um NCM** · "qual a descrição oficial" · código NCM (≥4 dígitos) OU termo da descrição; período opcional.
  2. **Alíquota de um estado** · "quanto é o ICMS e desde quando" · UF (select) + período AAAA-MM.
  3. **Por que caiu nessa categoria** · "regras que valem p/ um NCM" · NCM. Resultado ordenado por precedência: 1. exceção (NCM exato) → 2. faixa de NCM (prefixo mais longo vence) → 3. palavra-chave.
  4. **Linhas processadas** · "filtrar por situação e estado" · status (select com rótulos de statuses.json) + UF.
  5. **Quem mudou o quê** · "registro de alterações" · filtro livre (quem/ação/alvo).
  6. **Situação da base** · "o que está em dia ou pendente" · sem parâmetros; devolve cobertura/pendências por base (ncm_vigente, ncm_historico, aliquota_icms_modal, regras, cargas, contestações).
  7. **Avançado (SQL)** · "para quem conhece SQL" · textarea mono; **somente SELECT**, com whitelist de tabelas e LIMIT obrigatório (ver Backend).
- Card de resultado: tabela (células mono 11.5px, ellipsis, max-width 340px) + rodapé com **nota de proveniência** (ex.: "fonte: ncm_vigente · carga #4 · coleta 01/07/2026"), contagem "N linhas" e botão **"Copiar p/ Excel"** (gera TSV: header + linhas com `\t`/`\n` → `navigator.clipboard.writeText`; feedback "Copiado ✓" por 1,6s).
- Erros como texto vermelho amigável no card de resultado (ex.: "Nenhum NCM encontrado para X. Verifique zeros à esquerda — nunca à direita.").
- Botão "Executar" com tooltip "Roda a consulta e mostra o resultado como uma tabela — nada é alterado."

### 8. Manual prático (tela nova — ex.: `screens/Manual.tsx`)

- Intro fixa: "O GIVA em 30 segundos: os analistas enviam planilhas fiscais e o sistema devolve cada linha conferida e completada. O seu papel aqui é cuidar da base — aprovar atualizações, conferir alíquotas e corrigir categorias. Nada que você faz altera planilhas já processadas." + link "Faça o tour guiado (2 min)".
- 6 acordeões (um aberto por vez; header com título 600 + "▼ ver passos"/"▲ fechar"): Aprovar uma atualização da base · Conferir a alíquota de um estado · Corrigir a categoria de um produto · Responder uma contestação de analista · Consultar a base e levar para o Excel · O que significam as cores dos selos. **Os passos exatos estão no protótipo (constante `MANUAL`) — copiar literalmente.**

### 9. Tour guiado

- Card flutuante fixo (bottom-right 24px, 350px, borda `--accent-line`, sombra `--sh-pop`), **sem backdrop** — o usuário vê a tela real atrás.
- 8 passos; cada passo **navega para a tela correspondente** (b1→b2→b3→b4→b5→consultas→manual). Textos exatos na constante `TOUR` do protótipo.
- Header: "TOUR GUIADO" (uppercase Bronze) + "N de 8" + ✕. Botões: Anterior (a partir do 2º) · Próximo/Concluir (primário) · "Pular — não mostrar de novo".
- **Auto-abertura na primeira visita**: flag em `localStorage` (`giva-op-tour-visto`); concluir/fechar/pular grava a flag. Sugestão: por usuário logado, não só por navegador.

### 10. Tooltips (dicas de hover)

- Tooltip global único: div fixed, max-width 260px, fundo `--text`, texto `--bg`, radius 9px, padding 8/11, 12px, `pointer-events:none`.
- Padrão de implementação: atributo `data-dica` no elemento + handlers `onMouseEnter`/`onMouseLeave` compartilhados; posiciona abaixo do elemento (ou acima se não couber), clampado à viewport. Em React, extrair como hook `useDica()` ou componente `<ComDica texto="...">`.
- **Todo controle de ação tem dica**, sempre descrevendo a consequência em linguagem leiga. Textos exatos no protótipo (buscar por `data-dica`).

---

## Interações e comportamento

- **Menus suspensos**: um aberto por vez (estado global `menu`); clique em qualquer lugar fecha (listener no root); `stopPropagation` nos gatilhos. Radius 10, sombra `--sh-pop`, itens com hover `--surface-2`.
- **Tema claro/escuro**: ciclo sistema → claro → escuro no botão da TopBar (já existe no repo via `data-theme` + localStorage `giva-theme` — manter).
- **Animação de entrada de tela**: `fadeup 0.25s ease` (já existe em global.css). Respeitar `prefers-reduced-motion` (já existe).
- **Otimista vs. confirmado**: mutações (promover, PUT uf, PUT parametro, POST excecao, encaminhar) devem invalidar/refetch as queries afetadas (react-query, padrão do repo) e atualizar badges da sidebar.
- **Auditoria**: toda mutação já é auditada no backend; a consulta "Quem mudou o quê" e o "Histórico" de B3 leem dessa trilha.

## Estado

- Navegação por `screen` no store zustand (`store/app.ts`) — adicionar telas `consultas` e `manual` ao tipo `Screen`.
- Estado novo no store (ou local): `menu` aberto, `diffAberto`, confirmação de promoção, acordeão do manual, passo do tour, tooltip.
- Dados de servidor via react-query nos screens (padrão do repo); modo demo continua usando `data/demo.ts` (estender os mocks com os dados do protótipo).

## Backend — endpoints novos (FastAPI, `src/giva/api/routers/`)

Criar router `consultas.py` (RBAC operador/admin, padrão de `operacao.py`):

- `GET /consultas/ncm?q=&periodo=` — busca em `ncm_vigente` (prefixo de código ≥4 dígitos ou `ILIKE` na descrição); se período informado e histórico carregado, responder de `ncm_historico`. Incluir proveniência (carga_id, data_coleta).
- `GET /consultas/aliquota?uf=&periodo=` — vigência de `aliquota_icms_modal` que contém o período (`daterange @>`); devolve modal, vigência, status_validacao, fontes.
- `GET /consultas/regras?ncm=` — exceção exata (`regras_excecao`) + faixas que casam (`regra_ncm_categoria`, prefixo mais longo primeiro) + palavras (`regra_palavra_categoria`), na versão vigente, com campo de precedência.
- `GET /consultas/linhas?status=&uf=&lote_id=` — `lote_linha` join `lote`, filtros opcionais, paginado.
- `GET /consultas/auditoria?filtro=` — `auditoria` com `ILIKE` em quem/acao/alvo, DESC, paginado.
- `GET /consultas/saude` — contagens agregadas: nº códigos em `ncm_vigente` + carga de origem; cobertura de `ncm_historico`; UFs com vigência corrente e nº não-validadas; nº exceções na versão vigente; cargas por status; contestações por status.
- `POST /consultas/sql` — **somente leitura, defesa em profundidade**: (1) executar com um usuário Postgres read-only dedicado; (2) validar que o statement único começa com SELECT (rejeitar `;`, CTEs com DML, `pg_`/`information_schema`); (3) whitelist de tabelas: `ncm_vigente, ncm_historico, aliquota_icms_modal, carga, regras_excecao, regra_ncm_categoria, regra_palavra_categoria, categoria, parametro, auditoria, lote, lote_linha, contestacao`; (4) `LIMIT` forçado (ex. 500) + `statement_timeout` (ex. 5s); (5) auditar cada execução.

Todos os resultados tabulares devolvem `{cols: string[], rows: (string|number)[][], nota: string}` para render genérico + cópia TSV.

## Design tokens (fonte: `frontend/src/styles/tokens.css` — já no repo)

- Marca: Bronze `#B98A4B` (ação primária), hover `#A5763B`, texto sobre Bronze = Safira `#0A1A2E`; `--accent-soft` rgba(185,138,75,.16); sucesso `#3FB68B`; erro `#C0563D`.
- Claro: bg Papel `#F4F1EA`, surface `#EDEFF3`, surface-2 `#DED8CC`, sidebar `#E7E1D5`, texto `#0A1A2E`, linha `#D8D2C4`.
- Escuro: bg Safira `#0A1A2E`, surface `#142A44`, surface-2 `#1E3A56`, sidebar `#10233A`, texto `#F4F1EA`, linha `#24405C`.
- Farol (pares bg/tx AA por tema — ver tokens.css): verde/amarelo/vermelho/cinza; dots saturados constantes.
- Raios: botão 9px · card 14px · pill 20px · menu 10px. Sombras: `--sh-card`, `--sh-pop`.
- Tipografia: Newsreader (títulos, 24px/600 nos h1) · Archivo (interface, base 13–14px) · Fragment Mono (códigos, alíquotas, dados tabulares). Rótulos de coluna: 11px/700/uppercase/letter-spacing .06em.

## Copywriting — tabela de-para (obrigatória)

| Termo técnico | Termo na UI |
|---|---|
| Cargas e aprovações / staging | Atualizações da base / "aguardando aprovação" |
| Ver diff vs. produção | Ver o que muda |
| Promover à produção | Aprovar e aplicar (confirmação: "Tem certeza? Confirmar") |
| Rejeitar carga | Descartar |
| Validação por estado | Alíquotas por estado |
| validada / pendente_validacao / divergencia_entre_fontes / confirmada_fonte_secundaria | conferida na fonte oficial / ainda não conferida / fontes não batem — conferir / conferida em fonte secundária |
| Parâmetros do motor | Ajustes do sistema |
| Exceções de categoria / justificativa | Correções de categoria / Motivo |
| Consulta ao banco / SQL livre | Consultas prontas / Avançado (SQL) |
| Trilha de auditoria | Quem mudou o quê |

**Importante**: os rótulos leigos são camada de exibição; os enums/contratos do backend (`statuses.json`, `status_validacao` etc.) não mudam.

## Assets

Nenhum asset novo. Fontes: Newsreader, Archivo e Fragment Mono — o repo prevê self-hosted .woff2 (global.css tem os @font-face comentados); o protótipo usa Google Fonts só por conveniência. Ícones: continuar com lucide-react (o protótipo usa glifos de texto por minimalismo; ⋯ → `MoreHorizontal`, ▾ → `ChevronDown`, ✕ → `X`).

## Arquivos deste pacote

- `README.md` — este documento (autossuficiente).
- `GIVA Operação.dc.html` — protótipo de referência. Abra no navegador para ver todas as telas, o tour, o manual e os tooltips funcionando. As constantes `TOUR`, `MANUAL`, os textos `data-dica` e os dados demo estão no bloco de script e devem ser copiados literalmente.
