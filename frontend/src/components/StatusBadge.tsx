import { FAROL, statusInfo } from '../data/statuses'
import styles from './StatusBadge.module.css'

/**
 * A cor do farol NUNCA aparece sozinha. Este é o único jeito de pintar um status
 * — e ele sempre renderiza o dot quadrado E o rótulo textual. Legível em P&B (o
 * rótulo carrega a informação; a cor reforça). As cores vêm dos tokens, então o
 * badge acompanha o tema claro/escuro automaticamente.
 */
export function StatusBadge({ statusKey }: { statusKey: string }) {
  const info = statusInfo(statusKey)
  const c = FAROL[info.farol]
  return (
    <span className={styles.badge} style={{ background: c.bg, color: c.tx }}>
      <span className={styles.dot} style={{ background: c.dot }} aria-hidden="true" />
      {info.label}
    </span>
  )
}
