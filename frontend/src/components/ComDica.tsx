// Dicas de hover (tooltips) do Bloco B. Padrão do handoff: o elemento carrega
// um atributo `data-dica` com o texto (sempre descrevendo a CONSEQUÊNCIA em
// linguagem leiga) e recebe os handlers compartilhados de `useDica()`.
//
// Uso:
//   const { dicaHandlers, tooltip } = useDica()
//   ...
//   <button data-dica="Roda a consulta — nada é alterado." {...dicaHandlers}>Executar</button>
//   ...
//   {tooltip}   // renderiza o balão único (position: fixed; a posição na árvore não importa)
import { type ReactElement, type SyntheticEvent, useCallback, useState } from 'react'
import styles from './ComDica.module.css'

interface Tip {
  texto: string
  x: number
  y: number
}

export interface Dica {
  dicaHandlers: {
    onMouseEnter: (e: SyntheticEvent<HTMLElement>) => void
    onMouseLeave: () => void
    onFocus: (e: SyntheticEvent<HTMLElement>) => void
    onBlur: () => void
  }
  tooltip: ReactElement | null
}

export function useDica(): Dica {
  const [tip, setTip] = useState<Tip | null>(null)

  const mostrar = useCallback((e: SyntheticEvent<HTMLElement>) => {
    const el = e.currentTarget
    const texto = el.getAttribute('data-dica')
    if (!texto) return
    const r = el.getBoundingClientRect()
    // Posiciona abaixo do elemento; sobe se não couber. Clampa à viewport.
    const x = Math.max(8, Math.min(r.left, window.innerWidth - 275))
    const y = r.bottom + 8 > window.innerHeight - 60 ? r.top - 52 : r.bottom + 8
    setTip({ texto, x, y })
  }, [])

  const esconder = useCallback(() => setTip(null), [])

  return {
    dicaHandlers: { onMouseEnter: mostrar, onMouseLeave: esconder, onFocus: mostrar, onBlur: esconder },
    tooltip: tip ? (
      <div className={styles.tip} style={{ left: tip.x, top: tip.y }} role="tooltip">
        {tip.texto}
      </div>
    ) : null,
  }
}
