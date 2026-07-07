// Bloco B — Operação. Rotas exigem papel operador/admin no backend. As telas do
// Bloco B são stubs simples nesta fase (ver screens/B*.tsx); estes tipos e
// funções ficam prontos para quando forem implementadas de fato.
import { apiFetch } from './client'

export type StatusValidacao =
  | 'validada' | 'confirmada_fonte_secundaria' | 'divergencia_entre_fontes' | 'pendente_validacao'

export interface Uf {
  uf: string
  status_validacao: StatusValidacao
  aliquota_modal: string
  fonte_compilada: string
}

export interface Carga {
  id: number
  fonte: string
  arquivo_bruto: string
  data_coleta: string
  promovido_em: string | null
  promovido_por: string | null
  status: 'staging' | 'aprovada'
}

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
}

export function listarUfs(): Promise<Uf[]> {
  return apiFetch<Uf[]>('/ufs')
}

export function listarCargas(): Promise<Carga[]> {
  return apiFetch<Carga[]>('/cargas')
}

export function listarContestacoesOperacao(status?: 'aberta' | 'resolvida'): Promise<ContestacaoOperacao[]> {
  const query = status ? `?status_filtro=${status}` : ''
  return apiFetch<ContestacaoOperacao[]>(`/contestacoes${query}`)
}
