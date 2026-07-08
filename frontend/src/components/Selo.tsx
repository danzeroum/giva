import type { ReactNode } from 'react'
import { FAROL, type Farol } from '../data/statuses'
import styles from './Selo.module.css'

// Selo de status genérico: dot quadrado + rótulo, cores do farol via tokens.
// A COR NUNCA VEM SOZINHA (o rótulo carrega a informação; a cor reforça). Aceita
// caret ▾ e virar botão (B2, onde o próprio selo é o controle de validação).
interface SeloProps {
  farol: Farol
  label: string
  caret?: boolean
  onClick?: (e: React.MouseEvent) => void
  dica?: string
  dicaHandlers?: Record<string, unknown>
  children?: ReactNode
}

export function Selo({ farol, label, caret, onClick, dica, dicaHandlers }: SeloProps) {
  const c = FAROL[farol]
  const estilo = { background: c.bg, color: c.tx }
  const conteudo = (
    <>
      <span className={styles.dot} style={{ background: c.dot }} aria-hidden="true" />
      {label}
      {caret ? <span className={styles.caret} aria-hidden="true">▾</span> : null}
    </>
  )
  if (onClick) {
    return (
      <button
        type="button"
        className={styles.seloBtn}
        style={estilo}
        onClick={onClick}
        data-dica={dica}
        {...dicaHandlers}
      >
        {conteudo}
      </button>
    )
  }
  return (
    <span className={styles.selo} style={estilo}>
      {conteudo}
    </span>
  )
}
