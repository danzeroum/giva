import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, FileSpreadsheet, Upload } from 'lucide-react'
import { listarLotes, type Lote } from '../api/lotes'
import { DEMO_LOTES } from '../data/demo'
import { FAROL } from '../data/statuses'
import { useApp } from '../store/app'
import styles from './A2.module.css'

const STATUS_LOTE: Record<Lote['status'], { label: string; cor: string; bg: string }> = {
  recebido: { label: 'recebido', cor: 'var(--text-soft)', bg: 'var(--surface-2)' },
  processando: { label: 'processando', cor: 'var(--accent-ink)', bg: 'var(--accent-soft)' },
  concluido: { label: 'concluído', cor: FAROL.verde.tx, bg: FAROL.verde.bg },
  erro: { label: 'erro', cor: FAROL.vermelho.tx, bg: FAROL.vermelho.bg },
}

function ResumoCor({ lote }: { lote: Lote }) {
  if (lote.status === 'concluido' && lote.resumo) {
    const { linhas, verde, amarelo, vermelho } = lote.resumo
    const pct = (n: number) => (linhas > 0 ? Math.round((n / linhas) * 100) : 0)
    return (
      <div>
        <div className={styles.tri} aria-hidden="true">
          <span style={{ width: `${pct(verde)}%`, background: FAROL.verde.bar }} />
          <span style={{ width: `${pct(amarelo)}%`, background: FAROL.amarelo.bar }} />
          <span style={{ width: `${pct(vermelho)}%`, background: FAROL.vermelho.bar }} />
        </div>
        <div className={styles.triLeg}>{pct(verde)}% ok · {pct(amarelo)}% conferir · {pct(vermelho)}% revisão</div>
      </div>
    )
  }
  if (lote.status === 'processando' || lote.status === 'recebido') {
    const total = lote.total_linhas ?? 0
    return (
      <div>
        <div className={styles.proc} aria-hidden="true" />
        <div className={styles.triLeg}>
          <span className="mono">{lote.linhas_processadas.toLocaleString('pt-BR')}</span> de{' '}
          <span className="mono">{total.toLocaleString('pt-BR')}</span> linhas
        </div>
      </div>
    )
  }
  if (lote.status === 'erro') {
    return (
      <div className={styles.erroResumo}>
        <AlertTriangle size={14} strokeWidth={2} /> Falha ao processar o arquivo
      </div>
    )
  }
  return <span className={styles.triLeg}>—</span>
}

export function A2() {
  const { openLote, goUpload, demo } = useApp()
  const { data: lotes, isLoading } = useQuery({
    queryKey: ['lotes', demo],
    queryFn: () => (demo ? Promise.resolve(DEMO_LOTES) : listarLotes()),
  })

  return (
    <div className={styles.wrap}>
      <header className={styles.head}>
        <h1 className={styles.h1}>Meus lotes</h1>
        <button type="button" className={styles.enviar} onClick={goUpload}>
          <Upload size={16} strokeWidth={2} /> Enviar planilha
        </button>
      </header>

      {isLoading ? (
        <p>Carregando…</p>
      ) : !lotes || lotes.length === 0 ? (
        <div className={styles.vazio}>
          <FileSpreadsheet size={30} strokeWidth={1.6} />
          <h2>Envie sua primeira planilha</h2>
          <ol className={styles.passos}>
            <li><strong>Envie</strong> a planilha com NCM, período, descrição e estado.</li>
            <li><strong>Acompanhe</strong> o processamento em tempo real.</li>
            <li><strong>Baixe e revise</strong> — cada valor com a fonte legal de origem.</li>
          </ol>
          <button type="button" className={styles.enviar} onClick={goUpload}>
            <Upload size={16} strokeWidth={2} /> Enviar primeira planilha
          </button>
        </div>
      ) : (
        <div className={styles.card}>
          <table className={styles.tabela}>
            <thead>
              <tr>
                <th>Arquivo</th>
                <th>Enviado</th>
                <th>Status</th>
                <th>Resumo por cor</th>
                <th aria-label="ações" />
              </tr>
            </thead>
            <tbody>
              {lotes.map((l) => {
                const st = STATUS_LOTE[l.status]
                return (
                  <tr key={l.id}>
                    <td>
                      <div className={styles.arquivo}>
                        <FileSpreadsheet size={17} strokeWidth={1.8} />
                        <div>
                          <div className="mono">{l.nome_arquivo ?? `Lote #${l.id}`}</div>
                          <div className={styles.linhas}>
                            {(l.total_linhas ?? 0).toLocaleString('pt-BR')} linhas
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className={styles.data}>{new Date(l.criado_em).toLocaleDateString('pt-BR')}</td>
                    <td>
                      <span className={styles.pill} style={{ color: st.cor, background: st.bg }}>{st.label}</span>
                    </td>
                    <td className={styles.resumoCol}><ResumoCor lote={l} /></td>
                    <td className={styles.acaoCol}>
                      <button type="button" className={styles.detalhes} onClick={() => openLote(l.id)}>
                        Detalhes
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
