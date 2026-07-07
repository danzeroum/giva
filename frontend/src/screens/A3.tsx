import { useMutation, useQueryClient } from '@tanstack/react-query'
import { FileSpreadsheet, Upload, X } from 'lucide-react'
import { type ChangeEvent, useState } from 'react'
import { ApiError } from '../api/client'
import { enviarLote } from '../api/lotes'
import { useApp } from '../store/app'
import styles from './A3.module.css'

const ROTULO_PASSO = { select: 'Selecionar', mapping: 'Mapear colunas', preview: 'Prévia e processar' } as const

// Colunas mínimas esperadas na planilha de entrada.
const COLUNAS_MINIMAS = ['NCM', 'Período', 'Descrição', 'UF']

export function A3() {
  const {
    uploadStep, arquivoSelecionado, colunasDetectadas,
    pickFile, voltarSelecao, confirmMap, loteEnviado, go, demo,
  } = useApp()
  const [erro, setErro] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: enviarLote,
    onSuccess: (lote) => {
      void queryClient.invalidateQueries({ queryKey: ['lotes'] })
      loteEnviado(lote.id)
    },
    onError: (err) => {
      setErro(err instanceof ApiError ? err.message : 'Falha ao enviar o arquivo.')
    },
  })

  async function aoSelecionar(e: ChangeEvent<HTMLInputElement>) {
    const arquivo = e.target.files?.[0]
    if (!arquivo) return
    setErro(null)
    let colunas: string[] = []
    // Só conseguimos ler o cabeçalho de .csv no navegador; .xlsx é binário e o
    // parsing acontece no backend (ou numa fase futura com uma lib dedicada).
    if (/\.csv$/i.test(arquivo.name)) {
      const texto = await arquivo.text()
      const primeiraLinha = texto.split(/\r?\n/, 1)[0] ?? ''
      colunas = primeiraLinha.split(/[,;]/).map((c) => c.trim()).filter(Boolean)
    }
    pickFile(arquivo, colunas)
  }

  function aoProcessar() {
    if (!arquivoSelecionado) return
    setErro(null)
    // Modo demo: sem backend, "processar" leva ao lote de demonstração que exibe
    // o progresso/polling (A4).
    if (demo) {
      loteEnviado(2)
      return
    }
    mutation.mutate(arquivoSelecionado)
  }

  return (
    <div className={styles.wrap}>
      <header className={styles.head}>
        <button type="button" className={styles.voltar} onClick={() => go('a2')}>← Meus lotes</button>
        <h1 className={styles.h1}>Enviar planilha</h1>
      </header>

      <ol className={styles.passos}>
        {(Object.keys(ROTULO_PASSO) as (keyof typeof ROTULO_PASSO)[]).map((p, i) => (
          <li key={p} className={uploadStep === p ? styles.passoAtivo : undefined}>
            {i + 1}. {ROTULO_PASSO[p]}
          </li>
        ))}
      </ol>

      {uploadStep === 'select' && (
        <div className={styles.card}>
          <FileSpreadsheet size={32} strokeWidth={1.6} />
          <p>Selecione um arquivo <span className="mono">.csv</span> ou <span className="mono">.xlsx</span> com as colunas NCM, Período, Descrição e UF.</p>
          <label className={styles.inputLabel}>
            <Upload size={15} strokeWidth={2} /> Escolher arquivo
            <input
              type="file"
              accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              onChange={aoSelecionar}
              className={styles.input}
            />
          </label>
        </div>
      )}

      {uploadStep === 'mapping' && arquivoSelecionado && (
        <div className={styles.card}>
          <h2 className={styles.h2}>Mapear colunas</h2>
          {colunasDetectadas.length === 0 ? (
            <p className={styles.nota}>
              Cabeçalho não lido automaticamente (arquivo .xlsx ou sem cabeçalho legível). O
              mapeamento e a validação completa (colunas mínimas: {COLUNAS_MINIMAS.join(', ')})
              acontecem ao processar.
            </p>
          ) : (
            <>
              <p className={styles.notaEsq}>Colunas detectadas no cabeçalho — confira o mapeamento:</p>
              <ul className={styles.listaColunas}>
                {colunasDetectadas.map((c) => {
                  const casa = COLUNAS_MINIMAS.some((m) => c.toLowerCase().includes(m.toLowerCase()))
                  return (
                    <li key={c} className={casa ? styles.colOk : undefined}>{c}</li>
                  )
                })}
              </ul>
              <p className={styles.nota}>
                A validação completa (nomes aceitos, colunas mínimas: {COLUNAS_MINIMAS.join(', ')})
                acontece ao processar.
              </p>
            </>
          )}
          <div className={styles.acoes}>
            <button type="button" className={styles.btnSec} onClick={voltarSelecao}>Voltar</button>
            <button type="button" className={styles.btnPrim} onClick={confirmMap}>Continuar</button>
          </div>
        </div>
      )}

      {uploadStep === 'preview' && arquivoSelecionado && (
        <div className={styles.card}>
          <h2 className={styles.h2}>Pronto para processar</h2>
          <div className={styles.arquivoInfo}>
            <FileSpreadsheet size={18} strokeWidth={1.8} />
            <span className="mono">{arquivoSelecionado.name}</span>
            <span className={styles.tamanho}>{(arquivoSelecionado.size / 1024).toFixed(1)} KB</span>
          </div>
          {erro && <p className={styles.erro}>{erro}</p>}
          <div className={styles.acoes}>
            <button type="button" className={styles.btnSec} onClick={voltarSelecao} disabled={mutation.isPending}>
              <X size={15} strokeWidth={2} /> Cancelar
            </button>
            <button type="button" className={styles.btnPrim} onClick={aoProcessar} disabled={mutation.isPending}>
              <Upload size={15} strokeWidth={2} /> {mutation.isPending ? 'Enviando…' : 'Processar'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
