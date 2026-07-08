import styles from './DemoBanner.module.css'

/**
 * Com demo=true, os números na tela são fictícios — e para um analista fiscal um
 * número plausível JÁ É uma afirmação fiscal. Esta faixa é renderizada em todas
 * as telas enquanto o modo demo está ligado (opt-in via VITE_DEMO_MODE; em
 * produção, com a API conectada, fica desligado).
 */
export function DemoBanner() {
  return (
    <div className={styles.banner} role="alert">
      <span className={styles.dot} aria-hidden="true" />
      <strong>Dados de demonstração</strong>
      <span>— valores ilustrativos, não usar para análise fiscal. Desligue o modo de demonstração para usar a API real.</span>
    </div>
  )
}
