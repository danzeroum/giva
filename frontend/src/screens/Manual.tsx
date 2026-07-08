import { useState } from 'react'
import { MANUAL } from '../data/ajuda'
import { useApp } from '../store/app'
import styles from './Manual.module.css'

// Manual prático — 6 acordeões (um aberto por vez). Passos copiados literalmente
// da constante MANUAL do protótipo.
export function Manual() {
  const startTour = useApp((s) => s.startTour)
  const [aberto, setAberto] = useState<string | null>('aprovar')

  return (
    <div className={styles.wrap}>
      <h1 className={styles.h1}>Manual prático</h1>
      <p className={styles.intro}>
        O GIVA em 30 segundos: os analistas enviam planilhas fiscais e o sistema devolve cada linha
        conferida e completada. O seu papel aqui é cuidar da base — aprovar atualizações, conferir
        alíquotas e corrigir categorias. Nada que você faz altera planilhas já processadas.
      </p>
      <p className={styles.introLink}>
        Prefere ver na prática?{' '}
        <a
          role="button"
          tabIndex={0}
          onClick={startTour}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && startTour()}
        >
          Faça o tour guiado (2 min)
        </a>
        .
      </p>
      <div className={styles.lista}>
        {MANUAL.map((m) => {
          const isAberto = aberto === m.key
          return (
            <div key={m.key} className={styles.item}>
              <button
                type="button"
                className={styles.header}
                aria-expanded={isAberto}
                onClick={() => setAberto(isAberto ? null : m.key)}
              >
                <span className={styles.titulo}>{m.titulo}</span>
                <span className={styles.seta}>{isAberto ? '▲ fechar' : '▼ ver passos'}</span>
              </button>
              {isAberto && (
                <ol className={styles.passos}>
                  {m.passos.map((passo, i) => (
                    <li key={i}>{passo}</li>
                  ))}
                </ol>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
