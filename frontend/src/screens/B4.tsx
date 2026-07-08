import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useDica } from '../components/ComDica'
import { criarExcecao, type Excecao, listarExcecoes } from '../api/operacao'
import { DEMO_EXCECOES } from '../data/demo'
import { CATEGORIAS_EFD } from '../data/parametros'
import { useApp } from '../store/app'
import styles from './operacao.module.css'

function fmtNcm(ncm: string): string {
  const d = ncm.replace(/\D/g, '')
  return d.length === 8 ? `${d.slice(0, 4)}.${d.slice(4, 6)}.${d.slice(6, 8)}` : ncm
}

function origem(e: Excecao): string {
  if (e.origem_tipo === 'contestacao' && e.origem_contestacao_id) return `contestação #${e.origem_contestacao_id}`
  return e.origem_tipo ?? 'curadoria'
}

export function B4() {
  const demo = useApp((s) => s.demo)
  const qc = useQueryClient()
  const { dicaHandlers, tooltip } = useDica()
  const [aberto, setAberto] = useState(false)
  const [form, setForm] = useState({ ncm: '', categoria: 'EPI', justificativa: '' })
  const [erro, setErro] = useState<string | null>(null)

  const { data: excecoes, isLoading } = useQuery({
    queryKey: ['excecoes', demo],
    queryFn: () => (demo ? Promise.resolve(DEMO_EXCECOES) : listarExcecoes()),
  })

  const versao = excecoes?.[0]?.versao ?? 'v4'

  const criar = useMutation({
    mutationFn: (dados: { ncm: string; categoria: string; justificativa: string }) =>
      demo ? Promise.resolve(null) : criarExcecao(dados),
    onSuccess: (_r, dados) => {
      setForm({ ncm: '', categoria: 'EPI', justificativa: '' })
      setAberto(false)
      setErro(null)
      if (demo) {
        const nova: Excecao = {
          ncm: dados.ncm,
          categoria: dados.categoria,
          justificativa: dados.justificativa,
          versao,
          origem_tipo: 'curadoria',
          origem_contestacao_id: null,
          autor_id: null,
          criado_em: new Date().toISOString(),
        }
        qc.setQueryData<Excecao[]>(['excecoes', demo], (old) => [nova, ...(old ?? [])])
      } else {
        qc.invalidateQueries({ queryKey: ['excecoes'] })
      }
    },
  })

  const submeter = () => {
    const ncm = form.ncm.replace(/\D/g, '')
    if (ncm.length !== 8) {
      setErro('NCM precisa de 8 dígitos.')
      return
    }
    if (!form.justificativa.trim()) {
      setErro('Motivo é obrigatório.')
      return
    }
    criar.mutate({ ncm, categoria: form.categoria, justificativa: form.justificativa })
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.head}>
        <div style={{ flex: 1 }}>
          <h1 className={styles.h1}>Correções de categoria</h1>
          <p className={styles.sub}>
            Quando um código NCM cai na categoria errada, corrija aqui — a correção vale para todos os
            próximos processamentos. Versão em uso: <span className={styles.mono}>{versao}</span>
          </p>
        </div>
        <button
          type="button"
          className={styles.btnPrim}
          data-dica="Abre o formulário: informe o código NCM, a categoria certa e o motivo."
          {...dicaHandlers}
          onClick={() => {
            setAberto((v) => !v)
            setErro(null)
          }}
        >
          {aberto ? 'Fechar' : 'Nova correção'}
        </button>
      </div>

      {aberto && (
        <div className={`${styles.form} ${styles.formDestaque}`}>
          <label className={styles.campo}>
            NCM (8 dígitos)
            <input
              className={`${styles.input} ${styles.inputMono}`}
              style={{ width: 130 }}
              placeholder="3926.20.00"
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
              {CATEGORIAS_EFD.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </label>
          <label className={`${styles.campo} ${styles.campoLargo}`}>
            Motivo (obrigatório)
            <input
              className={styles.input}
              placeholder="Por que esta correção existe"
              value={form.justificativa}
              onChange={(e) => setForm((f) => ({ ...f, justificativa: e.target.value }))}
            />
          </label>
          <button type="button" className={styles.btnPrim} onClick={submeter}>Salvar correção</button>
          {erro && <span className={styles.erroPill}>{erro}</span>}
        </div>
      )}

      <div className={styles.card}>
        {isLoading ? (
          <div className={styles.vazio}>Carregando…</div>
        ) : !excecoes || excecoes.length === 0 ? (
          <div className={styles.vazio}>Nenhuma correção cadastrada.</div>
        ) : (
          <table className={styles.tabela}>
            <thead>
              <tr>
                <th>NCM</th>
                <th>Categoria</th>
                <th>Justificativa</th>
                <th>Origem</th>
                <th>Criada em</th>
              </tr>
            </thead>
            <tbody>
              {excecoes.map((e) => (
                <tr key={`${e.ncm}-${e.versao}`}>
                  <td className={styles.mono}>{fmtNcm(e.ncm)}</td>
                  <td style={{ fontWeight: 600, color: 'var(--text-2)' }}>{e.categoria}</td>
                  <td className={styles.faint}>{e.justificativa}</td>
                  <td className={styles.faint}>{origem(e)}</td>
                  <td className={styles.faint}>{new Date(e.criado_em).toLocaleDateString('pt-BR')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {tooltip}
    </div>
  )
}
