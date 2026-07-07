import { DemoBanner } from './components/DemoBanner'
import { Sidebar } from './components/Sidebar'
import { TopBar } from './components/TopBar'
import { A2 } from './screens/A2'
import { A3 } from './screens/A3'
import { A4 } from './screens/A4'
import { A5 } from './screens/A5'
import { A6 } from './screens/A6'
import { B1 } from './screens/B1'
import { B2 } from './screens/B2'
import { B3 } from './screens/B3'
import { B4 } from './screens/B4'
import { B5 } from './screens/B5'
import { Login } from './screens/Login'
import { useApp } from './store/app'
import styles from './App.module.css'

const TELAS = {
  a2: A2, a3: A3, a4: A4, a5: A5, a6: A6,
  b1: B1, b2: B2, b3: B3, b4: B4, b5: B5,
} as const

export function App() {
  const { screen, demo } = useApp()

  if (screen === 'login') return <Login />

  const Tela = TELAS[screen]

  return (
    <div className={styles.app}>
      <TopBar />
      {demo && <DemoBanner />}
      <div className={styles.body}>
        <Sidebar />
        <main className={styles.main}>
          <Tela />
        </main>
      </div>
    </div>
  )
}
