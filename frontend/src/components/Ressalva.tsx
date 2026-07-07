import { AlertCircle } from 'lucide-react'
import { RESSALVAS } from '../data/ressalvas'
import styles from './Ressalva.module.css'

/**
 * As ressalvas obrigatórias, sempre visíveis (nunca em rodapé ignorável). `only`
 * mostra uma única ressalva (ex.: a da categoria perto da coluna de categoria);
 * sem `only`, mostra as duas. Usa a família Bronze — alerta semântico do
 * V-VORTEX.
 */
export function Ressalva({ only }: { only?: 0 | 1 }) {
  const itens = only === undefined ? RESSALVAS : [RESSALVAS[only]]
  return (
    <aside className={styles.box} role="note" aria-label="Ressalvas importantes">
      <AlertCircle size={16} strokeWidth={1.9} aria-hidden="true" className={styles.icone} />
      <ul className={styles.list}>
        {itens.map((t) => (
          <li key={t}>{t}</li>
        ))}
      </ul>
    </aside>
  )
}
