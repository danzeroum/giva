// Dados de DEMONSTRAÇÃO do GIVA. Usados enquanto a API não existe (modo demo,
// ligado por padrão) — a faixa <DemoBanner> deixa explícito na UI que os números
// são ilustrativos e não servem para análise fiscal. Tudo aqui já está no formato
// dos DTOs da API (ver src/api/lotes.ts e src/api/operacao.ts), para que os
// screens troquem `demo ? mock : apiCall()` sem remodelar nada.
import type { Lote, LinhaLote, Resumo } from '../api/lotes'
import type { Carga, ContestacaoOperacao, Uf } from '../api/operacao'
import { statusInfo, type StatusKey } from './statuses'

// -----------------------------------------------------------------------------
// Linhas (LinhaLote) — colunas de saída do GIVA:
//   originais (NCM, Período, Descrição, UF)  +  enriquecimento:
//     descricao_oficial_ncm · aliquota_icms_interna · categoria_macro ·
//     confianca_categorizacao  +  status
// -----------------------------------------------------------------------------
interface Prov {
  descricao_oficial_ncm?: Record<string, string>
  aliquota_icms_interna?: Record<string, string>
  categoria_macro?: Record<string, string>
}

function mk(
  numero: number,
  originais: { NCM: string; Período: string; Descrição: string; UF: string },
  enr: {
    descricao_oficial_ncm: string
    aliquota_icms_interna: string
    categoria_macro: string
    confianca_categorizacao: string
  },
  status: StatusKey,
  prov: Prov,
): LinhaLote {
  return {
    numero,
    originais,
    enriquecimento: {
      descricao_oficial_ncm: enr.descricao_oficial_ncm,
      aliquota_icms_interna: enr.aliquota_icms_interna,
      categoria_macro: enr.categoria_macro,
      confianca_categorizacao: enr.confianca_categorizacao,
    },
    status,
    uf: originais.UF || null,
    proveniencia: prov as Record<string, unknown>,
  }
}

const provSP = (ato: string) => ({
  descricao_oficial_ncm: { fonte: 'TEC/NCM (Classificação SH)', ato_legal: 'TIPI 2022', vigencia: 'vig. 2026', coleta: '01/07/2026' },
  aliquota_icms_interna: { fonte: 'RICMS/SP', ato_legal: ato, vigencia: 'vig. 2026', coleta: '01/07/2026' },
  categoria_macro: { mapa_versao: 'v4 (jun/2026)', origem: 'mapa NCM→categoria' },
})

export const DEMO_LINHAS: LinhaLote[] = [
  mk(1, { NCM: '6403.99.90', Período: '2026-05', Descrição: 'Botina de segurança em couro', UF: 'SP' },
    { descricao_oficial_ncm: 'Calçados com sola exterior de couro — outros', aliquota_icms_interna: '18%', categoria_macro: 'EPI', confianca_categorizacao: '0,96' },
    'ok', provSP('Decreto 45.490/2000, art. 52, I')),
  mk(2, { NCM: '8471.30.19', Período: '2026-05', Descrição: 'Notebook Dell Latitude', UF: 'SP' },
    { descricao_oficial_ncm: 'Máquinas p/ processamento de dados, portáteis, ≤10kg', aliquota_icms_interna: '18%', categoria_macro: 'TI / Equipamentos', confianca_categorizacao: '0,98' },
    'ok', provSP('Decreto 45.490/2000, art. 34')),
  mk(3, { NCM: '2710.19.21', Período: '2026-04', Descrição: 'Óleo diesel S-10 rodoviário', UF: 'MG' },
    { descricao_oficial_ncm: 'Óleos combustíveis (gasóleo) — enxofre ≤10mg/kg', aliquota_icms_interna: 'alíquota específica', categoria_macro: 'Combustíveis', confianca_categorizacao: '0,74' },
    'alerta_similaridade', {
      descricao_oficial_ncm: { fonte: 'TEC/NCM', ato_legal: 'TIPI 2022', vigencia: 'vig. 2026', coleta: '30/06/2026' },
      aliquota_icms_interna: { fonte: 'RICMS/MG', ato_legal: 'Decreto 48.589/2023, Anexo XII', vigencia: 'vig. 2026', coleta: '30/06/2026' },
      categoria_macro: { mapa_versao: 'v4 (jun/2026)', origem: 'similaridade 0,74 — conferir' },
    }),
  mk(4, { NCM: '3004.90.69', Período: '2026-05', Descrição: 'Dipirona sódica 500mg cx', UF: 'RJ' },
    { descricao_oficial_ncm: 'Medicamentos p/ venda a retalho — outros', aliquota_icms_interna: '20%', categoria_macro: 'Saúde / Medicamentos', confianca_categorizacao: '0,55' },
    'requer_revisao', {
      descricao_oficial_ncm: { fonte: 'TEC/NCM', ato_legal: 'TIPI 2022', vigencia: 'vig. 2026', coleta: '30/06/2026' },
      aliquota_icms_interna: { fonte: 'RICMS/RJ', ato_legal: 'Decreto 27.427/2000, Livro I', vigencia: 'vig. 2026', coleta: '30/06/2026' },
      categoria_macro: { mapa_versao: 'v4 (jun/2026)', origem: 'regra geral pode não refletir medicamento' },
    }),
  mk(5, { NCM: '7308.90.10', Período: '2026-05', Descrição: 'Estrutura metálica p/ galpão', UF: 'PE' },
    { descricao_oficial_ncm: 'Construções e partes, de ferro ou aço', aliquota_icms_interna: '—', categoria_macro: 'Materiais de construção', confianca_categorizacao: '0,88' },
    'pendente_validacao_uf', {
      descricao_oficial_ncm: { fonte: 'TEC/NCM', ato_legal: 'TIPI 2022', vigencia: 'vig. 2026', coleta: '30/06/2026' },
      categoria_macro: { mapa_versao: 'v4 (jun/2026)', origem: 'mapa NCM→categoria' },
    }),
  mk(6, { NCM: '9999.99.99', Período: '2026-05', Descrição: 'Item diverso sem código', UF: 'BA' },
    { descricao_oficial_ncm: '—', aliquota_icms_interna: '—', categoria_macro: '—', confianca_categorizacao: '—' },
    'codigo_inexistente', {}),
  mk(7, { NCM: '640399', Período: '2026-05', Descrição: 'Botina PVC cano curto', UF: 'SP' },
    { descricao_oficial_ncm: '—', aliquota_icms_interna: '—', categoria_macro: '—', confianca_categorizacao: '—' },
    'entrada_invalida', {}),
  mk(8, { NCM: '8517.62.59', Período: '2025-02', Descrição: 'Roteador Wi-Fi dual band', UF: 'RS' },
    { descricao_oficial_ncm: 'Aparelhos p/ transmissão/recepção de dados — outros', aliquota_icms_interna: '18%', categoria_macro: 'TI / Equipamentos', confianca_categorizacao: '0,93' },
    'descricao_vigente_periodo_nao_carregado', {
      descricao_oficial_ncm: { fonte: 'TEC/NCM (vigente)', ato_legal: 'TIPI 2022', vigencia: 'vig. atual', coleta: '30/06/2026' },
      aliquota_icms_interna: { fonte: 'RICMS/RS', ato_legal: 'Decreto 37.699/1997, Livro I', vigencia: 'vig. 2026', coleta: '30/06/2026' },
      categoria_macro: { mapa_versao: 'v4 (jun/2026)', origem: 'histórico 02/2025 não carregado' },
    }),
  mk(9, { NCM: '2836.20.10', Período: '2019-03', Descrição: 'Barrilha (carbonato de sódio)', UF: 'PR' },
    { descricao_oficial_ncm: '—', aliquota_icms_interna: '—', categoria_macro: 'Insumos químicos', confianca_categorizacao: '0,81' },
    'periodo_sem_cobertura', {
      categoria_macro: { mapa_versao: 'v4 (jun/2026)', origem: 'período 03/2019 fora da cobertura' },
    }),
  mk(10, { NCM: '8467.21.00', Período: '2026-05', Descrição: 'Furadeira elétrica 650W', UF: 'SP' },
    { descricao_oficial_ncm: 'Ferramentas eletromecânicas — furadeiras', aliquota_icms_interna: '18%', categoria_macro: 'Ferramentas', confianca_categorizacao: '0,95' },
    'ok', provSP('Decreto 45.490/2000, art. 34')),
  mk(11, { NCM: '4820.10.00', Período: '2026-05', Descrição: 'Caderno pautado capa dura', UF: 'SP' },
    { descricao_oficial_ncm: 'Cadernos, blocos de notas e artigos semelhantes', aliquota_icms_interna: '18%', categoria_macro: 'Material de escritório', confianca_categorizacao: '0,94' },
    'ok', provSP('Decreto 45.490/2000, art. 34')),
  mk(12, { NCM: '3926.20.00', Período: '2026-05', Descrição: 'Avental de plástico', UF: 'SP' },
    { descricao_oficial_ncm: 'Vestuário e acessórios de plástico', aliquota_icms_interna: '18%', categoria_macro: 'EPI', confianca_categorizacao: '0,79' },
    'codigo_alterado_pela_revisao_sh', {
      descricao_oficial_ncm: { fonte: 'Classificação SH', ato_legal: 'Revisão SH 2022 — reclassificado', vigencia: 'a partir de 01/2022', coleta: '01/07/2026' },
      aliquota_icms_interna: { fonte: 'RICMS/SP', ato_legal: 'Decreto 45.490/2000, art. 34', vigencia: 'vig. 2026', coleta: '01/07/2026' },
      categoria_macro: { mapa_versao: 'v4 (jun/2026)', origem: 'exceção EPI (contestação #158)' },
    }),
  mk(13, { NCM: '2207.10.90', Período: '2026-04', Descrição: 'Álcool etílico não desnaturado', UF: 'PI' },
    { descricao_oficial_ncm: 'Álcool etílico não desnaturado ≥80% vol — outros', aliquota_icms_interna: '—', categoria_macro: 'Insumos químicos', confianca_categorizacao: '0,84' },
    'pendente_validacao_uf', {
      descricao_oficial_ncm: { fonte: 'TEC/NCM', ato_legal: 'TIPI 2022', vigencia: 'vig. 2026', coleta: '30/06/2026' },
      categoria_macro: { mapa_versao: 'v4 (jun/2026)', origem: 'mapa NCM→categoria' },
    }),
  mk(14, { NCM: '8544.49.00', Período: '2026-05', Descrição: 'Cabo elétrico flexível 2,5mm²', UF: 'SP' },
    { descricao_oficial_ncm: 'Condutores elétricos p/ tensão ≤1000V — outros', aliquota_icms_interna: '18%', categoria_macro: 'Materiais elétricos', confianca_categorizacao: '0,91' },
    'ok', provSP('Decreto 45.490/2000, art. 34')),
]

export function demoLinhas(filtros: { status?: string; uf?: string } = {}): LinhaLote[] {
  return DEMO_LINHAS.filter(
    (l) =>
      (!filtros.status || l.status === filtros.status) &&
      (!filtros.uf || l.uf === filtros.uf),
  )
}

// -----------------------------------------------------------------------------
// Resumo agregado (ilustrativo). ok/verde/amarelo/vermelho + motivos + categorias.
// -----------------------------------------------------------------------------
const RESUMO_CONCLUIDO: Resumo = {
  linhas: 8420,
  ok: 5980,
  invalidas: 412,
  verde: 5980,
  amarelo: 1766,
  vermelho: 674,
  motivos: [
    { motivo: 'Alíquota geral pode não refletir produto específico', linhas: 1240 },
    { motivo: 'Descrição diverge da oficial (conferir similaridade)', linhas: 890 },
    { motivo: 'Estado pendente de validação', linhas: 520 },
    { motivo: 'Linhas não lidas (entrada inválida)', linhas: 412 },
  ],
  categorias: [
    { categoria: 'TI / Equipamentos', linhas: 2358 },
    { categoria: 'Materiais de construção', linhas: 1768 },
    { categoria: 'EPI', linhas: 1179 },
    { categoria: 'Materiais elétricos', linhas: 1010 },
    { categoria: 'Ferramentas', linhas: 758 },
    { categoria: 'Outros', linhas: 1347 },
  ],
}

// -----------------------------------------------------------------------------
// Lotes (histórico do analista).
// -----------------------------------------------------------------------------
export const DEMO_LOTES: Lote[] = [
  {
    id: 1, nome_arquivo: 'Compras_Q2_2026.xlsx', status: 'concluido',
    total_linhas: 8420, linhas_processadas: 8420, criado_por: 'Ana L.',
    criado_em: '2026-07-02T14:38:00', concluido_em: '2026-07-02T14:52:00', resumo: RESUMO_CONCLUIDO,
  },
  {
    id: 2, nome_arquivo: 'Notas_junho.csv', status: 'processando',
    total_linhas: 10000, linhas_processadas: 4200, criado_por: 'Ana L.',
    criado_em: '2026-07-03T09:10:00', concluido_em: null, resumo: null,
  },
  {
    id: 3, nome_arquivo: 'Materiais_obra_maio.xlsx', status: 'concluido',
    total_linhas: 3480, linhas_processadas: 3480, criado_por: 'Paulo R.',
    criado_em: '2026-06-28T11:02:00', concluido_em: '2026-06-28T11:09:00',
    resumo: {
      linhas: 3480, ok: 2227, invalidas: 121, verde: 2227, amarelo: 870, vermelho: 383,
      motivos: [
        { motivo: 'Descrição diverge da oficial (conferir similaridade)', linhas: 430 },
        { motivo: 'Estado pendente de validação', linhas: 260 },
        { motivo: 'Linhas não lidas (entrada inválida)', linhas: 121 },
      ],
      categorias: [
        { categoria: 'Materiais de construção', linhas: 1740 },
        { categoria: 'Ferramentas', linhas: 522 },
        { categoria: 'EPI', linhas: 418 },
        { categoria: 'Outros', linhas: 800 },
      ],
    },
  },
  {
    id: 4, nome_arquivo: 'Frota_abril.xlsx', status: 'erro',
    total_linhas: null, linhas_processadas: 0, criado_por: 'Ana L.',
    criado_em: '2026-06-15T16:20:00', concluido_em: null, resumo: null,
  },
  {
    id: 5, nome_arquivo: 'Insumos_TI_Q1.xlsx', status: 'concluido',
    total_linhas: 6210, linhas_processadas: 6210, criado_por: 'Ana L.',
    criado_em: '2026-03-30T10:00:00', concluido_em: '2026-03-30T10:11:00',
    resumo: {
      linhas: 6210, ok: 4968, invalidas: 186, verde: 4968, amarelo: 931, vermelho: 311,
      motivos: [
        { motivo: 'Alíquota geral pode não refletir produto específico', linhas: 540 },
        { motivo: 'Descrição diverge da oficial (conferir similaridade)', linhas: 391 },
        { motivo: 'Linhas não lidas (entrada inválida)', linhas: 186 },
      ],
      categorias: [
        { categoria: 'TI / Equipamentos', linhas: 3540 },
        { categoria: 'Materiais elétricos', linhas: 1120 },
        { categoria: 'Outros', linhas: 1550 },
      ],
    },
  },
]

export function demoLote(id: number): Lote | undefined {
  return DEMO_LOTES.find((l) => l.id === id)
}

// Versões das bases (Leia-me da prévia). No demo, marcadas como fictícias.
export const BASES_VERSAO: { nome: string; versao: string }[] = [
  { nome: 'NCM vigente (Classificação SH)', versao: 'demo' },
  { nome: 'Alíquotas ICMS internas por estado', versao: 'demo' },
  { nome: 'Mapa de categorias macro', versao: 'demo' },
]
export const PROCESSADO_EM = '02/07/2026 14:52'

// Legenda agrupada por farol (aba Leia-me da prévia).
export const LEGENDA: { farol: string; statuses: string[] }[] = [
  { farol: 'verde', statuses: [statusInfo('ok').label] },
  {
    farol: 'amarelo',
    statuses: [
      statusInfo('alerta_similaridade').label,
      statusInfo('codigo_alterado_pela_revisao_sh').label,
      statusInfo('descricao_vigente_periodo_nao_carregado').label,
      statusInfo('periodo_sem_cobertura').label,
      statusInfo('pendente_validacao_uf').label,
    ],
  },
  {
    farol: 'vermelho',
    statuses: [
      statusInfo('requer_revisao').label,
      statusInfo('entrada_invalida').label,
      statusInfo('codigo_inexistente').label,
    ],
  },
]

// -----------------------------------------------------------------------------
// Bloco B (operação) — mock mínimo para badges da sidebar e stubs de tela.
// -----------------------------------------------------------------------------
export const DEMO_UFS: Uf[] = [
  { uf: 'SP', status_validacao: 'validada', aliquota_modal: '18%', fonte_compilada: 'RICMS/SP' },
  { uf: 'RJ', status_validacao: 'validada', aliquota_modal: '20%', fonte_compilada: 'RICMS/RJ' },
  { uf: 'MG', status_validacao: 'validada', aliquota_modal: '18%', fonte_compilada: 'RICMS/MG' },
  { uf: 'PE', status_validacao: 'divergencia_entre_fontes', aliquota_modal: '18%', fonte_compilada: 'consolidado' },
  { uf: 'PI', status_validacao: 'divergencia_entre_fontes', aliquota_modal: '21%', fonte_compilada: 'consolidado' },
  { uf: 'RS', status_validacao: 'validada', aliquota_modal: '17%', fonte_compilada: 'RICMS/RS' },
  { uf: 'BA', status_validacao: 'confirmada_fonte_secundaria', aliquota_modal: '20,5%', fonte_compilada: 'secundária' },
  { uf: 'PR', status_validacao: 'pendente_validacao', aliquota_modal: '19,5%', fonte_compilada: 'pendente' },
]

export const DEMO_CARGAS: Carga[] = [
  { id: 1, fonte: 'Receita Federal / TIPI', arquivo_bruto: 'tipi_2026s27.csv', data_coleta: '01/07/2026', promovido_em: null, promovido_por: null, status: 'staging' },
  { id: 2, fonte: 'SEFAZ (consolidado)', arquivo_bruto: 'icms_hist_q2.csv', data_coleta: '30/06/2026', promovido_em: null, promovido_por: null, status: 'staging' },
  { id: 3, fonte: 'RICMS/SP (atualização)', arquivo_bruto: 'ricms_sp_2026.csv', data_coleta: '28/06/2026', promovido_em: '2026-06-29T09:00:00', promovido_por: 'M. Ferraz', status: 'aprovada' },
]

export const DEMO_CONTESTACOES: ContestacaoOperacao[] = [
  { id: 158, lote_id: 1, numero_linha: 4, autor_id: 2, tipo: 'validação de alíquota', texto: 'Dipirona em RJ tem tratamento específico; a alíquota geral de 20% pode não se aplicar.', status: 'aberta', resolucao: null, criado_em: '2026-07-02T15:00:00' },
  { id: 150, lote_id: 3, numero_linha: 88, autor_id: 2, tipo: 'exceção de categoria', texto: 'Luva nitrílica deveria ser EPI, não “Outros”.', status: 'resolvida', resolucao: 'Exceção criada — luva nitrílica → EPI.', criado_em: '2026-06-19T10:00:00' },
]
