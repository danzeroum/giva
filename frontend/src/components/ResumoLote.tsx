import type { Resumo } from '../api/lotes'
import { FAROL } from '../data/statuses'
import { RESSALVA_CATEGORIA } from '../data/ressalvas'
import { Ressalva } from './Ressalva'
import styles from './ResumoLote.module.css'

function pct(parte: number, total: number): number {
  return total > 0 ? Math.round((parte / total) * 100) : 0
}

// Cards de totais + principais motivos + distribuição por categoria. Compartilhado
// entre o Resumo do lote (A4) e a aba Resumo da prévia (A6) — mesma fonte, nunca
// divergem.
export function ResumoLote({ resumo }: { resumo: Resumo }) {
  const cards = [
    { rotulo: 'Total de linhas', valor: resumo.linhas, pct: null as number | null, cor: 'var(--accent)' },
    { rotulo: 'ok', valor: resumo.verde, pct: pct(resumo.verde, resumo.linhas), cor: FAROL.verde.bar },
    { rotulo: 'conferir', valor: resumo.amarelo, pct: pct(resumo.amarelo, resumo.linhas), cor: FAROL.amarelo.bar },
    { rotulo: 'requer revisão', valor: resumo.vermelho, pct: pct(resumo.vermelho, resumo.linhas), cor: FAROL.vermelho.bar },
  ]

  return (
    <div className={styles.wrap}>
      <div className={styles.cards}>
        {cards.map((c) => (
          <div key={c.rotulo} className={styles.card} style={{ borderLeftColor: c.cor }}>
            <div className={styles.cardValor}>{c.valor.toLocaleString('pt-BR')}</div>
            <div className={styles.cardRotulo}>
              {c.rotulo}
              {c.pct !== null && <span className={styles.cardPct}> · {c.pct}%</span>}
            </div>
          </div>
        ))}
      </div>

      <div className={styles.duas}>
        <section className={styles.painel}>
          <h3 className={styles.h3}>Principais motivos de pendência</h3>
          {resumo.motivos.length === 0 ? (
            <p className={styles.semDados}>Nenhuma pendência neste lote.</p>
          ) : (
            <ul className={styles.motivos}>
              {resumo.motivos.map((m) => (
                <li key={m.motivo}>
                  <div className={styles.motivoTopo}>
                    <span>{m.motivo}</span>
                    <span className="mono">{m.linhas.toLocaleString('pt-BR')}</span>
                  </div>
                  <div className={styles.barra}>
                    <span style={{ width: `${pct(m.linhas, resumo.linhas)}%` }} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className={styles.painel}>
          <h3 className={styles.h3}>Distribuição por categoria</h3>
          {resumo.categorias.length === 0 ? (
            <p className={styles.semDados}>Sem categoria atribuída neste lote.</p>
          ) : (
            <ul className={styles.cats}>
              {resumo.categorias.map((c) => (
                <li key={c.categoria}>
                  <span className={styles.catNome}>{c.categoria}</span>
                  <span className={styles.catBarra}>
                    <span style={{ width: `${pct(c.linhas, resumo.linhas)}%` }} />
                  </span>
                  <span className={`${styles.catPct} mono`}>{pct(c.linhas, resumo.linhas)}%</span>
                </li>
              ))}
            </ul>
          )}
          <div className={styles.ressalvaCat}>
            <Ressalva only={RESSALVA_CATEGORIA} />
          </div>
        </section>
      </div>
    </div>
  )
}
