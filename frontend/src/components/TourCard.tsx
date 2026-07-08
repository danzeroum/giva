import { X } from 'lucide-react'
import { TOUR } from '../data/ajuda'
import { useApp } from '../store/app'
import styles from './TourCard.module.css'

// Card flutuante do tour guiado (8 passos). Cada passo navega para a tela
// correspondente (a store cuida disso em tourNext/tourPrev). Sem backdrop.
export function TourCard() {
  const { tourStep, tourNext, tourPrev, tourClose } = useApp()
  if (tourStep === null) return null

  const passo = TOUR[tourStep]
  const temAnterior = tourStep > 0
  const ehUltimo = tourStep === TOUR.length - 1

  return (
    <div className={styles.card} role="dialog" aria-label="Tour guiado">
      <div className={styles.head}>
        <span className={styles.kicker}>Tour guiado</span>
        <span className={styles.contador}>{tourStep + 1} de {TOUR.length}</span>
        <button type="button" className={styles.fechar} onClick={tourClose} aria-label="Fechar tour">
          <X size={14} strokeWidth={2.2} />
        </button>
      </div>
      <div className={styles.titulo}>{passo.titulo}</div>
      <div className={styles.texto}>{passo.texto}</div>
      <div className={styles.acoes}>
        {temAnterior && (
          <button type="button" className={styles.anterior} onClick={tourPrev}>Anterior</button>
        )}
        <button type="button" className={styles.proximo} onClick={tourNext}>
          {ehUltimo ? 'Concluir' : 'Próximo'}
        </button>
        <button type="button" className={styles.pular} onClick={tourClose}>
          Pular — não mostrar de novo
        </button>
      </div>
    </div>
  )
}
