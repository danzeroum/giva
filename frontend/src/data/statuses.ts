// Fonte ÚNICA de statuses no front. Espelha o contrato do backend: statuses.json
// tem 9 status, cada um com rótulo textual + cor de farol (verde/amarelo/vermelho).
// Mapa 1:1 — nunca fundir estados. O StatusBadge garante que a cor NUNCA aparece
// sem o rótulo (legível em P&B; a cor apenas reforça).
import mapa from './statuses.json'

export type Farol = 'verde' | 'amarelo' | 'vermelho' | 'cinza'

export interface StatusInfo {
  label: string
  farol: Farol
}

export const STATUSES: Record<string, StatusInfo> = mapa as Record<string, StatusInfo>

export type StatusKey = keyof typeof mapa

// Trincas de cor do farol. Os valores saem dos TOKENS (tokens.css) via var() —
// assim o badge acompanha o tema (claro/escuro) automaticamente e não há hex de
// marca fora do design system.
//
// Mapeamento V-VORTEX pedido no brief:
//   verde   -> Verde #3FB68B (dot) · pares bg/tx AA por tema
//   amarelo -> Bronze #B98A4B (dot) · texto âmbar acessível por tema
//   vermelho-> Terracota #C0563D (dot) · pares bg/tx AA por tema
// Contrastes documentados em tokens.css (AA verificado nos dois temas).
export const FAROL: Record<Farol, { bar: string; bg: string; tx: string; dot: string }> = {
  verde: {
    bar: 'var(--farol-verde-bar)',
    bg: 'var(--farol-verde-bg)',
    tx: 'var(--farol-verde-tx)',
    dot: 'var(--farol-verde-dot)',
  },
  amarelo: {
    bar: 'var(--farol-amarelo-bar)',
    bg: 'var(--farol-amarelo-bg)',
    tx: 'var(--farol-amarelo-tx)',
    dot: 'var(--farol-amarelo-dot)',
  },
  vermelho: {
    bar: 'var(--farol-vermelho-bar)',
    bg: 'var(--farol-vermelho-bg)',
    tx: 'var(--farol-vermelho-tx)',
    dot: 'var(--farol-vermelho-dot)',
  },
  cinza: {
    bar: 'var(--farol-cinza-bar)',
    bg: 'var(--farol-cinza-bg)',
    tx: 'var(--farol-cinza-tx)',
    dot: 'var(--farol-cinza-dot)',
  },
}

export function statusInfo(key: string): StatusInfo {
  return STATUSES[key] ?? { label: key, farol: 'cinza' }
}

// Severidade do farol, declarada UMA vez. Espelha o backend: a coluna-farol da
// linha (planilha de saída) e o montador de saída usam a mesma ordem para
// escolher o "pior" status de uma linha. Ponto de deriva com o backend — por
// isso vive junto da fonte única de statuses.
export const SEVERIDADE: Record<Farol, number> = { cinza: 0, verde: 1, amarelo: 2, vermelho: 3 }

/** O status mais severo de uma lista (pior farol). Lista vazia -> 'ok'. */
export function piorStatus(keys: string[]): string {
  if (keys.length === 0) return 'ok'
  return keys.reduce((pior, k) =>
    SEVERIDADE[statusInfo(k).farol] > SEVERIDADE[statusInfo(pior).farol] ? k : pior,
  )
}

/** Severidade numérica de um status (atalho para ordenação/agrupamento). */
export function severidade(key: string): number {
  return SEVERIDADE[statusInfo(key).farol]
}
