import { AlertTriangle, FileSpreadsheet, GitPullRequest, Inbox, type LucideIcon, MapPin, Sliders, Tags, Upload } from 'lucide-react'
import { DEMO_CARGAS, DEMO_CONTESTACOES, DEMO_UFS } from '../data/demo'
import { type Screen, useApp } from '../store/app'
import styles from './Sidebar.module.css'

interface Item { screen: Screen; label: string; icon: LucideIcon; badge?: number }

export function Sidebar() {
  const { screen, role, demo, go } = useApp()
  const showA = role === 'analista' || role === 'admin'
  const showB = role === 'operador' || role === 'admin'

  const cargasStaging = demo ? DEMO_CARGAS.filter((c) => c.status === 'staging').length : 0
  const ufsDiverg = demo ? DEMO_UFS.filter((u) => u.status_validacao === 'divergencia_entre_fontes').length : 0
  const contestAbertas = demo ? DEMO_CONTESTACOES.filter((c) => c.status === 'aberta').length : 0

  const grupoA: Item[] = [
    { screen: 'a2', label: 'Meus lotes', icon: Inbox },
    { screen: 'a3', label: 'Enviar planilha', icon: Upload },
  ]
  const grupoB: Item[] = [
    { screen: 'b1', label: 'Cargas e aprovações', icon: GitPullRequest, badge: cargasStaging },
    { screen: 'b2', label: 'Validação por estado', icon: MapPin, badge: ufsDiverg },
    { screen: 'b3', label: 'Parâmetros do motor', icon: Sliders },
    { screen: 'b4', label: 'Exceções de categoria', icon: Tags },
    { screen: 'b5', label: 'Contestações', icon: AlertTriangle, badge: contestAbertas },
  ]

  // Telas de lote (a4/a5/a6) mantêm "Meus lotes" como grupo ativo.
  const grupoAtivo = (s: Screen): Screen =>
    (['a4', 'a5', 'a6'] as Screen[]).includes(s) ? 'a2' : s

  const renderItem = (it: Item) => {
    const ativo = grupoAtivo(screen) === it.screen
    const Icon = it.icon
    return (
      <button
        key={it.screen}
        type="button"
        className={`${styles.item} ${ativo ? styles.itemAtivo : ''}`}
        aria-current={ativo ? 'page' : undefined}
        onClick={() => go(it.screen)}
      >
        <Icon size={17} strokeWidth={1.9} />
        <span>{it.label}</span>
        {it.badge ? <span className={styles.badge}>{it.badge}</span> : null}
      </button>
    )
  }

  return (
    <nav className={styles.sidebar} aria-label="Navegação principal">
      {showA && (
        <div className={styles.grupo}>
          <div className={styles.rotulo}>Analista</div>
          {grupoA.map(renderItem)}
        </div>
      )}
      {showB && (
        <div className={styles.grupo}>
          <div className={styles.rotulo}>Operação</div>
          {grupoB.map(renderItem)}
        </div>
      )}
      <div className={styles.rodape}>
        <FileSpreadsheet size={14} strokeWidth={1.8} aria-hidden="true" />
        A superfície nº 1 é a planilha de saída.
      </div>
    </nav>
  )
}
