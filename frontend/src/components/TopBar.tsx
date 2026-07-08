import { LogOut, Monitor, Moon, Search, Sun } from 'lucide-react'
import { type Role, type Theme, useApp } from '../store/app'
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
  const { role, demo, theme, toggleDemo, cycleTheme, logout } = useApp()
  const iniciais = role === 'operador' ? 'OP' : role === 'admin' ? 'AD' : 'AF'
  const tema = TEMA_META[theme]
  const TemaIcon = tema.icon

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
    </header>
  )
}
