import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, BookOpen, Compass, Database, FileSpreadsheet, GitPullRequest, Inbox, type LucideIcon, MapPin, Sliders, Tags, Upload } from 'lucide-react'
import { listarCargas, listarContestacoesOperacao, listarUfs } from '../api/operacao'
import { DEMO_CARGAS, DEMO_CONTESTACOES, DEMO_UFS } from '../data/demo'
import { type Screen, useApp } from '../store/app'
import { useDica } from './ComDica'
import styles from './Sidebar.module.css'

interface Item {
  screen: Screen
  label: string
  icon: LucideIcon
  dica: string
  badge?: number
  onClick?: () => void
}

interface Grupo {
  titulo: string
  itens: Item[]
}

export function Sidebar() {
  const { screen, role, demo, go, startTour } = useApp()
  const { dicaHandlers, tooltip } = useDica()
  const showA = role === 'analista' || role === 'admin'
  const showB = role === 'operador' || role === 'admin'

  // Badges vêm das MESMAS queries usadas por B1/B2/B5 (mesmas chaves) — assim
  // uma mutação (aprovar carga, validar UF, resolver contestação) invalida/atualiza
  // o cache e a badge acompanha na hora, nos dois modos.
  const { data: cargas } = useQuery({
    queryKey: ['cargas', demo],
    queryFn: () => (demo ? Promise.resolve(DEMO_CARGAS) : listarCargas()),
    enabled: showB,
  })
  const { data: ufs } = useQuery({
    queryKey: ['ufs', demo],
    queryFn: () => (demo ? Promise.resolve(DEMO_UFS) : listarUfs()),
    enabled: showB,
  })
  const { data: contestacoes } = useQuery({
    queryKey: ['contestacoes', demo],
    queryFn: () => (demo ? Promise.resolve(DEMO_CONTESTACOES) : listarContestacoesOperacao()),
    enabled: showB,
  })
  const cargasStaging = (cargas ?? []).filter((c) => c.status === 'staging').length
  const ufsDiverg = (ufs ?? []).filter((u) => u.status_validacao === 'divergencia_entre_fontes').length
  const contestAbertas = (contestacoes ?? []).filter((c) => c.status === 'aberta').length

  const gruposA: Grupo[] = [
    {
      titulo: 'Analista',
      itens: [
        { screen: 'a2', label: 'Meus lotes', icon: Inbox, dica: 'Suas planilhas enviadas e o resultado de cada uma.' },
        { screen: 'a3', label: 'Enviar planilha', icon: Upload, dica: 'Envie uma nova planilha para o GIVA conferir.' },
      ],
    },
  ]

  const gruposB: Grupo[] = [
    {
      titulo: 'Base & motor',
      itens: [
        { screen: 'b1', label: 'Atualizações da base', icon: GitPullRequest, dica: 'Aprovar ou descartar tabelas novas de códigos e alíquotas.', badge: cargasStaging },
        { screen: 'b2', label: 'Alíquotas por estado', icon: MapPin, dica: 'Ver e conferir a alíquota de ICMS de cada estado.', badge: ufsDiverg },
        { screen: 'b3', label: 'Ajustes do sistema', icon: Sliders, dica: 'Controlar o rigor da análise das planilhas.' },
        { screen: 'b4', label: 'Correções de categoria', icon: Tags, dica: 'Corrigir produtos que caem na categoria errada.' },
        { screen: 'b5', label: 'Contestações', icon: AlertTriangle, dica: 'Responder dúvidas e discordâncias dos analistas.', badge: contestAbertas },
      ],
    },
    {
      titulo: 'Banco de dados',
      itens: [
        { screen: 'consultas', label: 'Consultas prontas', icon: Database, dica: 'Perguntar à base e copiar o resultado para o Excel.' },
      ],
    },
    {
      titulo: 'Ajuda',
      itens: [
        { screen: 'manual', label: 'Manual prático', icon: BookOpen, dica: 'Passo a passo das tarefas do dia a dia.' },
        { screen: 'b1', label: 'Tour guiado', icon: Compass, dica: 'Percorre as telas em 2 minutos, explicando cada área.', onClick: startTour },
      ],
    },
  ]

  // Telas de lote (a4/a5/a6) mantêm "Meus lotes" como grupo ativo.
  const grupoAtivo = (s: Screen): Screen =>
    (['a4', 'a5', 'a6'] as Screen[]).includes(s) ? 'a2' : s

  const renderItem = (it: Item) => {
    const ativo = it.onClick === undefined && grupoAtivo(screen) === it.screen
    const Icon = it.icon
    return (
      <button
        key={`${it.label}`}
        type="button"
        className={`${styles.item} ${ativo ? styles.itemAtivo : ''}`}
        aria-current={ativo ? 'page' : undefined}
        data-dica={it.dica}
        {...dicaHandlers}
        onClick={() => (it.onClick ? it.onClick() : go(it.screen))}
      >
        <Icon size={17} strokeWidth={1.9} />
        <span>{it.label}</span>
        {it.badge ? <span className={styles.badge}>{it.badge}</span> : null}
      </button>
    )
  }

  const grupos = showA && showB ? [...gruposA, ...gruposB] : showB ? gruposB : gruposA

  return (
    <nav className={styles.sidebar} aria-label="Navegação principal">
      {grupos.map((g) => (
        <div key={g.titulo} className={styles.grupo}>
          <div className={styles.rotulo}>{g.titulo}</div>
          {g.itens.map(renderItem)}
        </div>
      ))}
      <div className={styles.rodape}>
        <FileSpreadsheet size={14} strokeWidth={1.8} aria-hidden="true" />
        A superfície nº 1 é a planilha de saída.
      </div>
      {tooltip}
    </nav>
  )
}
