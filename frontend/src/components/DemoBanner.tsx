import styles from './DemoBanner.module.css'

/**
 * Com demo=true, os números na tela são fictícios — e para um analista fiscal um
 * número plausível JÁ É uma afirmação fiscal. Esta faixa é renderizada em todas
 * as telas enquanto o modo demo está ligado (padrão nesta fase sem backend).
 */
export function DemoBanner() {
  return (
    <div className={styles.banner} role="alert">
      <span className={styles.dot} aria-hidden="true" />
      <strong>Dados de demonstração</strong>
      <span>— valores ilustrativos, não usar para análise fiscal. A API real ainda não está conectada.</span>
    </div>
  )
}
