// Autenticação. login guarda o token no client antes de devolver a resposta,
// para que a próxima chamada já saia autenticada. Sem autocadastro na V1.
import { apiFetch, setToken } from './client'
import type { Role } from '../store/app'

export interface LoginResponse {
  token: string
  papel: Role
}

export async function login(email: string, senha: string): Promise<LoginResponse> {
  const resposta = await apiFetch<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, senha }),
  })
  setToken(resposta.token)
  return resposta
}
