import { DEMO_CARGAS } from '../data/demo'
import { useApp } from '../store/app'
import styles from './stub.module.css'

// STUB (Bloco B — Operação). Aprovação/diff de cargas ainda não implementados.
// Mostra, em somente leitura, as cargas registradas (demo).
export function B1() {
  const demo = useApp((s) => s.demo)
  const cargas = demo ? DEMO_CARGAS : []

  return (
    <div className={styles.wrap}>
      <h1 className={styles.h1}>Cargas e aprovações</h1>
      <p className={styles.nota}>
        Tela de operação (stub). Aprovação e comparação (diff) de novas cargas ainda não estão
        implementadas nesta fase. Abaixo, em somente leitura, as cargas registradas.
      </p>
      <div className={styles.card}>
        {cargas.length === 0 ? (
          <div className={styles.vazio}>Nenhuma carga registrada.</div>
        ) : (
          <table className={styles.tabela}>
            <thead>
              <tr>
                <th>Fonte</th>
                <th>Arquivo</th>
                <th>Coletado em</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {cargas.map((c) => (
                <tr key={c.id}>
                  <td>{c.fonte}</td>
                  <td className="mono">{c.arquivo_bruto}</td>
                  <td>{c.data_coleta}</td>
                  <td>{c.promovido_em ? `Aprovada por ${c.promovido_por}` : 'Em staging'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
