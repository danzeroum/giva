import { HelpCircle, LogOut, Monitor, Moon, Search, Sun } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { type Role, type Theme, useApp } from '../store/app'
import { useDica } from './ComDica'
import styles from './TopBar.module.css'

const PAPEL_LABEL: Record<Role, string> = {
  analista: 'Analista fiscal',
  operador: 'Operação',
  admin: 'Administrador',
}

const TEMA_META: Record<Theme, { icon: typeof Sun; label: string; proximo: string }> = {
  system: { icon: Monitor, label: 'Tema do sistema', proximo: 'claro' },
  light: { icon: Sun, label: 'Tema claro', proximo: 'escuro' },
  dark: { icon: Moon, label: 'Tema escuro', proximo: 'sistema' },
}

export function TopBar() {
  const { role, demo, theme, toggleDemo, cycleTheme, logout, go, startTour } = useApp()
  const { dicaHandlers, tooltip } = useDica()
  const [ajudaAberto, setAjudaAberto] = useState(false)
  const ajudaRef = useRef<HTMLDivElement>(null)
  const iniciais = role === 'operador' ? 'OP' : role === 'admin' ? 'AD' : 'AF'
  const tema = TEMA_META[theme]
  const TemaIcon = tema.icon
  const mostraAjuda = role === 'operador' || role === 'admin'

  // Um menu aberto por vez; clique fora fecha.
  useEffect(() => {
    if (!ajudaAberto) return
    const fechar = (e: MouseEvent) => {
      if (ajudaRef.current && !ajudaRef.current.contains(e.target as Node)) setAjudaAberto(false)
    }
    document.addEventListener('click', fechar)
    return () => document.removeEventListener('click', fechar)
  }, [ajudaAberto])

  return (
    <header className={styles.bar}>
      <div className={styles.brand}>
        <span className={styles.mark} aria-hidden="true">
          <span className={styles.markDot} />
        </span>
        <span className={styles.wordmark}>GIVA</span>
      </div>

      <label className={styles.search}>
        <Search size={16} strokeWidth={1.9} aria-hidden="true" />
        <input type="search" placeholder="Buscar (em breve)" disabled aria-label="Busca global (indisponível na V1)" />
      </label>

      <div className={styles.right}>
        {mostraAjuda && (
          <div className={styles.ajudaWrap} ref={ajudaRef}>
            <button
              type="button"
              className={styles.ajuda}
              aria-haspopup="menu"
              aria-expanded={ajudaAberto}
              data-dica="Tour guiado pelas telas ou manual passo a passo."
              {...dicaHandlers}
              onClick={(e) => {
                e.stopPropagation()
                setAjudaAberto((v) => !v)
              }}
            >
              <HelpCircle size={15} strokeWidth={2} aria-hidden="true" /> Ajuda
            </button>
            {ajudaAberto && (
              <div className={styles.ajudaMenu} role="menu">
                <button
                  type="button"
                  className={styles.ajudaItem}
                  role="menuitem"
                  onClick={() => {
                    setAjudaAberto(false)
                    startTour()
                  }}
                >
                  Tour guiado (2 min)
                </button>
                <button
                  type="button"
                  className={styles.ajudaItem}
                  role="menuitem"
                  onClick={() => {
                    setAjudaAberto(false)
                    go('manual')
                  }}
                >
                  Manual prático
                </button>
              </div>
            )}
          </div>
        )}

        <button
          type="button"
          className={styles.tema}
          onClick={cycleTheme}
          aria-label={`${tema.label}. Alternar para tema ${tema.proximo}.`}
          title={`${tema.label} — clique para ${tema.proximo}`}
        >
          <TemaIcon size={16} strokeWidth={1.9} aria-hidden="true" />
        </button>

        <button
          type="button"
          className={`${styles.toggle} ${demo ? styles.toggleOn : ''}`}
          role="switch"
          aria-checked={demo}
          onClick={toggleDemo}
        >
          <span className={styles.knob} />
          <span className={styles.toggleLabel}>Dados de demonstração</span>
        </button>

        <div className={styles.user}>
          <div className={styles.userText}>
            <strong>{PAPEL_LABEL[role]}</strong>
            <span>{demo ? 'sessão de demonstração' : 'sessão ativa'}</span>
          </div>
          <span className={styles.avatar} aria-hidden="true">{iniciais}</span>
        </div>

        <button type="button" className={styles.sair} onClick={logout}>
          <LogOut size={16} strokeWidth={1.9} aria-hidden="true" />
          Sair
        </button>
      </div>
      {tooltip}
    </header>
  )
}
