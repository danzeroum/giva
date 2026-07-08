// Camada de tradução (de-para) — Bloco B Operação.
//
// REGRA DO HANDOFF (seção "Copywriting — tabela de-para"): os rótulos leigos são
// APENAS camada de exibição. Os enums/contratos do backend (statuses.json,
// status_validacao, destino de contestação etc.) NÃO mudam — este módulo traduz
// o enum técnico para o texto que o usuário lê, e nada mais.
//
// Tabela de-para (fonte: README do handoff):
//   Termo técnico                              | Termo na UI
//   -------------------------------------------|-------------------------------------
//   Cargas e aprovações / staging              | Atualizações da base / "aguardando aprovação"
//   Ver diff vs. produção                      | Ver o que muda
//   Promover à produção                        | Aprovar e aplicar ("Tem certeza? Confirmar")
//   Rejeitar carga                             | Descartar
//   Validação por estado                       | Alíquotas por estado
//   validada                                   | conferida na fonte oficial
//   confirmada_fonte_secundaria                | conferida em fonte secundária
//   divergencia_entre_fontes                   | fontes não batem — conferir
//   pendente_validacao                         | ainda não conferida
//   Parâmetros do motor                        | Ajustes do sistema
//   Exceções de categoria / justificativa      | Correções de categoria / Motivo
//   Consulta ao banco / SQL livre              | Consultas prontas / Avançado (SQL)
//   Trilha de auditoria                        | Quem mudou o quê
import type { Farol } from './statuses'

export interface ValidacaoInfo {
  label: string
  farol: Farol
}

/** status_validacao (enum do backend) → rótulo leigo + cor de farol. Exibição
 * pura: o `PUT /ufs/{uf}` continua recebendo/gravando a chave técnica. */
export const VALIDACAO: Record<string, ValidacaoInfo> = {
  validada: { label: 'conferida na fonte oficial', farol: 'verde' },
  confirmada_fonte_secundaria: { label: 'conferida em fonte secundária', farol: 'amarelo' },
  divergencia_entre_fontes: { label: 'fontes não batem — conferir', farol: 'vermelho' },
  pendente_validacao: { label: 'ainda não conferida', farol: 'cinza' },
}

/** Ordem canônica das opções no menu do selo-botão (B2). */
export const VALIDACAO_OPCOES = [
  'validada',
  'confirmada_fonte_secundaria',
  'divergencia_entre_fontes',
  'pendente_validacao',
] as const

export function validacaoInfo(key: string): ValidacaoInfo {
  return VALIDACAO[key] ?? { label: key, farol: 'cinza' }
}
