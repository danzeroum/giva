// Lotes: upload, listagem, linhas, contestações e download da planilha de saída.
import { apiFetch, apiFetchBlob } from './client'

export interface Motivo {
  motivo: string
  linhas: number
}

export interface CategoriaDist {
  categoria: string
  linhas: number
}

export interface Resumo {
  linhas: number
  ok: number
  invalidas: number
  verde: number
  amarelo: number
  vermelho: number
  motivos: Motivo[]
  categorias: CategoriaDist[]
}

export interface Lote {
  id: number
  nome_arquivo: string | null
  status: 'recebido' | 'processando' | 'concluido' | 'erro'
  total_linhas: number | null
  linhas_processadas: number
  criado_por: string
  criado_em: string
  concluido_em: string | null
  resumo: Resumo | null
}

/** Uma linha enriquecida. `enriquecimento` carrega as colunas de saída do GIVA:
 * descricao_oficial_ncm, aliquota_icms_interna, categoria_macro e
 * confianca_categorizacao. `status` e `uf` são campos próprios. */
export interface LinhaLote {
  numero: number
  originais: Record<string, string>
  enriquecimento: Record<string, string>
  status: string
  uf: string | null
  proveniencia: Record<string, unknown>
}

export interface Contestacao {
  id: number
  lote_id: number
  numero_linha: number
  autor_id: number
  tipo: string
  texto: string
  status: 'aberta' | 'resolvida'
  criado_em: string
}

export function listarLotes(): Promise<Lote[]> {
  return apiFetch<Lote[]>('/lotes')
}

export function buscarLote(id: number): Promise<Lote> {
  return apiFetch<Lote>(`/lotes/${id}`)
}

export function enviarLote(arquivo: File): Promise<Lote> {
  const form = new FormData()
  form.append('arquivo', arquivo)
  return apiFetch<Lote>('/lotes', { method: 'POST', body: form })
}

export function listarLinhas(
  loteId: number,
  filtros: { status?: string; uf?: string } = {},
): Promise<LinhaLote[]> {
  const params = new URLSearchParams()
  if (filtros.status) params.set('status_filtro', filtros.status)
  if (filtros.uf) params.set('uf', filtros.uf)
  const query = params.toString()
  return apiFetch<LinhaLote[]>(`/lotes/${loteId}/linhas${query ? `?${query}` : ''}`)
}

export function contestar(
  loteId: number,
  numero: number,
  dados: { tipo: string; texto: string },
): Promise<Contestacao> {
  return apiFetch<Contestacao>(`/lotes/${loteId}/linhas/${numero}/contestacoes`, {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}

/** Baixa o `.xlsx` de saída e dispara o download (o token só existe em memória —
 * não dá pra usar um `<a href>` puro, ver client.ts). */
export async function baixarSaida(loteId: number): Promise<void> {
  const blob = await apiFetchBlob(`/lotes/${loteId}/saida.xlsx`)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `giva_lote_${loteId}.xlsx`
  a.click()
  URL.revokeObjectURL(url)
}
