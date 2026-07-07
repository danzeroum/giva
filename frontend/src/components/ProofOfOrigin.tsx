import { Fragment } from 'react'
import styles from './ProofOfOrigin.module.css'

function rotular(chave: string): string {
  const texto = chave.replace(/_/g, ' ')
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

interface ProofOfOriginProps {
  /** Um grupo por campo resolvido (descricao_oficial_ncm/aliquota_icms_interna/
   * categoria_macro), cada um com os atributos que o resolvedor registrou
   * (fonte, ato legal, vigência, coleta). */
  proveniencia: Record<string, Record<string, string>>
}

/**
 * Prova de origem a 1 clique. Sem nenhum grupo, mostra explicitamente que não há
 * proveniência — nunca um vazio ambíguo.
 */
export function ProofOfOrigin({ proveniencia }: ProofOfOriginProps) {
  const grupos = Object.entries(proveniencia)
  return (
    <div className={styles.box}>
      <div className={styles.titulo}>Prova de origem</div>
      {grupos.length === 0 ? (
        <p className={styles.vazio}>Sem valor enriquecido para esta linha.</p>
      ) : (
        grupos.map(([grupo, campos]) => (
          <div key={grupo} className={styles.grupo}>
            <div className={styles.grupoTitulo}>{rotular(grupo)}</div>
            <dl className={styles.dl}>
              {Object.entries(campos).map(([chave, valor]) => (
                <Fragment key={chave}>
                  <dt>{rotular(chave)}</dt>
                  <dd className="mono">{valor}</dd>
                </Fragment>
              ))}
            </dl>
          </div>
        ))
      )}
    </div>
  )
}
