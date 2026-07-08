// Estado global do GIVA. Roteamento por `screen` (sem react-router na V1) e
// estado de UI (tema, demo, wizard de upload, filtros, linhas expandidas).
//
// Dado de servidor (lotes, linhas) NÃO mora aqui — isso é papel do react-query
// nos próprios screens. Enquanto a API não existe, os screens usam os mocks de
// data/demo.ts quando `demo` está ligado (padrão). A faixa <DemoBanner> avisa.
import { create } from 'zustand'
import { TOUR } from '../data/ajuda'
import { login as apiLogin } from '../api/auth'
import { ApiError, setToken } from '../api/client'

export type Screen =
  | 'login' | 'a2' | 'a3' | 'a4' | 'a5' | 'a6'
  | 'b1' | 'b2' | 'b3' | 'b4' | 'b5'
  | 'consultas' | 'manual'
export type Role = 'analista' | 'operador' | 'admin'
export type UploadStep = 'select' | 'mapping' | 'preview'
export type PlanilhaTab = 'dados' | 'leiame' | 'resumo'
export type Theme = 'system' | 'light' | 'dark'

const THEME_KEY = 'giva-theme'
// Flag de "tour já visto" — auto-abertura do tour guiado só na primeira visita.
// Sugestão do handoff: por usuário logado; na V1 o token não traz id estável no
// front, então mantemos por navegador (localStorage), como no protótipo.
const TOUR_KEY = 'giva-op-tour-visto'

function tourVisto(): boolean {
  try {
    return localStorage.getItem(TOUR_KEY) === '1'
  } catch {
    return false
  }
}

function marcarTourVisto(): void {
  try {
    localStorage.setItem(TOUR_KEY, '1')
  } catch {
    /* localStorage indisponível — o tour só não será silenciado nesta sessão */
  }
}

// Modo demo (dados fictícios, sem backend) — opt-in por build. Com a API real
// conectada (produção), fica desligado; ligue com VITE_DEMO_MODE=true no build
// do frontend para telas de demonstração. Só 'true' liga — qualquer outra
// coisa (ausente, vazio) = desligado.
const DEMO_INICIAL = import.meta.env.VITE_DEMO_MODE === 'true'

/** Aplica o tema no <html> e persiste. 'system' remove o override e deixa o
 * @media (prefers-color-scheme) decidir. Espelha o script inline do index.html. */
export function applyTheme(theme: Theme): void {
  const root = document.documentElement
  if (theme === 'system') root.removeAttribute('data-theme')
  else root.setAttribute('data-theme', theme)
  try {
    localStorage.setItem(THEME_KEY, theme)
  } catch {
    /* localStorage indisponível (modo privado) — ignora, tema fica só na sessão */
  }
}

function temaInicial(): Theme {
  try {
    const salvo = localStorage.getItem(THEME_KEY)
    if (salvo === 'light' || salvo === 'dark' || salvo === 'system') return salvo
  } catch {
    /* ignora */
  }
  return 'system'
}

interface AppState {
  screen: Screen
  role: Role
  token: string | null
  authLoading: boolean
  authError: string | null
  demo: boolean
  theme: Theme
  loteId: number | null
  uploadStep: UploadStep
  arquivoSelecionado: File | null
  colunasDetectadas: string[]
  planilhaTab: PlanilhaTab
  pendFilter: string
  pendUf: string
  expanded: Record<number, boolean>
  tourStep: number | null

  go: (screen: Screen) => void
  autoTour: () => void
  startTour: () => void
  tourNext: () => void
  tourPrev: () => void
  tourClose: () => void
  login: (email: string, senha: string) => Promise<void>
  logout: () => void
  toggleDemo: () => void
  cycleTheme: () => void
  openLote: (id: number) => void
  goUpload: () => void
  pickFile: (arquivo: File, colunas: string[]) => void
  voltarSelecao: () => void
  confirmMap: () => void
  loteEnviado: (id: number) => void
  setTab: (tab: PlanilhaTab) => void
  toggleRow: (id: number) => void
  setPendFilter: (f: string) => void
  setPendUf: (f: string) => void
}

const homeDoPapel: Record<Role, Screen> = { analista: 'a2', operador: 'b1', admin: 'a2' }
const PROXIMO_TEMA: Record<Theme, Theme> = { system: 'light', light: 'dark', dark: 'system' }

export const useApp = create<AppState>((set, get) => ({
  screen: 'login',
  role: 'analista',
  token: null,
  authLoading: false,
  authError: null,
  demo: DEMO_INICIAL,
  theme: temaInicial(),
  loteId: null,
  uploadStep: 'select',
  arquivoSelecionado: null,
  colunasDetectadas: [],
  planilhaTab: 'dados',
  pendFilter: 'todos',
  pendUf: 'todos',
  expanded: {},
  tourStep: null,

  go: (screen) => set({ screen }),

  // Auto-abertura na primeira visita do operador (chamado uma vez no App).
  autoTour: () => {
    if (!tourVisto() && get().tourStep === null) {
      set({ tourStep: 0, screen: TOUR[0].screen })
    }
  },
  startTour: () => set({ tourStep: 0, screen: TOUR[0].screen }),
  tourNext: () => {
    const passo = get().tourStep
    if (passo === null) return
    if (passo >= TOUR.length - 1) {
      marcarTourVisto()
      set({ tourStep: null })
      return
    }
    const proximo = passo + 1
    set({ tourStep: proximo, screen: TOUR[proximo].screen })
  },
  tourPrev: () => {
    const passo = get().tourStep
    if (passo === null || passo === 0) return
    const anterior = passo - 1
    set({ tourStep: anterior, screen: TOUR[anterior].screen })
  },
  tourClose: () => {
    marcarTourVisto()
    set({ tourStep: null })
  },

  login: async (email, senha) => {
    set({ authLoading: true, authError: null })
    // Modo demo: sem backend, qualquer credencial válida entra como admin — assim
    // a demonstração alcança TODAS as áreas (analista + operação: B1–B5, Consultas
    // prontas, ajuda), que é o que os mocks de data/demo.ts cobrem. O tour guiado
    // auto-abre na primeira visita e leva pelas telas de operação.
    if (get().demo) {
      setToken('demo')
      set({ token: 'demo', role: 'admin', screen: 'a2', authLoading: false })
      return
    }
    try {
      const { token, papel } = await apiLogin(email, senha)
      set({ token, role: papel, screen: homeDoPapel[papel], authLoading: false })
    } catch (err) {
      const mensagem = err instanceof ApiError ? err.message : 'Falha ao conectar à API.'
      set({ authLoading: false, authError: mensagem })
    }
  },

  logout: () => {
    setToken(null)
    set({ token: null, screen: 'login', authError: null })
  },

  // Trocar de modo troca o significado do token (JWT real ↔ a string 'demo'):
  // zera a sessão e volta ao login, para nunca vazar o token de um modo no
  // outro — era o que fazia `Bearer demo` chegar na API real e voltar 401
  // "Not enough segments".
  toggleDemo: () => {
    const demo = !get().demo
    setToken(null)
    set({ demo, token: null, screen: 'login', authError: null })
  },

  cycleTheme: () => {
    const proximo = PROXIMO_TEMA[get().theme]
    applyTheme(proximo)
    set({ theme: proximo })
  },

  openLote: (id) => set({ loteId: id, screen: 'a4', expanded: {}, planilhaTab: 'dados' }),
  goUpload: () => set({ screen: 'a3', uploadStep: 'select', arquivoSelecionado: null, colunasDetectadas: [] }),
  pickFile: (arquivo, colunas) => set({ uploadStep: 'mapping', arquivoSelecionado: arquivo, colunasDetectadas: colunas }),
  voltarSelecao: () => set({ uploadStep: 'select', arquivoSelecionado: null, colunasDetectadas: [] }),
  confirmMap: () => set({ uploadStep: 'preview' }),
  loteEnviado: (id) => set({ screen: 'a4', loteId: id, uploadStep: 'select', arquivoSelecionado: null, colunasDetectadas: [] }),
  setTab: (planilhaTab) => set({ planilhaTab }),
  toggleRow: (id) => set((s) => ({ expanded: { ...s.expanded, [id]: !s.expanded[id] } })),
  setPendFilter: (pendFilter) => set({ pendFilter }),
  setPendUf: (pendUf) => set({ pendUf }),
}))
