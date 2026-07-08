// Consultas prontas (Bloco B — Banco de dados). Todo resultado usa o mesmo
// envelope genérico {cols, rows, nota} — o front renderiza qualquer consulta
// com o mesmo componente e copia TSV para o Excel sem conhecer o formato.
import { apiFetch } from './client'

export type Celula = string | number | boolean | null

export interface ConsultaResposta {
  cols: string[]
  rows: Celula[][]
  nota: string
}

function query(params: Record<string, string | number | undefined>): string {
  const sp = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') sp.set(k, String(v))
  }
  const s = sp.toString()
  return s ? `?${s}` : ''
}

export function consultarNcm(q: string, periodo?: string): Promise<ConsultaResposta> {
  return apiFetch<ConsultaResposta>(`/consultas/ncm${query({ q, periodo })}`)
}

export function consultarAliquota(uf: string, periodo?: string): Promise<ConsultaResposta> {
  return apiFetch<ConsultaResposta>(`/consultas/aliquota${query({ uf, periodo })}`)
}

export function consultarRegras(ncm: string): Promise<ConsultaResposta> {
  return apiFetch<ConsultaResposta>(`/consultas/regras${query({ ncm })}`)
}

export function consultarLinhas(
  filtros: { status?: string; uf?: string; lote_id?: number } = {},
): Promise<ConsultaResposta> {
  return apiFetch<ConsultaResposta>(`/consultas/linhas${query(filtros)}`)
}

export function consultarAuditoria(filtro?: string): Promise<ConsultaResposta> {
  return apiFetch<ConsultaResposta>(`/consultas/auditoria${query({ filtro })}`)
}

export function consultarSaude(): Promise<ConsultaResposta> {
  return apiFetch<ConsultaResposta>('/consultas/saude')
}

export function executarSql(sql: string): Promise<ConsultaResposta> {
  return apiFetch<ConsultaResposta>('/consultas/sql', {
    method: 'POST',
    body: JSON.stringify({ sql }),
  })
}
