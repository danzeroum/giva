import styles from './stub.module.css'

// STUB (Bloco B — Operação). Parâmetros do motor de enriquecimento.
export function B3() {
  return (
    <div className={styles.wrap}>
      <h1 className={styles.h1}>Parâmetros do motor</h1>
      <p className={styles.nota}>
        Tela de operação (stub). Ajuste de limiares (similaridade, expurgo, versão do mapa de
        categorias) e histórico de alterações entram numa fase futura.
      </p>
      <div className={styles.placeholder}>Em construção — sem parâmetros editáveis nesta fase.</div>
    </div>
  )
}
