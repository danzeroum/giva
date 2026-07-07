import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { MessageSquareWarning } from 'lucide-react'
import { Fragment, useState } from 'react'
import { contestar, listarLinhas } from '../api/lotes'
import { ProofOfOrigin } from '../components/ProofOfOrigin'
import { StatusBadge } from '../components/StatusBadge'
import { demoLinhas } from '../data/demo'
import { STATUSES } from '../data/statuses'
import { useApp } from '../store/app'
import styles from './A5.module.css'

const UFS = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG',
  'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
]

export function A5() {
  const { loteId, pendFilter, pendUf, setPendFilter, setPendUf, expanded, toggleRow, go, demo } = useApp()
  const [texto, setTexto] = useState('')
  const [linhaContestando, setLinhaContestando] = useState<number | null>(null)
  const queryClient = useQueryClient()

  const filtros = {
    status: pendFilter !== 'todos' ? pendFilter : undefined,
    uf: pendUf !== 'todos' ? pendUf : undefined,
  }

  const { data: linhas, isLoading } = useQuery({
    queryKey: ['linhas', loteId, filtros, demo],
    queryFn: () => (demo ? Promise.resolve(demoLinhas(filtros)) : listarLinhas(loteId as number, filtros)),
    enabled: loteId != null,
  })

  const mutation = useMutation({
    mutationFn: (vars: { numero: number; texto: string }) => {
      if (demo) return Promise.resolve() // sem backend: apenas fecha o formulário
      return contestar(loteId as number, vars.numero, { tipo: 'outro', texto: vars.texto }).then(() => undefined)
    },
    onSuccess: () => {
      setLinhaContestando(null)
      setTexto('')
      void queryClient.invalidateQueries({ queryKey: ['linhas', loteId] })
    },
  })

  if (loteId == null) {
    return (
      <div className={styles.wrap}>
        <button type="button" className={styles.voltar} onClick={() => go('a2')}>← Meus lotes</button>
      </div>
    )
  }

  return (
    <div className={styles.wrap}>
      <header className={styles.head}>
        <button type="button" className={styles.voltar} onClick={() => go('a4')}>← Resumo do lote</button>
        <h1 className={styles.h1}>Revisão de pendências</h1>
      </header>

      <div className={styles.filtros}>
        <label className={styles.campo}>
          Status
          <select value={pendFilter} onChange={(e) => setPendFilter(e.target.value)}>
            <option value="todos">Todos</option>
            {Object.entries(STATUSES).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </label>
        <label className={styles.campo}>
          UF
          <select value={pendUf} onChange={(e) => setPendUf(e.target.value)}>
            <option value="todos">Todas</option>
            {UFS.map((uf) => <option key={uf} value={uf}>{uf}</option>)}
          </select>
        </label>
      </div>

      {isLoading ? (
        <p>Carregando…</p>
      ) : !linhas || linhas.length === 0 ? (
        <p className={styles.vazio}>Nenhuma linha encontrada para os filtros selecionados.</p>
      ) : (
        <div className={styles.card}>
          <table className={styles.tabela}>
            <thead>
              <tr>
                <th>#</th>
                <th>NCM</th>
                <th>UF</th>
                <th>Status</th>
                <th aria-label="ações" />
              </tr>
            </thead>
            <tbody>
              {linhas.map((l) => {
                const aberta = !!expanded[l.numero]
                return (
                  <Fragment key={l.numero}>
                    <tr>
                      <td className="mono">{l.numero}</td>
                      <td className="mono">{l.originais.NCM ?? '—'}</td>
                      <td>{l.uf ?? '—'}</td>
                      <td><StatusBadge statusKey={l.status} /></td>
                      <td className={styles.acaoCol}>
                        <button type="button" className={styles.detalhes} onClick={() => toggleRow(l.numero)}>
                          {aberta ? 'Fechar' : 'Detalhes'}
                        </button>
                      </td>
                    </tr>
                    {aberta && (
                      <tr>
                        <td colSpan={5} className={styles.detalheCol}>
                          <ProofOfOrigin proveniencia={l.proveniencia as Record<string, Record<string, string>>} />
                          {linhaContestando === l.numero ? (
                            <div className={styles.formContestacao}>
                              <textarea
                                className={styles.textarea}
                                value={texto}
                                onChange={(e) => setTexto(e.target.value)}
                                placeholder="Descreva sua discordância…"
                              />
                              <div className={styles.acoesForm}>
                                <button type="button" className={styles.btnSec} onClick={() => setLinhaContestando(null)}>
                                  Cancelar
                                </button>
                                <button
                                  type="button"
                                  className={styles.btnPrim}
                                  disabled={!texto.trim() || mutation.isPending}
                                  onClick={() => mutation.mutate({ numero: l.numero, texto })}
                                >
                                  {mutation.isPending ? 'Enviando…' : 'Enviar'}
                                </button>
                              </div>
                            </div>
                          ) : (
                            <button
                              type="button"
                              className={styles.btnContestar}
                              onClick={() => { setLinhaContestando(l.numero); setTexto('') }}
                            >
                              <MessageSquareWarning size={14} strokeWidth={2} /> Discordo desta linha
                            </button>
                          )}
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
