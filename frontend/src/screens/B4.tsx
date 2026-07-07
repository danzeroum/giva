import styles from './stub.module.css'

// STUB (Bloco B — Operação). Exceções de categoria (NCM → categoria macro).
export function B4() {
  return (
    <div className={styles.wrap}>
      <h1 className={styles.h1}>Exceções de categoria</h1>
      <p className={styles.nota}>
        Tela de operação (stub). O cadastro de exceções de categoria (com justificativa e origem)
        entra numa fase futura. Lembrete: a categoria macro é sugestão operacional, não substitui
        enquadramento fiscal.
      </p>
      <div className={styles.placeholder}>Em construção — sem exceções cadastráveis nesta fase.</div>
    </div>
  )
}
