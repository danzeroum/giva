import { type FormEvent, useState } from 'react'
import { FAROL } from '../data/statuses'
import { useApp } from '../store/app'
import styles from './Login.module.css'

const LEGENDA: { farol: keyof typeof FAROL; texto: string }[] = [
  { farol: 'verde', texto: 'ok' },
  { farol: 'amarelo', texto: 'conferir' },
  { farol: 'vermelho', texto: 'requer revisão' },
]

export function Login() {
  const login = useApp((s) => s.login)
  const authLoading = useApp((s) => s.authLoading)
  const authError = useApp((s) => s.authError)
  const demo = useApp((s) => s.demo)
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')

  function aoSubmeter(e: FormEvent) {
    e.preventDefault()
    void login(email, senha)
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <section className={styles.left}>
          <div className={styles.brand}>
            <span className={styles.mark} aria-hidden="true"><span /></span>
            <span className={styles.wordmark}>GIVA</span>
          </div>
          <h1 className={styles.headline}>Enriquecimento NCM / ICMS com lastro legal.</h1>
          <p className={styles.lead}>
            Envie sua planilha de itens e receba, de volta, cada linha com a descrição oficial da
            NCM, a alíquota interna do estado no período e a categoria macro de gasto — sempre com a
            fonte legal de origem.
          </p>
          <div className={styles.legenda}>
            {LEGENDA.map((l) => (
              <span key={l.farol} className={styles.legItem}>
                <span className={styles.legDot} style={{ background: FAROL[l.farol].dot }} aria-hidden="true" />
                {l.texto}
              </span>
            ))}
          </div>
        </section>

        <section className={styles.right}>
          <div className={styles.rightTitle}>Entrar</div>
          <form className={styles.form} onSubmit={aoSubmeter}>
            <label className={styles.field}>
              <span>Email</span>
              <input
                className={styles.input}
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <label className={styles.field}>
              <span>Senha</span>
              <input
                className={styles.input}
                type="password"
                autoComplete="current-password"
                required
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
              />
            </label>
            {authError && <p className={styles.erro}>{authError}</p>}
            <button type="submit" className={styles.entrar} disabled={authLoading}>
              {authLoading ? 'Entrando…' : 'Entrar'}
            </button>
          </form>
          {demo && (
            <p className={styles.notaDemo}>
              Modo de demonstração: qualquer email e senha entram como analista fiscal.
            </p>
          )}
          <p className={styles.nota}>Sem autocadastro nesta versão.</p>
        </section>
      </div>
    </div>
  )
}
