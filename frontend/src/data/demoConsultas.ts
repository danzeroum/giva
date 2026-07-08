// Executor de "Consultas prontas" no MODO DEMO — replica a lógica do protótipo
// (constantes NCM_TABELA/REGRAS/LINHAS/AUDITORIA + a função executar) para que a
// tela funcione ponta a ponta sem backend. No modo real, a tela chama a API
// (/consultas/*). Os datasets abaixo são de demonstração, sem valor fiscal.
import type { ConsultaResposta } from '../api/consultas'
import { validacaoInfo } from './copy'
import { DEMO_CARGAS, DEMO_CONTESTACOES, DEMO_EXCECOES, DEMO_PARAMETROS, DEMO_UFS } from './demo'
import { statusInfo } from './statuses'

export type ScriptConsulta =
  | 'ncm' | 'aliquota' | 'regras' | 'linhas' | 'auditoria' | 'saude' | 'sql'

export interface ParamsConsulta {
  ncm: string
  periodo: string
  uf: string
  status: string
  lUf: string
  alvo: string
  sql: string
}

const NCM_TABELA = [
  { codigo: '64039990', descricao: 'Calçados com sola exterior de couro — outros', inicio: '2022-04-01', ato: 'Gecex 272/2021' },
  { codigo: '84713019', descricao: 'Máquinas p/ processamento de dados, portáteis, ≤10kg — outras', inicio: '2022-04-01', ato: 'Gecex 272/2021' },
  { codigo: '27101921', descricao: 'Óleos combustíveis (gasóleo) — enxofre ≤10mg/kg', inicio: '2022-04-01', ato: 'Gecex 272/2021' },
  { codigo: '30049069', descricao: 'Medicamentos p/ venda a retalho — outros', inicio: '2022-04-01', ato: 'Gecex 272/2021' },
  { codigo: '73089010', descricao: 'Construções e partes, de ferro ou aço', inicio: '2022-04-01', ato: 'Gecex 272/2021' },
  { codigo: '85176259', descricao: 'Aparelhos p/ transmissão/recepção de dados — outros', inicio: '2022-04-01', ato: 'Gecex 272/2021' },
  { codigo: '28362010', descricao: 'Carbonato de sódio (barrilha)', inicio: '2017-01-01', ato: 'Camex 92/2016' },
  { codigo: '84672100', descricao: 'Ferramentas eletromecânicas — furadeiras', inicio: '2022-04-01', ato: 'Gecex 272/2021' },
  { codigo: '48201000', descricao: 'Cadernos, blocos de notas e artigos semelhantes', inicio: '2022-04-01', ato: 'Gecex 272/2021' },
  { codigo: '39262000', descricao: 'Vestuário e acessórios de plástico', inicio: '2022-04-01', ato: 'Gecex 272/2021' },
  { codigo: '85444900', descricao: 'Condutores elétricos p/ tensão ≤1000V — outros', inicio: '2022-04-01', ato: 'Gecex 272/2021' },
  { codigo: '22071090', descricao: 'Álcool etílico não desnaturado ≥80% vol — outros', inicio: '2022-04-01', ato: 'Gecex 272/2021' },
]

const REGRAS_NCM = [
  { prefixo: '3926', categoria: 'Material de embalagem' },
  { prefixo: '392620', categoria: 'EPI' },
  { prefixo: '8467', categoria: 'Ferramentas' },
  { prefixo: '8544', categoria: 'Material elétrico' },
  { prefixo: '2710', categoria: 'Combustível e lubrificante' },
  { prefixo: '7308', categoria: 'Material de construção' },
  { prefixo: '4820', categoria: 'Material de escritório e informática' },
  { prefixo: '2836', categoria: 'Produto químico' },
  { prefixo: '6403', categoria: 'EPI' },
]

const REGRAS_PALAVRA = [
  { palavra: 'luva', categoria: 'EPI' },
  { palavra: 'luva', categoria: 'Material de limpeza' },
  { palavra: 'botina', categoria: 'EPI' },
  { palavra: 'furadeira', categoria: 'Ferramentas' },
  { palavra: 'diesel', categoria: 'Combustível e lubrificante' },
  { palavra: 'caderno', categoria: 'Material de escritório e informática' },
]

const LINHAS = [
  { lote: 1, numero: 1, ncm: '6403.99.90', periodo: '2026-05', descricao: 'Botina de segurança em couro', uf: 'SP', status: 'ok', categoria: 'EPI', aliquota: '18%' },
  { lote: 1, numero: 3, ncm: '2710.19.21', periodo: '2026-04', descricao: 'Óleo diesel S-10 rodoviário', uf: 'MG', status: 'alerta_similaridade', categoria: 'Combustível e lubrificante', aliquota: 'específica' },
  { lote: 1, numero: 4, ncm: '3004.90.69', periodo: '2026-05', descricao: 'Dipirona sódica 500mg cx', uf: 'RJ', status: 'requer_revisao', categoria: 'Indefinido', aliquota: '20%' },
  { lote: 1, numero: 5, ncm: '7308.90.10', periodo: '2026-05', descricao: 'Estrutura metálica p/ galpão', uf: 'PE', status: 'pendente_validacao_uf', categoria: 'Material de construção', aliquota: '—' },
  { lote: 1, numero: 6, ncm: '9999.99.99', periodo: '2026-05', descricao: 'Item diverso sem código', uf: 'BA', status: 'codigo_inexistente', categoria: '—', aliquota: '—' },
  { lote: 1, numero: 7, ncm: '640399', periodo: '2026-05', descricao: 'Botina PVC cano curto', uf: 'SP', status: 'entrada_invalida', categoria: '—', aliquota: '—' },
  { lote: 3, numero: 9, ncm: '2836.20.10', periodo: '2019-03', descricao: 'Barrilha (carbonato de sódio)', uf: 'PR', status: 'periodo_sem_cobertura', categoria: 'Produto químico', aliquota: '—' },
  { lote: 3, numero: 12, ncm: '3926.20.00', periodo: '2026-05', descricao: 'Avental de plástico', uf: 'SP', status: 'codigo_alterado_pela_revisao_sh', categoria: 'EPI', aliquota: '18%' },
  { lote: 3, numero: 14, ncm: '8544.49.00', periodo: '2026-05', descricao: 'Cabo elétrico flexível 2,5mm²', uf: 'SP', status: 'ok', categoria: 'Material elétrico', aliquota: '18%' },
  { lote: 3, numero: 88, ncm: '4015.19.00', periodo: '2026-04', descricao: 'Luva nitrílica descartável', uf: 'SP', status: 'ok', categoria: 'EPI', aliquota: '18%' },
]

const AUDITORIA = [
  { quando: '05/07/2026 09:12', quem: 'm.ferraz', acao: 'uf_status_validacao_atualizado', alvo: 'aliquota_icms_modal:CE', mudanca: 'pendente_validacao → confirmada_fonte_secundaria' },
  { quando: '29/06/2026 09:00', quem: 'm.ferraz', acao: 'carga_promovida', alvo: 'carga:3', mudanca: 'staging → produção (1.204 registros)' },
  { quando: '19/06/2026 10:31', quem: 'm.ferraz', acao: 'excecao_categoria_criada', alvo: 'regras_excecao:40151900:v4', mudanca: 'Indefinido → EPI' },
  { quando: '19/06/2026 10:30', quem: 'm.ferraz', acao: 'contestacao_encaminhada', alvo: 'contestacao:150', mudanca: 'aberta → resolvida (exceção)' },
  { quando: '11/06/2026 15:04', quem: 'a.lima', acao: 'parametro_atualizado', alvo: 'parametro:t_ok', mudanca: '0.80 → 0.85' },
  { quando: '02/05/2026 11:40', quem: 'm.ferraz', acao: 'excecao_categoria_criada', alvo: 'regras_excecao:22071090:v4', mudanca: '(nova) → Produto químico' },
]

const soDigitos = (v: string) => (v || '').replace(/\D/g, '')
const fmtNcm = (c: string) => c.replace(/(\d{4})(\d{2})(\d{2})/, '$1.$2.$3')

/** Roda a consulta no modo demo. Devolve o envelope {cols, rows, nota}; lança
 * Error com mensagem de leigo em erros de entrada (mesma UX que a API real). */
export function executarConsultaDemo(script: ScriptConsulta, q: ParamsConsulta): ConsultaResposta {
  if (script === 'ncm') {
    const termo = (q.ncm || '').toLowerCase().trim()
    if (!termo) throw new Error('Informe um código NCM (≥4 dígitos) ou um termo da descrição.')
    const cod = soDigitos(q.ncm)
    const hits = NCM_TABELA.filter((n) =>
      (cod.length >= 4 && n.codigo.startsWith(cod)) ||
      (cod.length < 4 && n.descricao.toLowerCase().includes(termo)))
    return {
      cols: ['código', 'descrição oficial', 'vigente desde', 'ato legal'],
      rows: hits.map((n) => [fmtNcm(n.codigo), n.descricao, n.inicio, n.ato]),
      nota: 'fonte: ncm_vigente · carga #4 · coleta 01/07/2026' +
        (q.periodo ? ` · período ${q.periodo} respondido pela redação vigente` : ''),
    }
  }
  if (script === 'aliquota') {
    const u = DEMO_UFS.find((x) => x.uf === q.uf)
    if (!u) return { cols: [], rows: [], nota: 'UF não encontrada.' }
    return {
      cols: ['UF', 'período', 'alíquota modal', 'vigência', 'validação', 'fonte'],
      rows: [[u.uf, q.periodo || 'corrente', `${Number(u.aliquota_modal).toFixed(1).replace('.', ',')}%`,
        `desde ${u.vigencia_inicio.slice(0, 7)}`, validacaoInfo(u.status_validacao).label, u.fonte_compilada]],
      nota: 'fonte: aliquota_icms_modal · modal nominal, sem FECP (playbook §5)',
    }
  }
  if (script === 'regras') {
    const cod = soDigitos(q.ncm)
    if (cod.length < 4) throw new Error('Informe um NCM com pelo menos 4 dígitos.')
    const rows: (string | number)[][] = []
    const exc = DEMO_EXCECOES.find((e) => e.ncm === cod)
    if (exc) rows.push(['1. exceção (NCM exato)', fmtNcm(cod), exc.categoria, exc.justificativa])
    const faixas = REGRAS_NCM.filter((rg) => cod.startsWith(rg.prefixo)).sort((a, b) => b.prefixo.length - a.prefixo.length)
    faixas.forEach((f, i) => rows.push(['2. faixa de NCM' + (i === 0 ? ' (vence: mais específica)' : ''), `${f.prefixo}*`, f.categoria, 'regra_ncm_categoria v4']))
    REGRAS_PALAVRA.forEach((p) => rows.push(['3. palavra-chave', `“${p.palavra}”`, p.categoria, 'fallback pela descrição']))
    return {
      cols: ['precedência', 'gatilho', 'categoria', 'detalhe'],
      rows,
      nota: 'precedência do categorizador: exceção → faixa NCM (prefixo mais longo) → palavra-chave → Indefinido',
    }
  }
  if (script === 'linhas') {
    const hits = LINHAS.filter((l) =>
      (q.status === 'todos' || l.status === q.status) && (q.lUf === 'todos' || l.uf === q.lUf))
    return {
      cols: ['lote', 'linha', 'NCM', 'período', 'descrição', 'UF', 'status', 'categoria', 'alíquota'],
      rows: hits.map((l) => [l.lote, l.numero, l.ncm, l.periodo, l.descricao, l.uf, statusInfo(l.status).label, l.categoria, l.aliquota]),
      nota: 'fonte: lote_linha (join lote) · statuses do contrato DT-01..04',
    }
  }
  if (script === 'auditoria') {
    const f = (q.alvo || '').toLowerCase().trim()
    const hits = AUDITORIA.filter((a) => !f || a.quem.includes(f) || a.acao.includes(f) || a.alvo.toLowerCase().includes(f))
    return {
      cols: ['quando', 'quem', 'ação', 'alvo', 'antes → depois'],
      rows: hits.map((a) => [a.quando, a.quem, a.acao, a.alvo, a.mudanca]),
      nota: 'fonte: auditoria · imutável, ordenada do mais recente',
    }
  }
  if (script === 'saude') {
    const pend = DEMO_UFS.filter((u) => u.status_validacao !== 'validada').length
    const stag = DEMO_CARGAS.filter((c) => c.status === 'staging').length
    const abertas = DEMO_CONTESTACOES.filter((c) => c.status === 'aberta').length
    return {
      cols: ['base', 'cobertura', 'situação'],
      rows: [
        ['ncm_vigente', '10.542 códigos', 'carga #4 em staging aguardando revisão'],
        ['ncm_historico', 'revisão SH 2022 (seed)', 'export "Alterações Históricas" pendente (roadmap F5)'],
        ['aliquota_icms_modal', `${DEMO_UFS.length} UFs com vigência corrente`, `${pend} UFs não validadas`],
        ['regras de categoria', '18 categorias · v4', `${DEMO_EXCECOES.length} exceções ativas`],
        ['cargas', `${DEMO_CARGAS.length} registradas`, `${stag} em staging`],
        ['contestações', `${DEMO_CONTESTACOES.length} no total`, `${abertas} abertas`],
      ],
      nota: 'visão compilada de carga, ncm_vigente, aliquota_icms_modal, regras_excecao e contestacao',
    }
  }
  return executarSqlDemo(q.sql || '')
}

function executarSqlDemo(sql: string): ConsultaResposta {
  const s = sql.trim().replace(/;\s*$/, '')
  if (!/^select\s/i.test(s)) throw new Error('Somente leitura: apenas SELECT é permitido.')
  const m = s.match(/^select\s+(count\(\*\)|\*)\s+from\s+([a-z_]+)(?:\s+limit\s+(\d+))?$/i)
  if (!m) throw new Error('No modo demo o SQL suportado é: SELECT * | COUNT(*) FROM <tabela> [LIMIT n].')
  const tabelas: Record<string, Record<string, string | number>[]> = {
    ufs: DEMO_UFS.map((u) => ({ uf: u.uf, aliquota_modal: Number(u.aliquota_modal), vigencia: u.vigencia_inicio, status_validacao: u.status_validacao, fonte: u.fonte_compilada })),
    cargas: DEMO_CARGAS.map((c) => ({ id: c.id, fonte: c.fonte, arquivo_bruto: c.arquivo_bruto, data_coleta: c.data_coleta, status: c.status })),
    excecoes: DEMO_EXCECOES.map((e) => ({ ncm: e.ncm, categoria: e.categoria, justificativa: e.justificativa, versao: e.versao })),
    contestacoes: DEMO_CONTESTACOES.map((c) => ({ id: c.id, lote_id: c.lote_id, numero_linha: c.numero_linha, tipo: c.tipo, status: c.status })),
    parametros: DEMO_PARAMETROS.map((p) => ({ nome: p.nome, valor: String(p.valor) })),
    auditoria: AUDITORIA.map((a) => ({ quando: a.quando, quem: a.quem, acao: a.acao, alvo: a.alvo })),
    ncm_vigente: NCM_TABELA.map((n) => ({ codigo: n.codigo, descricao: n.descricao, data_inicio: n.inicio, ato: n.ato })),
    lote_linha: LINHAS.map((l) => ({ lote_id: l.lote, numero: l.numero, ncm: l.ncm, periodo: l.periodo, uf: l.uf, status: l.status, categoria: l.categoria })),
  }
  const nome = m[2].toLowerCase()
  const dados = tabelas[nome]
  if (!dados) throw new Error(`Tabela “${nome}” não existe. Disponíveis: ${Object.keys(tabelas).join(' · ')}`)
  if (/^count/i.test(m[1])) return { cols: ['count'], rows: [[dados.length]], nota: `${nome} · ${dados.length} registros` }
  const lim = m[3] ? parseInt(m[3], 10) : 50
  const slice = dados.slice(0, lim)
  const cols = slice.length ? Object.keys(slice[0]) : []
  return {
    cols,
    rows: slice.map((d) => cols.map((c) => String(d[c]))),
    nota: nome + (dados.length > lim ? ` · LIMIT ${lim} de ${dados.length}` : ''),
  }
}

// Metadados das 7 consultas (rótulo + sub-rótulo) — rail esquerdo.
export const CONSULTAS_META: { key: ScriptConsulta; label: string; sub: string }[] = [
  { key: 'ncm', label: 'Buscar um NCM', sub: 'qual a descrição oficial' },
  { key: 'aliquota', label: 'Alíquota de um estado', sub: 'quanto é o ICMS e desde quando' },
  { key: 'regras', label: 'Por que caiu nessa categoria', sub: 'regras que valem p/ um NCM' },
  { key: 'linhas', label: 'Linhas processadas', sub: 'filtrar por situação e estado' },
  { key: 'auditoria', label: 'Quem mudou o quê', sub: 'registro de alterações' },
  { key: 'saude', label: 'Situação da base', sub: 'o que está em dia ou pendente' },
  { key: 'sql', label: 'Avançado (SQL)', sub: 'para quem conhece SQL' },
]
