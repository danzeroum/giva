# GIVA

**Sistema de validação e enriquecimento de planilhas NCM/ICMS.** Recebe uma
planilha fiscal (NCM · Período · Descrição · UF) e devolve **validada e
enriquecida** com:

1. a **descrição oficial do NCM** vigente naquele período (sinalizando
   divergência com a descrição informada);
2. a **alíquota interna de ICMS** (modal nominal) da UF no período;
3. uma **categoria macro sugestiva** (uma das 18 categorias operacionais do EFD);

cada campo com **proveniência auditável**. Posicionamento: **análise
retrospectiva de ICMS** (janela ~2016–2033) — não acompanha IBS/CBS.

> O núcleo do produto **não é a tela** — é a base de dados histórica própria
> (NCM + alíquotas de ICMS por UF, com rastreabilidade temporal) e o motor que a
> consulta. Roda **100% local** no caminho de enriquecimento (LGPD): nenhum dado
> de cliente vai para API externa.

Este repositório reaproveita a arquitetura provada do `enriquecedor-fiscal`
(Python + FastAPI + PostgreSQL, motor de tabelas de decisão, Alembic, worker de
fila, CI) e implementa as decisões do pacote de documentação do GIVA. As cinco
decisões que definem o produto estão registradas em
[`docs/decisoes.md`](docs/decisoes.md).

## Decisões que definem o GIVA (resumo)

| # | Tema | Decisão |
|---|------|---------|
| 1 | Taxonomia de categorias | **18 categorias EFD** (NCM → palavra-chave → `Indefinido`, com confiança) |
| 2 | Fonte de NCM | **Classif/Siscomex** (JSON público) + histórico bitemporal |
| 3 | Alíquota entregue | **Modal nominal, sem FECP** (playbook §5) |
| 4 | Identidade visual | **Design System V-VORTEX** (Safira/Bronze, light + dark) |
| 5 | Hospedagem | **VPS** como forma inicial (arquitetura permanece local por dentro) |

## Subir o ambiente (dev local)
```bash
docker compose up -d db
pip install -e ".[dev]"
export ALEMBIC_ALLOW_INI_URL=1   # dev local: permite a URL do alembic.ini
alembic upgrade head             # schema (0001) + dados de referência (0002)
pytest                           # verde antes de qualquer mudança
```
`DATABASE_URL` é obrigatória em produção/homologação/CI (12-factor —
`giva.config`). Sem ela e sem o opt-in `ALEMBIC_ALLOW_INI_URL=1`, o alembic/app
falham explicitamente.

## Rodar tudo via Docker (VPS ou local)
```bash
cp .env.example .env   # ajuste POSTGRES_PASSWORD e JWT_SECRET antes de produção
docker compose up -d --build
```
Sobe `db` → `migrate` (roda as migrations, sai) → `api` → `worker` → `frontend`.

## Onde está o quê
- `src/giva/decisao/` — interpretador de tabelas de decisão (ADR-04) + DT-01..04.
  **Nenhum `if` fiscal fora daqui.**
- `src/giva/normalizacao/` — normalização de NCM/período/UF (armadilhas de
  planilha real: zeros à **esquerda** do NCM, nunca à direita).
- `src/giva/ncm/` — resolução da descrição oficial por período (Classif).
- `src/giva/aliquota/` — alíquota interna modal por UF/período (sem FECP).
- `src/giva/categoria/` — categorizador das 18 categorias EFD (NCM + palavra-chave).
- `src/giva/similaridade/` — score de divergência de descrição (DT-03).
- `src/giva/saida/` — montador da planilha enriquecida (CSV/`.xlsx`) + disclaimer.
- `src/giva/pipeline/` — leitor, modelo da linha e a cadeia de etapas (C3).
- `migrations/` — schema (0001) e dados de referência (0002: 18 categorias +
  regras + 27 UFs).
- `docs/` — decisões, PRD adaptado e roadmap.

## Estado atual (scaffold inicial)
Motor de enriquecimento (normalização → NCM → alíquota → categoria →
similaridade → saída), tabelas de decisão, migrations e seed das 27 UFs estão
implementados e testáveis. **Próximas fases** (ver `docs/roadmap.md`): base
histórica de NCM e alíquotas (o caminho crítico), API HTTP + worker de fila,
frontend V-VORTEX.
