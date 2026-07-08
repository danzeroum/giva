import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useDica } from '../components/ComDica'
import {
  atualizarParametro,
  historicoParametro,
  listarParametros,
  type Parametro,
  type ValorParametro,
} from '../api/operacao'
import { DEMO_HISTORICO_PARAMETRO, DEMO_PARAMETROS } from '../data/demo'
import { PARAMETROS_ORDEM, parametroCopy } from '../data/parametros'
import { useApp } from '../store/app'
import styles from './operacao.module.css'

function ordenar(params: Parametro[]): Parametro[] {
  const pos = (nome: string) => {
    const i = PARAMETROS_ORDEM.indexOf(nome)
    return i === -1 ? PARAMETROS_ORDEM.length : i
  }
  return [...params].sort((a, b) => pos(a.nome) - pos(b.nome))
}

function Historico({ nome }: { nome: string }) {
  const demo = useApp((s) => s.demo)
  const { data } = useQuery({
    queryKey: ['historico-parametro', nome, demo],
    queryFn: () =>
      demo ? Promise.resolve(DEMO_HISTORICO_PARAMETRO[nome] ?? []) : historicoParametro(nome),
  })
  const itens = data ?? []
  return (
    <div style={{ marginTop: 12, borderTop: '1px solid var(--line-soft)', paddingTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
      {itens.length === 0 ? (
        <div style={{ fontSize: 12, color: 'var(--text-faint)' }}>Sem alterações registradas.</div>
      ) : (
        itens.map((h, i) => (
          <div key={i} style={{ display: 'flex', gap: 10, fontSize: 12, color: 'var(--text-soft)' }}>
            <span className={styles.mono} style={{ color: 'var(--text-faint)', flex: 'none' }}>
              {new Date(h.quando).toLocaleString('pt-BR')}
            </span>
            <span style={{ fontWeight: 600, color: 'var(--text-2)', flex: 'none' }}>{h.quem}</span>
            <span>
              {String(h.antes?.valor ?? '(novo)')} → {String(h.depois?.valor ?? '—')}
            </span>
          </div>
        ))
      )}
    </div>
  )
}

export function B3() {
  const demo = useApp((s) => s.demo)
  const qc = useQueryClient()
  const { dicaHandlers, tooltip } = useDica()
  const [edits, setEdits] = useState<Record<string, string>>({})
  const [histAberto, setHistAberto] = useState<string | null>(null)

  const { data: params, isLoading } = useQuery({
    queryKey: ['parametros', demo],
    queryFn: () => (demo ? Promise.resolve(DEMO_PARAMETROS) : listarParametros()),
  })

  const salvar = useMutation({
    mutationFn: async (v: { nome: string; valor: ValorParametro }) => {
      if (!demo) await atualizarParametro(v.nome, v.valor)
    },
    onSuccess: (_r, v) => {
      setEdits((e) => {
        const resto = { ...e }
        delete resto[v.nome]
        return resto
      })
      if (demo) {
        qc.setQueryData<Parametro[]>(['parametros', demo], (old) =>
          old?.map((p) => (p.nome === v.nome ? { ...p, valor: v.valor } : p)),
        )
      } else {
        qc.invalidateQueries({ queryKey: ['parametros'] })
        qc.invalidateQueries({ queryKey: ['historico-parametro', v.nome] })
      }
    },
  })

  return (
    <div className={`${styles.wrap} ${styles.wrapEstreito}`}>
      <h1 className={styles.h1}>Ajustes do sistema</h1>
      <p className={styles.sub}>
        Controles de como o GIVA analisa as planilhas. Cada mudança fica registrada com quem alterou e
        quando.
      </p>

      {isLoading || !params ? (
        <div className={styles.vazio}>Carregando…</div>
      ) : (
        <div className={styles.pilha}>
          {ordenar(params).map((p) => {
            const copy = parametroCopy(p.nome)
            const atual = String(p.valor ?? '')
            const editado = edits[p.nome]
            const valor = editado !== undefined ? editado : atual
            const alterado = editado !== undefined && editado !== atual
            return (
              <div key={p.nome} className={styles.itemCard}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>{copy.rotulo}</span>
                      <span className={styles.mono} style={{ fontSize: 10.5, color: 'var(--text-faint)' }}>{p.nome}</span>
                    </div>
                    <div style={{ fontSize: 12.5, color: 'var(--text-soft)', marginTop: 3 }}>{copy.descricao}</div>
                    <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 4, paddingLeft: 8, borderLeft: '2px solid var(--accent-line)' }}>
                      {copy.efeito}
                    </div>
                  </div>
                  <input
                    className={`${styles.input} ${styles.inputMono}`}
                    style={{ width: 110, textAlign: 'right' }}
                    value={valor}
                    onChange={(e) => setEdits((s) => ({ ...s, [p.nome]: e.target.value }))}
                    aria-label={`Valor de ${copy.rotulo}`}
                  />
                  {alterado && (
                    <button
                      type="button"
                      className={`${styles.btnPrim} ${styles.btnSmall}`}
                      onClick={() => salvar.mutate({ nome: p.nome, valor })}
                    >
                      Salvar
                    </button>
                  )}
                  <button
                    type="button"
                    className={`${styles.btnSec} ${styles.btnSmall}`}
                    data-dica="Mostra quem alterou este ajuste, quando, e qual era o valor antes."
                    {...dicaHandlers}
                    onClick={() => setHistAberto(histAberto === p.nome ? null : p.nome)}
                  >
                    Histórico
                  </button>
                </div>
                {histAberto === p.nome && <Historico nome={p.nome} />}
              </div>
            )
          })}
        </div>
      )}
      {tooltip}
    </div>
  )
}
