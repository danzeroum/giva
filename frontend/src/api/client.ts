// Cliente HTTP mínimo — wrapper fino sobre fetch, sem axios. Injeta o token JWT
// e traduz o corpo de erro `{erro, detalhe}` da API numa exceção tipada.
//
// Enquanto a API não existe, os screens usam os mocks de data/demo.ts no modo
// demo; este cliente só é exercido quando o modo demo está desligado.

const BASE_URL = import.meta.env.VITE_API_URL

let token: string | null = null

/** Guarda o token em memória (não localStorage — reduz superfície de XSS).
 * Chamado pelo store após login/logout. */
export function setToken(novoToken: string | null): void {
  token = novoToken
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly erro: string,
    detalhe: string,
  ) {
    super(detalhe)
    this.name = 'ApiError'
  }
}

async function corpoDeErro(res: Response): Promise<{ erro: string; detalhe: string }> {
  try {
    const corpo = await res.json()
    if (typeof corpo?.erro === 'string' && typeof corpo?.detalhe === 'string') return corpo
    // HTTPException direto na rota (401/403) cai no formato default `{detail}`.
    if (typeof corpo?.detail === 'string') return { erro: 'erro_http', detalhe: corpo.detail }
  } catch {
    // corpo não é JSON — cai no fallback abaixo
  }
  return { erro: 'erro_desconhecido', detalhe: `HTTP ${res.status}` }
}

export async function apiFetch<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  const headers = new Headers(opcoes.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  // FormData define seu próprio Content-Type (multipart, com boundary) — só
  // fixamos JSON quando o corpo não é FormData (upload de arquivo).
  if (opcoes.body && !(opcoes.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const res = await fetch(`${BASE_URL}${caminho}`, { ...opcoes, headers })
  if (!res.ok) {
    const { erro, detalhe } = await corpoDeErro(res)
    throw new ApiError(res.status, erro, detalhe)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

/** Para downloads autenticados (ex.: `.xlsx` de saída) — o token só existe em
 * memória, então um `<a href>` puro não o enviaria; buscamos como blob aqui. */
export async function apiFetchBlob(caminho: string): Promise<Blob> {
  const headers = new Headers()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const res = await fetch(`${BASE_URL}${caminho}`, { headers })
  if (!res.ok) {
    const { erro, detalhe } = await corpoDeErro(res)
    throw new ApiError(res.status, erro, detalhe)
  }
  return res.blob()
}
