import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Download, ListChecks, RefreshCw } from 'lucide-react'
import { useEffect, useState } from 'react'
import { buscarLote, type Lote } from '../api/lotes'
import { ResumoLote } from '../components/ResumoLote'
import { demoLote } from '../data/demo'
import { useApp } from '../store/app'
import styles from './A4.module.css'

function emAndamento(status: Lote['status']): boolean {
  return status === 'recebido' || status === 'processando'
}

export function A4() {
  const { loteId, go, demo } = useApp()

  const { data: lote, isLoading } = useQuery({
    queryKey: ['lote', loteId, demo],
    queryFn: () => (demo ? Promise.resolve(demoLote(loteId as number)) : buscarLote(loteId as number)),
    enabled: loteId != null,
    // Polling real só fora do modo demo; no demo, a progressão é simulada abaixo.
    refetchInterval: (query) =>
      !demo && query.state.data && emAndamento(query.state.data.status) ? 1200 : false,
  })

  // Progressão simulada no modo demo (sem backend para responder ao polling).
  const [demoProg, setDemoProg] = useState(0)
  const emDemoAndamento = demo && lote != null && emAndamento(lote.status)
  useEffect(() => {
    if (!emDemoAndamento) return
    setDemoProg(38)
    const t = setInterval(() => {
      setDemoProg((p) => {
        if (p >= 100) {
          clearInterval(t)
          return 100
        }
        return Math.min(100, p + 9)
      })
    }, 450)
    return () => clearInterval(t)
  }, [emDemoAndamento, lote?.id])

  if (loteId == null) {
    return (
      <div className={styles.centro}>
        <button type="button" className={styles.btnSec} onClick={() => go('a2')}>← Meus lotes</button>
      </div>
    )
  }

  if (isLoading || !lote) {
    return <div className={styles.centro}>Carregando…</div>
  }

  const mostrarProgresso = emAndamento(lote.status) && (!demo || demoProg < 100)

  if (mostrarProgresso) {
    const total = lote.total_linhas ?? 0
    const progresso = demo ? demoProg : total > 0 ? Math.round((lote.linhas_processadas / total) * 100) : 0
    const feito = demo ? Math.round((total * demoProg) / 100) : lote.linhas_processadas
    return (
      <div className={styles.centro}>
        <div className={styles.cardProc}>
          <div className={styles.badgeProc}>
            <span className={styles.dotProc} aria-hidden="true" /> Processando
          </div>
          <div className={styles.barra}>
            <span className={styles.barraFill} style={{ width: `${progresso}%` }} />
          </div>
          <div className={styles.procLinha}>
            <span className="mono">
              {feito.toLocaleString('pt-BR')} de {total.toLocaleString('pt-BR')} linhas
            </span>
            <span className="mono">{progresso}%</span>
          </div>
          <p className={styles.procTempo}>Atualizando automaticamente…</p>
        </div>
      </div>
    )
  }

  if (lote.status === 'erro') {
    return (
      <div className={styles.centro}>
        <div className={styles.cardErro}>
          <div className={styles.erroBar}>
            <AlertTriangle size={18} strokeWidth={2} /> Não foi possível processar o lote
          </div>
          <p className={styles.erroCausa}>Erro ao processar o arquivo.</p>
          <p className={styles.erroDica}>
            Confira se a planilha tem as quatro colunas mínimas (NCM, Período, Descrição, Estado) e
            envie novamente.
          </p>
          <div className={styles.acoes}>
            <button type="button" className={styles.btnPrim} onClick={() => go('a3')}>
              <RefreshCw size={16} strokeWidth={2} /> Enviar novamente
            </button>
            <button type="button" className={styles.btnSec} onClick={() => go('a2')}>Voltar aos lotes</button>
          </div>
        </div>
      </div>
    )
  }

  const resumo = lote.resumo
  const precisamAtencao = resumo ? resumo.amarelo + resumo.vermelho : 0

  return (
    <div className={styles.wrap}>
      <header className={styles.head}>
        <div>
          <button type="button" className={styles.voltar} onClick={() => go('a2')}>← Meus lotes</button>
          <h1 className={styles.h1}>Resumo do lote</h1>
          <p className={styles.sub}>{lote.nome_arquivo ?? `Lote #${lote.id}`} · concluído</p>
        </div>
        <div className={styles.acoesHead}>
          <button type="button" className={styles.btnSec} onClick={() => go('a5')}>
            <ListChecks size={16} strokeWidth={2} /> Revisar pendências
          </button>
          <button type="button" className={styles.btnPrim} onClick={() => go('a6')}>
            <Download size={16} strokeWidth={2} /> Ver planilha de saída
          </button>
        </div>
      </header>

      {precisamAtencao > 0 && (
        <div className={styles.atencao}>
          <AlertTriangle size={16} strokeWidth={2} />
          <span>
            <strong>{precisamAtencao.toLocaleString('pt-BR')} linhas</strong> precisam de atenção
            (conferir ou requer revisão) — o lote foi concluído; isto é ressalva, não erro.
          </span>
        </div>
      )}

      {resumo && <ResumoLote resumo={resumo} />}
    </div>
  )
}
