import { DEMO_CONTESTACOES } from '../data/demo'
import { useApp } from '../store/app'
import styles from './stub.module.css'

// STUB (Bloco B — Operação). Fila de contestações abertas pelos analistas.
export function B5() {
  const demo = useApp((s) => s.demo)
  const contestacoes = demo ? DEMO_CONTESTACOES : []

  return (
    <div className={styles.wrap}>
      <h1 className={styles.h1}>Contestações</h1>
      <p className={styles.nota}>
        Tela de operação (stub). O encaminhamento das contestações (para exceção, validação de UF ou
        resposta) entra numa fase futura. Abaixo, somente leitura (demo).
      </p>
      <div className={styles.card}>
        {contestacoes.length === 0 ? (
          <div className={styles.vazio}>Nenhuma contestação.</div>
        ) : (
          <table className={styles.tabela}>
            <thead>
              <tr>
                <th>#</th>
                <th>Tipo</th>
                <th>Texto</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {contestacoes.map((c) => (
                <tr key={c.id}>
                  <td className="mono">{c.id}</td>
                  <td>{c.tipo}</td>
                  <td>{c.texto}</td>
                  <td>{c.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
