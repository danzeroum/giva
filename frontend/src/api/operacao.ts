// Bloco B — Operação. Rotas exigem papel operador/admin no backend.
// DTOs espelham src/giva/api/schemas/operacao.py; os rótulos leigos ficam na
// camada de exibição (data/copy.ts) — aqui só o contrato técnico.
import { apiFetch } from './client'

export type StatusValidacao =
  | 'validada' | 'confirmada_fonte_secundaria' | 'divergencia_entre_fontes' | 'pendente_validacao'

// --- B2: alíquotas por estado -----------------------------------------------

export interface Uf {
  uf: string
  vigencia_inicio: string
  vigencia_fim: string | null
  aliquota_modal: string | number
  fecp_percentual: string | number | null
  fecp_incidencia: string
  status_validacao: StatusValidacao
  fonte_legal: string | null
  fonte_compilada: string
}

export function listarUfs(): Promise<Uf[]> {
  return apiFetch<Uf[]>('/ufs')
}

export function atualizarUf(uf: string, statusValidacao: StatusValidacao): Promise<Uf> {
  return apiFetch<Uf>(`/ufs/${uf}`, {
    method: 'PUT',
    body: JSON.stringify({ status_validacao: statusValidacao }),
  })
}

// --- B3: ajustes do sistema (parâmetros do motor) ---------------------------

export type ValorParametro = string | number | boolean | null

export interface Parametro {
  nome: string
  valor: ValorParametro
  atualizado_em: string
}

export interface HistoricoParametroItem {
  quando: string
  quem: string
  antes: Record<string, unknown> | null
  depois: Record<string, unknown> | null
}

export function listarParametros(): Promise<Parametro[]> {
  return apiFetch<Parametro[]>('/parametros')
}

export function atualizarParametro(nome: string, valor: ValorParametro): Promise<Parametro> {
  return apiFetch<Parametro>(`/parametros/${nome}`, {
    method: 'PUT',
    body: JSON.stringify({ valor }),
  })
}

export function historicoParametro(nome: string): Promise<HistoricoParametroItem[]> {
  return apiFetch<HistoricoParametroItem[]>(`/parametros/${nome}/historico`)
}

// --- B4: correções de categoria (exceções) ----------------------------------

export interface Excecao {
  ncm: string
  categoria: string
  justificativa: string
  versao: string
  origem_tipo: string | null
  origem_contestacao_id: number | null
  autor_id: number | null
  criado_em: string
}

export interface CriarExcecao {
  ncm: string
  categoria: string
  justificativa: string
  origem_tipo?: string | null
  origem_contestacao_id?: number | null
}

export function listarExcecoes(): Promise<Excecao[]> {
  return apiFetch<Excecao[]>('/excecoes')
}

export function criarExcecao(dados: CriarExcecao): Promise<Excecao> {
  return apiFetch<Excecao>('/excecoes', { method: 'POST', body: JSON.stringify(dados) })
}

// --- B5: contestações -------------------------------------------------------

export interface ContestacaoOperacao {
  id: number
  lote_id: number
  numero_linha: number
  autor_id: number
  tipo: string
  texto: string
  status: 'aberta' | 'resolvida'
  resolucao: string | null
  criado_em: string
  resolvido_em: string | null
}

export type DestinoContestacao = 'excecao' | 'validacao_uf' | 'resposta'

export interface EncaminharContestacao {
  destino: DestinoContestacao
  resolucao: string
  categoria?: string | null
  ncm?: string | null
}

export function listarContestacoesOperacao(status?: 'aberta' | 'resolvida'): Promise<ContestacaoOperacao[]> {
  const query = status ? `?status_filtro=${status}` : ''
  return apiFetch<ContestacaoOperacao[]>(`/contestacoes${query}`)
}

export function encaminharContestacao(
  id: number,
  dados: EncaminharContestacao,
): Promise<ContestacaoOperacao> {
  return apiFetch<ContestacaoOperacao>(`/contestacoes/${id}/encaminhar`, {
    method: 'PUT',
    body: JSON.stringify(dados),
  })
}

// --- B1: atualizações da base (cargas → diff → aprovar/descartar) ------------

export interface Carga {
  id: number
  fonte: string
  arquivo_bruto: string
  hash_arquivo: string
  data_coleta: string
  status: 'staging' | 'promovida' | 'rejeitada'
  criado_em: string
  promovido_em: string | null
  promovido_por: string | null
}

export interface DiffCarga {
  carga_id: number
  total_producao: number
  total_staging: number
  novos: number
  removidos: number
  alterados: number
  amostra_novos: string[]
  amostra_removidos: string[]
  amostra_alterados: string[]
}

export interface PromoverCarga {
  carga_id: number
  status: string
  promovidos: number
}

export function listarCargas(): Promise<Carga[]> {
  return apiFetch<Carga[]>('/cargas')
}

export function diffCarga(id: number): Promise<DiffCarga> {
  return apiFetch<DiffCarga>(`/cargas/${id}/diff`)
}

export function promoverCarga(id: number): Promise<PromoverCarga> {
  return apiFetch<PromoverCarga>(`/cargas/${id}/promover`, { method: 'POST' })
}

export function rejeitarCarga(id: number): Promise<PromoverCarga> {
  return apiFetch<PromoverCarga>(`/cargas/${id}/rejeitar`, { method: 'POST' })
}
