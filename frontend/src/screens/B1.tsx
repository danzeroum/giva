import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { MoreHorizontal } from 'lucide-react'
import { Fragment, useState } from 'react'
import { useDica } from '../components/ComDica'
import { Selo } from '../components/Selo'
import { useMenuGlobal } from '../components/useMenuGlobal'
import { type Carga, diffCarga, listarCargas, promoverCarga, rejeitarCarga } from '../api/operacao'
import { type CargaDemo, DEMO_CARGAS, type DiffAmostraItem } from '../data/demo'
import { useApp } from '../store/app'
import styles from './operacao.module.css'

interface DiffNormalizado {
  novos: number
  alterados: number
  removidos: number
  amostra: DiffAmostraItem[]
}

const TIPO_LABEL: Record<DiffAmostraItem['tipo'], string> = {
  novo: '+ novo',
  alterado: '~ alterado',
  removido: '− removido',
}
const TIPO_CLASSE: Record<DiffAmostraItem['tipo'], string> = {
  novo: styles.mudNovo,
  alterado: styles.mudAlterado,
  removido: styles.mudRemovido,
}

function seloCarga(c: Carga): { farol: 'verde' | 'amarelo' | 'cinza'; label: string } {
  if (c.status === 'staging') return { farol: 'amarelo', label: 'aguardando aprovação' }
  if (c.status === 'promovida') return { farol: 'verde', label: `aprovada · ${c.promovido_por ?? ''}`.trim() }
  return { farol: 'cinza', label: 'descartada' }
}

export function B1() {
  const demo = useApp((s) => s.demo)
  const qc = useQueryClient()
  const { dicaHandlers, tooltip } = useDica()
  const { menu, setMenu, alternar } = useMenuGlobal()
  const [diffAberto, setDiffAberto] = useState<number | null>(null)
  const [confirmando, setConfirmando] = useState<number | null>(null)

  const { data: cargas, isLoading } = useQuery({
    queryKey: ['cargas', demo],
    queryFn: () => (demo ? Promise.resolve(DEMO_CARGAS) : listarCargas()),
  })

  // Diff no modo real (o demo traz o detalhe embutido em `diffDemo`).
  const { data: diffReal } = useQuery({
    queryKey: ['diff', diffAberto],
    queryFn: () => diffCarga(diffAberto as number),
    enabled: !demo && diffAberto !== null,
  })

  const aposMutacao =
    (fn: (lista: CargaDemo[], id: number) => CargaDemo[]) => (_r: unknown, id: number) => {
      setConfirmando(null)
      setDiffAberto(null)
      setMenu(null)
      if (demo) {
        qc.setQueryData<CargaDemo[]>(['cargas', demo], (old) => (old ? fn(old, id) : old))
      } else {
        qc.invalidateQueries({ queryKey: ['cargas'] })
      }
    }

  const promover = useMutation({
    mutationFn: (id: number) => (demo ? Promise.resolve() : promoverCarga(id)),
    onSuccess: aposMutacao((lista, id) =>
      lista.map((c) => (c.id === id ? { ...c, status: 'promovida', promovido_por: 'M. Ferraz' } : c)),
    ),
  })
  const rejeitar = useMutation({
    mutationFn: (id: number) => (demo ? Promise.resolve() : rejeitarCarga(id)),
    onSuccess: aposMutacao((lista, id) =>
      lista.map((c) => (c.id === id ? { ...c, status: 'rejeitada' } : c)),
    ),
  })

  const clicarAprovar = (id: number) => {
    if (confirmando !== id) {
      setConfirmando(id)
      setDiffAberto(id)
      setMenu(null)
      return
    }
    promover.mutate(id)
  }

  const normalizar = (c: CargaDemo): DiffNormalizado | null => {
    if (c.diffDemo) return c.diffDemo
    if (!demo && diffReal && diffReal.carga_id === c.id) {
      return {
        novos: diffReal.novos,
        alterados: diffReal.alterados,
        removidos: diffReal.removidos,
        amostra: [
          ...diffReal.amostra_novos.map((codigo) => ({ codigo, tipo: 'novo' as const, detalhe: '—' })),
          ...diffReal.amostra_alterados.map((codigo) => ({ codigo, tipo: 'alterado' as const, detalhe: '—' })),
          ...diffReal.amostra_removidos.map((codigo) => ({ codigo, tipo: 'removido' as const, detalhe: '—' })),
        ],
      }
    }
    return null
  }

  const fmtData = (iso: string) => {
    const d = new Date(iso)
    return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString('pt-BR')
  }

  return (
    <div className={styles.wrap}>
      <h1 className={styles.h1}>Atualizações da base</h1>
      <p className={styles.sub}>
        Quando chega uma tabela nova (códigos NCM ou alíquotas), ela espera aqui. Nada muda no
        sistema até você aprovar.
      </p>

      <div className={`${styles.card} ${styles.cardVisivel}`}>
        {isLoading ? (
          <div className={styles.vazio}>Carregando…</div>
        ) : !cargas || cargas.length === 0 ? (
          <div className={styles.vazio}>Nenhuma atualização registrada.</div>
        ) : (
          <table className={styles.tabela}>
            <thead>
              <tr>
                <th>Fonte</th>
                <th>Arquivo</th>
                <th>Coleta</th>
                <th>Status</th>
                <th aria-label="ações" />
              </tr>
            </thead>
            <tbody>
              {cargas.map((c) => {
                const staging = c.status === 'staging'
                const selo = seloCarga(c)
                const diff = diffAberto === c.id ? normalizar(c) : null
                return (
                  <Fragment key={c.id}>
                    <tr>
                      <td>{c.fonte}</td>
                      <td className={styles.mono}>{c.arquivo_bruto}</td>
                      <td className={styles.faint}>{fmtData(c.data_coleta)}</td>
                      <td>
                        <Selo farol={selo.farol} label={selo.label} />
                      </td>
                      <td className={styles.acaoCol}>
                        {staging && (
                          <>
                            <button
                              type="button"
                              className={styles.mais}
                              aria-label="Ações da atualização"
                              data-dica="Ações desta atualização: ver o que muda, aprovar ou descartar."
                              {...dicaHandlers}
                              onClick={alternar(`carga${c.id}`)}
                            >
                              <MoreHorizontal size={16} strokeWidth={2} />
                            </button>
                            {menu === `carga${c.id}` && (
                              <div className={`${styles.menu} ${styles.menuDireita}`} role="menu">
                                <button
                                  type="button"
                                  className={styles.menuItem}
                                  onClick={() => setDiffAberto(diffAberto === c.id ? null : c.id)}
                                >
                                  {diffAberto === c.id ? 'Fechar comparação' : 'Ver o que muda'}
                                </button>
                                <button type="button" className={styles.menuItemVerde} onClick={() => clicarAprovar(c.id)}>
                                  Aprovar e aplicar
                                </button>
                                <button type="button" className={styles.menuItemVermelho} onClick={() => rejeitar.mutate(c.id)}>
                                  Descartar
                                </button>
                              </div>
                            )}
                          </>
                        )}
                      </td>
                    </tr>
                    {diff && (
                      <tr>
                        <td colSpan={5} style={{ padding: '0 14px 16px', borderTop: 'none' }}>
                          <div className={styles.diffPainel}>
                            <div className={styles.diffCabeca}>
                              <span className={styles.diffTitulo}>O que muda se você aprovar</span>
                              <span className={`${styles.pill} ${styles.pillVerde}`}>+{diff.novos} novos</span>
                              <span className={`${styles.pill} ${styles.pillAmarelo}`}>{diff.alterados} alterados</span>
                              <span className={`${styles.pill} ${styles.pillVermelho}`}>−{diff.removidos} removidos</span>
                            </div>
                            {diff.amostra.length > 0 && (
                              <table className={styles.diffTabela}>
                                <thead>
                                  <tr>
                                    <th>NCM</th>
                                    <th>Mudança</th>
                                    <th>Antes → depois</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {diff.amostra.map((d) => (
                                    <tr key={`${d.tipo}-${d.codigo}`}>
                                      <td className={styles.mono}>{d.codigo}</td>
                                      <td className={TIPO_CLASSE[d.tipo]}>{TIPO_LABEL[d.tipo]}</td>
                                      <td>{d.detalhe}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            )}
                            <div className={styles.diffAcoes}>
                              <button type="button" className={styles.btnPrim} onClick={() => clicarAprovar(c.id)}>
                                {confirmando === c.id ? 'Tem certeza? Confirmar' : 'Aprovar e aplicar'}
                              </button>
                              <button type="button" className={styles.btnSec} onClick={() => rejeitar.mutate(c.id)}>
                                Descartar
                              </button>
                              <span className={styles.diffNota}>
                                Tudo é aplicado de uma vez e fica registrado — dá para saber depois quem aprovou e quando.
                              </span>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
      {tooltip}
    </div>
  )
}
