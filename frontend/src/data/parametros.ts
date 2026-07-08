// Copy dos "Ajustes do sistema" (B3) — texto de leigo em três níveis por
// parâmetro (rótulo humano, descrição, efeito prático). É camada de EXIBIÇÃO:
// o valor de cada parâmetro vem do backend (GET /parametros); estes textos
// (validados com o usuário) são fixos e mapeados pelo nome técnico. Copiados
// literalmente do protótipo de referência.
export interface ParametroCopy {
  nome: string
  rotulo: string
  descricao: string
  efeito: string
}

export const PARAMETROS_COPY: Record<string, ParametroCopy> = {
  t_ok: {
    nome: 't_ok',
    rotulo: 'Rigor da comparação de descrições',
    descricao:
      'O quanto a descrição da planilha precisa parecer com a descrição oficial do NCM para a linha passar sem aviso.',
    efeito:
      'Aumentar = mais linhas recebem o aviso "conferir similaridade". Diminuir = menos avisos, mas erros podem passar.',
  },
  t_rev: {
    nome: 't_rev',
    rotulo: 'Limite para exigir revisão humana',
    descricao:
      'Abaixo desta semelhança, a linha é marcada em vermelho como "requer revisão" e vai para a fila do analista.',
    efeito:
      'Aumentar = mais linhas paradas para revisão manual. Diminuir = mais linhas seguem só com aviso amarelo.',
  },
  categoria_versao_vigente: {
    nome: 'categoria_versao_vigente',
    rotulo: 'Versão do mapa de categorias',
    descricao:
      'Qual versão das regras NCM→categoria (as 18 categorias EFD) o sistema usa ao classificar as planilhas.',
    efeito:
      'Trocar a versão muda a categoria sugerida em novos processamentos. Lotes antigos não são alterados.',
  },
  expurgo_lotes_meses: {
    nome: 'expurgo_lotes_meses',
    rotulo: 'Tempo de guarda dos arquivos (meses)',
    descricao:
      'Por quantos meses os arquivos enviados pelos analistas ficam guardados antes de serem apagados (LGPD).',
    efeito:
      'Aumentar = arquivos disponíveis por mais tempo. Diminuir = limpeza mais cedo; downloads antigos expiram.',
  },
}

/** Ordem de exibição dos parâmetros em B3 (a mesma do protótipo). */
export const PARAMETROS_ORDEM = ['t_ok', 't_rev', 'categoria_versao_vigente', 'expurgo_lotes_meses']

export function parametroCopy(nome: string): ParametroCopy {
  return PARAMETROS_COPY[nome] ?? { nome, rotulo: nome, descricao: '', efeito: '' }
}

// As 18 categorias EFD (protótipo) — usadas nos selects de B4/B5 quando o modo
// demo está ligado. No modo real, buscar de `categoria` no banco.
export const CATEGORIAS_EFD = [
  'Material de manutenção', 'Peça de máquina', 'Material elétrico', 'Material de limpeza',
  'EPI', 'Material de escritório e informática', 'Gás', 'Produto químico', 'Ferramentas',
  'Combustível e lubrificante', 'Material de construção', 'Serviço', 'Alimentação',
  'Material de embalagem', 'Brindes', 'Material de jardinagem', 'Material de laboratório',
  'Indefinido',
]
