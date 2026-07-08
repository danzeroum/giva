import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useDica } from '../components/ComDica'
import { ApiError } from '../api/client'
import {
  type ConsultaResposta,
  consultarAliquota,
  consultarAuditoria,
  consultarLinhas,
  consultarNcm,
  consultarRegras,
  consultarSaude,
  executarSql,
} from '../api/consultas'
import { listarUfs } from '../api/operacao'
import { CONSULTAS_META, executarConsultaDemo, type ParamsConsulta, type ScriptConsulta } from '../data/demoConsultas'
import { DEMO_UFS } from '../data/demo'
import { STATUSES } from '../data/statuses'
import { useApp } from '../store/app'
import base from './operacao.module.css'
import styles from './Consultas.module.css'

const PARAMS_INICIAIS: ParamsConsulta = {
  ncm: '', periodo: '', uf: 'SP', status: 'todos', lUf: 'todos', alvo: '',
  sql: 'SELECT * FROM ncm_vigente LIMIT 5',
}

const VAZIO: Record<ScriptConsulta, string> = {
  ncm: 'Nenhum NCM encontrado. Verifique zeros à esquerda — nunca à direita.',
  aliquota: 'Sem alíquota para esse estado/período.',
  regras: 'Nenhuma regra casa — cairia em Indefinido.',
  linhas: 'Nenhuma linha com esse filtro.',
  auditoria: 'Nada na auditoria para esse filtro.',
  saude: 'Nenhum resultado.',
  sql: 'Nenhuma linha.',
}

const STATUS_OPCOES = [{ valor: 'todos', label: 'todos' }].concat(
  Object.entries(STATUSES).map(([valor, info]) => ({ valor, label: info.label })),
)

function mensagemErro(e: unknown): string {
  if (e instanceof ApiError) return e.message
  if (e instanceof Error) return e.message
  return 'Não consegui rodar a consulta.'
}

export function Consultas() {
  const demo = useApp((s) => s.demo)
  const { dicaHandlers, tooltip } = useDica()
  const [script, setScript] = useState<ScriptConsulta>('ncm')
  const [q, setQ] = useState<ParamsConsulta>(PARAMS_INICIAIS)
  const [resultado, setResultado] = useState<ConsultaResposta | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [copiado, setCopiado] = useState(false)

  const { data: ufs } = useQuery({
    queryKey: ['ufs', demo],
    queryFn: () => (demo ? Promise.resolve(DEMO_UFS) : listarUfs()),
  })
  const siglas = ufs && ufs.length ? ufs.map((u) => u.uf) : [q.uf]

  const set = (campo: keyof ParamsConsulta) => (e: { target: { value: string } }) =>
    setQ((s) => ({ ...s, [campo]: e.target.value }))

  const chamarApi = (): Promise<ConsultaResposta> => {
    switch (script) {
      case 'ncm': return consultarNcm(q.ncm, q.periodo)
      case 'aliquota': return consultarAliquota(q.uf, q.periodo)
      case 'regras': return consultarRegras(q.ncm)
      case 'linhas': return consultarLinhas({
        status: q.status === 'todos' ? undefined : q.status,
        uf: q.lUf === 'todos' ? undefined : q.lUf,
      })
      case 'auditoria': return consultarAuditoria(q.alvo)
      case 'saude': return consultarSaude()
      case 'sql': return executarSql(q.sql)
    }
  }

  const executar = async () => {
    setErro(null)
    setCopiado(false)
    try {
      const r = demo ? executarConsultaDemo(script, q) : await chamarApi()
      setResultado(r)
    } catch (e) {
      setResultado(null)
      setErro(mensagemErro(e))
    }
  }

  const selecionar = (key: ScriptConsulta) => {
    setScript(key)
    setResultado(null)
    setErro(null)
  }

  const copiar = () => {
    if (!resultado) return
    const tsv = [resultado.cols.join('\t')]
      .concat(resultado.rows.map((row) => row.map((c) => (c === null ? '' : String(c))).join('\t')))
      .join('\n')
    void navigator.clipboard?.writeText(tsv)
    setCopiado(true)
    setTimeout(() => setCopiado(false), 1600)
  }

  const vazio = resultado !== null && resultado.rows.length === 0

  return (
    <div className={styles.wrap}>
      <h1 className={base.h1}>Consultas prontas</h1>
      <p className={base.sub}>
        Perguntas frequentes à base do GIVA — funciona como um filtro de planilha: escolha a pergunta,
        preencha e execute. Nada aqui altera dados.
      </p>

      <div className={styles.layout}>
        <div className={styles.rail}>
          {CONSULTAS_META.map((c) => (
            <button
              key={c.key}
              type="button"
              className={`${styles.railItem} ${script === c.key ? styles.railItemAtivo : ''}`}
              onClick={() => selecionar(c.key)}
            >
              <span>{c.label}</span>
              <span className={styles.railSub}>{c.sub}</span>
            </button>
          ))}
        </div>

        <div className={styles.direita}>
          <div className={styles.paramCard}>
            {script === 'ncm' && (
              <div className={base.form}>
                <label className={base.campo}>
                  Código NCM ou termo da descrição
                  <input className={`${base.input} ${base.inputMono}`} style={{ width: 260 }} placeholder="8471.30.19 ou “furadeira”" value={q.ncm} onChange={set('ncm')} />
                </label>
                <label className={base.campo}>
                  Período (opcional)
                  <input className={`${base.input} ${base.inputMono}`} style={{ width: 110 }} placeholder="2026-05" value={q.periodo} onChange={set('periodo')} />
                </label>
              </div>
            )}
            {script === 'aliquota' && (
              <div className={base.form}>
                <label className={base.campo}>
                  UF
                  <select className={base.select} value={q.uf} onChange={set('uf')}>
                    {siglas.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </label>
                <label className={base.campo}>
                  Período (AAAA-MM)
                  <input className={`${base.input} ${base.inputMono}`} style={{ width: 110 }} placeholder="2026-05" value={q.periodo} onChange={set('periodo')} />
                </label>
              </div>
            )}
            {script === 'regras' && (
              <label className={base.campo}>
                NCM
                <input className={`${base.input} ${base.inputMono}`} style={{ width: 200 }} placeholder="3926.20.00" value={q.ncm} onChange={set('ncm')} />
              </label>
            )}
            {script === 'linhas' && (
              <div className={base.form}>
                <label className={base.campo}>
                  Status
                  <select className={base.select} value={q.status} onChange={set('status')}>
                    {STATUS_OPCOES.map((o) => <option key={o.valor} value={o.valor}>{o.label}</option>)}
                  </select>
                </label>
                <label className={base.campo}>
                  UF
                  <select className={base.select} value={q.lUf} onChange={set('lUf')}>
                    <option value="todos">todas</option>
                    {siglas.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </label>
              </div>
            )}
            {script === 'auditoria' && (
              <label className={base.campo}>
                Filtro (quem, ação ou alvo — opcional)
                <input className={base.input} style={{ width: 280 }} placeholder="parametro:t_ok ou m.ferraz" value={q.alvo} onChange={set('alvo')} />
              </label>
            )}
            {script === 'saude' && (
              <div style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                Cobertura e pendências de todas as bases de referência. Sem parâmetros.
              </div>
            )}
            {script === 'sql' && (
              <div>
                <textarea className={styles.textarea} rows={4} spellCheck={false} value={q.sql} onChange={set('sql')} aria-label="Consulta SQL" />
                <div className={styles.sqlHint}>
                  Somente SELECT, tabelas da whitelist. Ex.: <span className="mono">SELECT * FROM ncm_vigente LIMIT 5</span>
                </div>
              </div>
            )}
            <div style={{ marginTop: 12 }}>
              <button
                type="button"
                className={base.btnPrim}
                data-dica="Roda a consulta e mostra o resultado como uma tabela — nada é alterado."
                {...dicaHandlers}
                onClick={executar}
              >
                Executar
              </button>
            </div>
          </div>

          {(erro || vazio || (resultado && resultado.rows.length > 0)) && (
            <div className={styles.resultCard}>
              {erro ? (
                <div className={styles.erro}>{erro}</div>
              ) : vazio ? (
                <div className={styles.erro}>{VAZIO[script]}</div>
              ) : resultado ? (
                <>
                  <table className={styles.resultTable}>
                    <thead>
                      <tr>
                        {resultado.cols.map((col) => <th key={col}>{col}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {resultado.rows.map((row, i) => (
                        <tr key={i}>
                          {row.map((cel, j) => <td key={j}>{cel === null ? '' : String(cel)}</td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div className={styles.footer}>
                    <span>{resultado.nota}</span>
                    <span className={styles.contagem}>
                      {resultado.rows.length} {resultado.rows.length === 1 ? 'linha' : 'linhas'}
                    </span>
                    <button
                      type="button"
                      className={`${base.btnSec} ${base.btnSmall}`}
                      data-dica="Copia a tabela inteira — abra o Excel e cole com Ctrl+V."
                      {...dicaHandlers}
                      onClick={copiar}
                    >
                      {copiado ? 'Copiado ✓' : 'Copiar p/ Excel'}
                    </button>
                  </div>
                </>
              ) : null}
            </div>
          )}
        </div>
      </div>
      {tooltip}
    </div>
  )
}
