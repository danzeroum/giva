import { useQuery } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { Fragment, useState } from 'react'
import { baixarSaida, buscarLote, type LinhaLote, listarLinhas } from '../api/lotes'
import { ProofOfOrigin } from '../components/ProofOfOrigin'
import { Ressalva } from '../components/Ressalva'
import { ResumoLote } from '../components/ResumoLote'
import { StatusBadge } from '../components/StatusBadge'
import { BASES_VERSAO, demoLinhas, demoLote, LEGENDA, PROCESSADO_EM } from '../data/demo'
import { RESSALVA_CATEGORIA, RESSALVAS } from '../data/ressalvas'
import { FAROL, statusInfo } from '../data/statuses'
import { useApp } from '../store/app'
import styles from './A6.module.css'

// Colunas enriquecidas exibidas depois das originais (contrato da planilha de saída).
const COLS_ENRIQUECIDAS: { chave: keyof LinhaLote['enriquecimento'] | 'status'; rotulo: string; mono?: boolean }[] = [
  { chave: 'status', rotulo: 'Status' },
  { chave: 'descricao_oficial_ncm', rotulo: 'Descrição oficial NCM' },
  { chave: 'aliquota_icms_interna', rotulo: 'Alíquota ICMS interna', mono: true },
  { chave: 'categoria_macro', rotulo: 'Categoria macro' },
  { chave: 'confianca_categorizacao', rotulo: 'Confiança', mono: true },
]

/** Neutraliza injeção de fórmula (CSV/Excel) numa célula original: um apóstrofo
 * força a célula a texto. Mesmo critério do backend (`MontadorSaida._texto_seguro`)
 * — o `.xlsx`/`.csv` baixado já é protegido lá; aqui protege a prévia e o CSV
 * de demonstração gerado no cliente. Só se aplica às células ORIGINAIS (entrada
 * do usuário); os campos enriquecidos são gerados pelo sistema. */
const FORMULA_INJECAO = /^[=+@]|^-\d/
function textoSeguro(valor: string | undefined): string {
  const v = valor ?? ''
  return FORMULA_INJECAO.test(v) ? `'${v}` : v
}

/** Download de demonstração: sem backend, monta um CSV client-side a partir das
 * linhas de demo para o botão "baixar" fazer algo real. */
function baixarDemoCsv(linhas: LinhaLote[]): void {
  const origCols = linhas.length > 0 ? Object.keys(linhas[0].originais) : []
  const cabecalho = [...origCols, 'status', 'descricao_oficial_ncm', 'aliquota_icms_interna', 'categoria_macro', 'confianca_categorizacao']
  const escapar = (v: string) => `"${(v ?? '').replace(/"/g, '""')}"`
  const linhasCsv = linhas.map((l) =>
    [...origCols.map((c) => textoSeguro(l.originais[c])), l.status, l.enriquecimento.descricao_oficial_ncm, l.enriquecimento.aliquota_icms_interna, l.enriquecimento.categoria_macro, l.enriquecimento.confianca_categorizacao]
      .map((v) => escapar(String(v ?? '')))
      .join(','),
  )
  const conteudo = [cabecalho.map(escapar).join(','), ...linhasCsv].join('\n')
  const blob = new Blob([`\uFEFF${conteudo}`], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'giva_saida_demo.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export function A6() {
  const { loteId, planilhaTab, setTab, go, expanded, toggleRow, demo } = useApp()
  const [baixando, setBaixando] = useState(false)

  const { data: lote } = useQuery({
    queryKey: ['lote', loteId, demo],
    queryFn: () => (demo ? Promise.resolve(demoLote(loteId as number)) : buscarLote(loteId as number)),
    enabled: loteId != null,
  })
  const { data: linhas } = useQuery({
    queryKey: ['linhas', loteId, 'todas', demo],
    queryFn: () => (demo ? Promise.resolve(demoLinhas()) : listarLinhas(loteId as number)),
    enabled: loteId != null && planilhaTab === 'dados',
  })

  async function aoBaixar() {
    if (loteId == null) return
    setBaixando(true)
    try {
      if (demo) baixarDemoCsv(demoLinhas())
      else await baixarSaida(loteId)
    } finally {
      setBaixando(false)
    }
  }

  if (loteId == null || !lote) {
    return (
      <div className={styles.wrap}>
        <button type="button" className={styles.voltar} onClick={() => go('a2')}>← Meus lotes</button>
      </div>
    )
  }

  const colunasOriginais = linhas && linhas.length > 0 ? Object.keys(linhas[0].originais) : []

  return (
    <div className={styles.wrap}>
      <header className={styles.head}>
        <div>
          <button type="button" className={styles.voltar} onClick={() => go('a4')}>← Resumo do lote</button>
          <h1 className={styles.h1}>Prévia da planilha de saída</h1>
          <p className={styles.sub} title="Prévia fiel do arquivo que você baixa.">
            Prévia do arquivo — {lote.nome_arquivo ?? `Lote #${lote.id}`}
          </p>
        </div>
        <button
          type="button"
          className={styles.baixar}
          onClick={aoBaixar}
          disabled={baixando || (lote.status !== 'concluido' && !demo)}
        >
          <Download size={16} strokeWidth={2} /> {baixando ? 'Baixando…' : demo ? 'Baixar (.csv demo)' : 'Baixar .xlsx'}
        </button>
      </header>

      <div className={styles.tabs} role="tablist">
        {(['dados', 'leiame', 'resumo'] as const).map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={planilhaTab === t}
            className={`${styles.tab} ${planilhaTab === t ? styles.tabAtiva : ''}`}
            onClick={() => setTab(t)}
          >
            {t === 'dados' ? 'Dados' : t === 'leiame' ? 'Leia-me' : 'Resumo'}
          </button>
        ))}
      </div>

      {planilhaTab === 'dados' && (
        <>
          <div className={styles.disclaimer}>
            <Ressalva only={RESSALVA_CATEGORIA} />
          </div>
          <div className={styles.sheet}>
            <div className={styles.scroll}>
              <table className={styles.grid}>
                <thead>
                  <tr>
                    {colunasOriginais.map((c) => <th key={c} className={styles.th}>{c}</th>)}
                    {COLS_ENRIQUECIDAS.map((c) => <th key={c.chave} className={`${styles.th} ${styles.thEnr}`}>{c.rotulo}</th>)}
                    <th className={styles.th} aria-label="proveniência" />
                  </tr>
                </thead>
                <tbody>
                  {(linhas ?? []).map((l) => {
                    const bg = FAROL[statusInfo(l.status).farol].bg
                    const aberta = !!expanded[l.numero]
                    return (
                      <Fragment key={l.numero}>
                        <tr
                          style={{ ['--rowbg' as string]: bg }}
                          className={styles.linhaClicavel}
                          onClick={() => toggleRow(l.numero)}
                        >
                          {colunasOriginais.map((c) => (
                            <td key={c} className={`${styles.td} mono`}>{textoSeguro(l.originais[c])}</td>
                          ))}
                          {COLS_ENRIQUECIDAS.map((c) => {
                            if (c.chave === 'status') {
                              return <td key="status" className={styles.td}><StatusBadge statusKey={l.status} /></td>
                            }
                            return (
                              <td key={c.chave} className={`${styles.td} ${c.mono ? 'mono' : ''}`}>
                                {l.enriquecimento[c.chave] ?? '—'}
                              </td>
                            )
                          })}
                          <td className={styles.td}>{aberta ? '▾' : '▸'}</td>
                        </tr>
                        {aberta && (
                          <tr>
                            <td className={styles.td} colSpan={colunasOriginais.length + COLS_ENRIQUECIDAS.length + 1}>
                              <ProofOfOrigin proveniencia={l.proveniencia as Record<string, Record<string, string>>} />
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <div className={styles.rodape}>
              Clique numa linha para ver a prova de origem de cada valor enriquecido.
            </div>
          </div>
        </>
      )}

      {planilhaTab === 'leiame' && (
        <div className={styles.leiame}>
          <section className={styles.card}>
            <h2 className={styles.h2}>Legenda de cores e status</h2>
            {LEGENDA.map((g) => (
              <div key={g.farol} className={styles.legGrupo}>
                <span className={styles.legDot} style={{ background: FAROL[g.farol as keyof typeof FAROL].dot }} aria-hidden="true" />
                <div>
                  <strong style={{ color: FAROL[g.farol as keyof typeof FAROL].tx }}>{g.farol}</strong>
                  <ul>{g.statuses.map((s) => <li key={s}>{s}</li>)}</ul>
                </div>
              </div>
            ))}
          </section>

          <section className={styles.card}>
            <h2 className={styles.h2}>Ressalvas importantes</h2>
            <ol className={styles.ressalvas}>
              {RESSALVAS.map((r) => <li key={r}>{r}</li>)}
            </ol>
          </section>

          <section className={styles.card}>
            <h2 className={styles.h2}>Bases e processamento</h2>
            <p className={styles.processo}>Processado em <span className="mono">{PROCESSADO_EM}</span></p>
            <ul className={styles.bases}>
              {BASES_VERSAO.map((b) => (
                <li key={b.nome}>
                  {b.nome}: <span className={styles.baseDemo}>[{b.versao}]</span>
                </li>
              ))}
            </ul>
            <p className={styles.notaBases}>Versões marcadas <span className={styles.baseDemo}>[demo]</span> são fictícias nesta prévia.</p>
          </section>
        </div>
      )}

      {planilhaTab === 'resumo' && lote.resumo && (
        <div className={styles.resumo}>
          <ResumoLote resumo={lote.resumo} />
        </div>
      )}
    </div>
  )
}
