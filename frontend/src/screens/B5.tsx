import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useDica } from '../components/ComDica'
import { Selo } from '../components/Selo'
import { useMenuGlobal } from '../components/useMenuGlobal'
import {
  type ContestacaoOperacao,
  type DestinoContestacao,
  encaminharContestacao,
  listarContestacoesOperacao,
} from '../api/operacao'
import { DEMO_CONTESTACOES } from '../data/demo'
import { CATEGORIAS_EFD } from '../data/parametros'
import { useApp } from '../store/app'
import styles from './operacao.module.css'

interface FormEnc {
  destino: DestinoContestacao
  ncm: string
  categoria: string
  resolucao: string
}

const VAZIO: FormEnc = { destino: 'resposta', ncm: '', categoria: 'EPI', resolucao: '' }

export function B5() {
  const demo = useApp((s) => s.demo)
  const qc = useQueryClient()
  const { dicaHandlers, tooltip } = useDica()
  const { menu, setMenu, alternar } = useMenuGlobal()
  const [encId, setEncId] = useState<number | null>(null)
  const [form, setForm] = useState<FormEnc>(VAZIO)

  const { data: contestacoes, isLoading } = useQuery({
    queryKey: ['contestacoes', demo],
    queryFn: () => (demo ? Promise.resolve(DEMO_CONTESTACOES) : listarContestacoesOperacao()),
  })

  const abrirForm = (id: number, destino: DestinoContestacao) => {
    setMenu(null)
    setEncId(id)
    setForm({ ...VAZIO, destino })
  }

  const resolver = useMutation({
    mutationFn: async (v: { id: number; form: FormEnc }) => {
      if (demo) return
      await encaminharContestacao(v.id, {
        destino: v.form.destino,
        resolucao: v.form.resolucao,
        categoria: v.form.destino === 'excecao' ? v.form.categoria : null,
        ncm: v.form.destino === 'excecao' ? v.form.ncm.replace(/\D/g, '') : null,
      })
    },
    onSuccess: (_r, v) => {
      setEncId(null)
      setForm(VAZIO)
      if (demo) {
        qc.setQueryData<ContestacaoOperacao[]>(['contestacoes', demo], (old) =>
          old?.map((c) =>
            c.id === v.id
              ? { ...c, status: 'resolvida', resolucao: v.form.resolucao, resolvido_em: new Date().toISOString() }
              : c,
          ),
        )
      } else {
        qc.invalidateQueries({ queryKey: ['contestacoes'] })
        qc.invalidateQueries({ queryKey: ['excecoes'] })
      }
    },
  })

  const submeter = (id: number) => {
    if (!form.resolucao.trim()) return
    resolver.mutate({ id, form })
  }

  return (
    <div className={`${styles.wrap} ${styles.wrapEstreito}`} style={{ maxWidth: 860 }}>
      <h1 className={styles.h1}>Contestações</h1>
      <p className={styles.sub}>
        Dúvidas e discordâncias que os analistas apontaram nas planilhas. Responda ou corrija a base
        direto daqui.
      </p>

      {isLoading || !contestacoes ? (
        <div className={styles.vazio}>Carregando…</div>
      ) : contestacoes.length === 0 ? (
        <div className={styles.vazio}>Nenhuma contestação.</div>
      ) : (
        <div className={styles.pilha}>
          {contestacoes.map((c) => {
            const aberta = c.status === 'aberta'
            const encAqui = encId === c.id
            const placeholder =
              form.destino === 'validacao_uf'
                ? 'Ex.: enviado à fila de validação de PE'
                : 'Texto da resolução para o analista'
            return (
              <div key={c.id} className={styles.itemCard}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span className={styles.mono} style={{ fontSize: 12, color: 'var(--text-faint)' }}>#{c.id}</span>
                      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-2)' }}>{c.tipo}</span>
                      <span style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                        lote {c.lote_id} · linha {c.numero_linha} · {new Date(c.criado_em).toLocaleDateString('pt-BR')}
                      </span>
                    </div>
                    <div style={{ fontSize: 13.5, marginTop: 6, color: 'var(--text)' }}>{c.texto}</div>
                    {c.resolucao && (
                      <div style={{ fontSize: 12.5, marginTop: 8, color: 'var(--farol-verde-tx)', background: 'var(--farol-verde-bg)', borderRadius: 8, padding: '7px 10px' }}>
                        Resolução: {c.resolucao}
                      </div>
                    )}
                  </div>
                  <Selo farol={aberta ? 'amarelo' : 'verde'} label={aberta ? 'aberta' : 'resolvida'} />
                  {aberta && (
                    <div style={{ position: 'relative', flex: 'none' }}>
                      <button
                        type="button"
                        className={`${styles.btnSec} ${styles.btnSmall}`}
                        data-dica="Escolha o que fazer: corrigir a categoria, mandar conferir a alíquota ou só responder."
                        {...dicaHandlers}
                        onClick={alternar(`ct${c.id}`)}
                      >
                        Encaminhar ▾
                      </button>
                      {menu === `ct${c.id}` && (
                        <div className={`${styles.menu} ${styles.menuDireita}`} style={{ minWidth: 230 }} role="menu">
                          <button type="button" className={styles.menuItem} onClick={() => abrirForm(c.id, 'excecao')}>
                            Corrigir a categoria
                          </button>
                          <button type="button" className={styles.menuItem} onClick={() => abrirForm(c.id, 'validacao_uf')}>
                            Mandar conferir a alíquota do estado
                          </button>
                          <button type="button" className={styles.menuItem} onClick={() => abrirForm(c.id, 'resposta')}>
                            Responder e resolver
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {encAqui && (
                  <div className={styles.form} style={{ marginTop: 12, borderTop: '1px solid var(--line-soft)', paddingTop: 12 }}>
                    {form.destino === 'excecao' && (
                      <>
                        <label className={styles.campo}>
                          NCM
                          <input
                            className={`${styles.input} ${styles.inputMono}`}
                            style={{ width: 120 }}
                            value={form.ncm}
                            onChange={(e) => setForm((f) => ({ ...f, ncm: e.target.value }))}
                          />
                        </label>
                        <label className={styles.campo}>
                          Categoria
                          <select
                            className={styles.select}
                            value={form.categoria}
                            onChange={(e) => setForm((f) => ({ ...f, categoria: e.target.value }))}
                          >
                            {CATEGORIAS_EFD.map((cat) => (
                              <option key={cat} value={cat}>{cat}</option>
                            ))}
                          </select>
                        </label>
                      </>
                    )}
                    <label className={`${styles.campo} ${styles.campoLargo}`}>
                      Resolução
                      <input
                        className={styles.input}
                        placeholder={placeholder}
                        value={form.resolucao}
                        onChange={(e) => setForm((f) => ({ ...f, resolucao: e.target.value }))}
                      />
                    </label>
                    <button type="button" className={`${styles.btnPrim} ${styles.btnSmall}`} onClick={() => submeter(c.id)}>
                      Resolver
                    </button>
                    <button type="button" className={`${styles.btnSec} ${styles.btnSmall}`} onClick={() => setEncId(null)}>
                      Cancelar
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
      {tooltip}
    </div>
  )
}
