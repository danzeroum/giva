import type { StatusValidacao } from '../api/operacao'
import { DEMO_UFS } from '../data/demo'
import { FAROL } from '../data/statuses'
import { useApp } from '../store/app'
import styles from './stub.module.css'

// Farol da validação de UF (mesma linguagem de cor do resto do produto).
const VALID_FAROL: Record<StatusValidacao, { label: string; farol: keyof typeof FAROL }> = {
  validada: { label: 'validada', farol: 'verde' },
  confirmada_fonte_secundaria: { label: 'fonte secundária', farol: 'amarelo' },
  divergencia_entre_fontes: { label: 'divergência entre fontes', farol: 'vermelho' },
  pendente_validacao: { label: 'pendente', farol: 'cinza' },
}

// STUB (Bloco B — Operação). Edição de validação por estado ainda não implementada.
export function B2() {
  const demo = useApp((s) => s.demo)
  const ufs = demo ? DEMO_UFS : []

  return (
    <div className={styles.wrap}>
      <h1 className={styles.h1}>Validação por estado</h1>
      <p className={styles.nota}>
        Tela de operação (stub). A edição do status de validação e da alíquota interna por UF entra
        numa fase futura. Abaixo, somente leitura (demo).
      </p>
      <div className={styles.card}>
        {ufs.length === 0 ? (
          <div className={styles.vazio}>Nenhum estado carregado.</div>
        ) : (
          <table className={styles.tabela}>
            <thead>
              <tr>
                <th>UF</th>
                <th>Alíquota interna</th>
                <th>Validação</th>
                <th>Fonte</th>
              </tr>
            </thead>
            <tbody>
              {ufs.map((u) => {
                const meta = VALID_FAROL[u.status_validacao]
                const c = FAROL[meta.farol]
                return (
                  <tr key={u.uf}>
                    <td className="mono">{u.uf}</td>
                    <td className="mono">{u.aliquota_modal}</td>
                    <td>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: c.tx, background: c.bg, borderRadius: 'var(--r-pill)', padding: '3px 9px', fontSize: 11.5, fontWeight: 600 }}>
                        <span style={{ width: 8, height: 8, borderRadius: 2, background: c.dot }} aria-hidden="true" />
                        {meta.label}
                      </span>
                    </td>
                    <td>{u.fonte_compilada}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
