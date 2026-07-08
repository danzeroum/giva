import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useDica } from '../components/ComDica'
import { Selo } from '../components/Selo'
import { useMenuGlobal } from '../components/useMenuGlobal'
import { atualizarUf, listarUfs, type StatusValidacao, type Uf } from '../api/operacao'
import { VALIDACAO_OPCOES, validacaoInfo } from '../data/copy'
import { DEMO_UFS } from '../data/demo'
import { FAROL } from '../data/statuses'
import { useApp } from '../store/app'
import styles from './operacao.module.css'

function fmtAliquota(v: string | number): string {
  const n = Number(v)
  return Number.isNaN(n) ? String(v) : `${n.toFixed(1).replace('.', ',')}%`
}

export function B2() {
  const demo = useApp((s) => s.demo)
  const qc = useQueryClient()
  const { dicaHandlers, tooltip } = useDica()
  const { menu, setMenu, alternar } = useMenuGlobal()

  const { data: ufs, isLoading } = useQuery({
    queryKey: ['ufs', demo],
    queryFn: () => (demo ? Promise.resolve(DEMO_UFS) : listarUfs()),
  })

  const validar = useMutation({
    mutationFn: async (v: { uf: string; status: StatusValidacao }) => {
      if (!demo) await atualizarUf(v.uf, v.status)
    },
    onSuccess: (_r, v) => {
      setMenu(null)
      if (demo) {
        qc.setQueryData<Uf[]>(['ufs', demo], (old) =>
          old?.map((u) => (u.uf === v.uf ? { ...u, status_validacao: v.status } : u)),
        )
      } else {
        qc.invalidateQueries({ queryKey: ['ufs'] })
      }
    },
  })

  return (
    <div className={styles.wrap}>
      <h1 className={styles.h1}>Alíquotas por estado</h1>
      <p className={styles.sub}>
        A alíquota de ICMS que o GIVA usa para cada estado. Clique no selo para marcar o que você já
        conferiu na fonte oficial.
      </p>

      <div className={`${styles.card} ${styles.cardVisivel}`}>
        {isLoading ? (
          <div className={styles.vazio}>Carregando…</div>
        ) : !ufs || ufs.length === 0 ? (
          <div className={styles.vazio}>Nenhuma alíquota registrada.</div>
        ) : (
          <table className={styles.tabela}>
            <thead>
              <tr>
                <th>UF</th>
                <th>Alíquota interna</th>
                <th>Vigência</th>
                <th>Validação</th>
                <th>Fonte</th>
              </tr>
            </thead>
            <tbody>
              {ufs.map((u) => {
                const info = validacaoInfo(u.status_validacao)
                return (
                  <tr key={u.uf}>
                    <td className={styles.mono} style={{ fontWeight: 600 }}>{u.uf}</td>
                    <td className={styles.mono}>{fmtAliquota(u.aliquota_modal)}</td>
                    <td className={styles.faint}>desde {u.vigencia_inicio.slice(0, 7)}</td>
                    <td style={{ position: 'relative' }}>
                      <Selo
                        farol={info.farol}
                        label={info.label}
                        caret
                        dica="Clique para mudar a situação: já conferi na fonte oficial, fontes não batem etc."
                        dicaHandlers={dicaHandlers}
                        onClick={alternar(`uf${u.uf}`)}
                      />
                      {menu === `uf${u.uf}` && (
                        <div className={`${styles.menu} ${styles.menuEsquerda}`} role="menu">
                          {VALIDACAO_OPCOES.map((chave) => {
                            const opt = validacaoInfo(chave)
                            return (
                              <button
                                key={chave}
                                type="button"
                                className={styles.menuItem}
                                onClick={() => {
                                  if (chave !== u.status_validacao) validar.mutate({ uf: u.uf, status: chave })
                                  else setMenu(null)
                                }}
                              >
                                <span className={styles.dotMenu} style={{ background: FAROL[opt.farol].dot }} />
                                {opt.label}
                              </button>
                            )
                          })}
                        </div>
                      )}
                    </td>
                    <td className={styles.faint}>{u.fonte_compilada}</td>
                  </tr>
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
