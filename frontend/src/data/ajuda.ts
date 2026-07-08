// Camada de ajuda — textos do tour guiado e do manual prático.
//
// Copiados LITERALMENTE do protótipo de referência (constantes TOUR e MANUAL em
// docs/design_handoff_giva_operacao/GIVA Operação.dc.html). Validados com o
// usuário — não reescrever.
import type { Screen } from '../store/app'

export interface TourPasso {
  titulo: string
  texto: string
  screen: Screen
}

// 8 passos; cada um navega para a tela correspondente (b1→…→consultas→manual).
export const TOUR: TourPasso[] = [
  { titulo: 'Bem-vindo à operação do GIVA', texto: 'Aqui você cuida da base de dados que confere as planilhas dos analistas. São 6 áreas — vamos passar por cada uma. Você pode sair do tour a qualquer momento.', screen: 'b1' },
  { titulo: 'Atualizações da base', texto: 'Quando chega uma tabela nova de códigos ou alíquotas, ela espera aqui. Você vê exatamente o que muda antes de aprovar — nada entra no sistema sem o seu OK.', screen: 'b1' },
  { titulo: 'Alíquotas por estado', texto: 'A alíquota de ICMS de cada estado, com a fonte de onde veio. Conferiu no site da SEFAZ? Clique no selo colorido e marque como conferida.', screen: 'b2' },
  { titulo: 'Ajustes do sistema', texto: 'Controles de rigor da análise, em linguagem simples: cada um explica o que acontece se você aumentar ou diminuir. Toda mudança fica registrada.', screen: 'b3' },
  { titulo: 'Correções de categoria', texto: 'Um produto caiu na categoria errada? Corrija aqui uma vez e o sistema acerta em todos os próximos processamentos.', screen: 'b4' },
  { titulo: 'Contestações', texto: 'Quando um analista discorda de um resultado, o aviso chega aqui. Use o botão “Encaminhar” para corrigir a base ou responder.', screen: 'b5' },
  { titulo: 'Consultas prontas', texto: 'Perguntas frequentes à base, como filtros de planilha: escolha, preencha, execute. E todo resultado tem o botão “Copiar p/ Excel”.', screen: 'consultas' },
  { titulo: 'Pronto!', texto: 'Dica final: passe o mouse sobre qualquer botão para ver uma explicação rápida. E o Manual prático (menu Ajuda, à esquerda) tem o passo a passo de cada tarefa.', screen: 'manual' },
]

export interface ManualSecao {
  key: string
  titulo: string
  passos: string[]
}

// 6 acordeões; um aberto por vez.
export const MANUAL: ManualSecao[] = [
  { key: 'aprovar', titulo: 'Aprovar uma atualização da base', passos: [
    'Abra “Atualizações da base” no menu à esquerda.',
    'Na linha com o selo “aguardando aprovação”, clique no botão ⋯.',
    'Clique em “Ver o que muda” e confira os números: novos, alterados e removidos.',
    'Se estiver de acordo, clique “Aprovar e aplicar” e confirme. Se algo estiver errado, clique “Descartar” — nada é alterado.',
    'A aprovação fica registrada com seu nome e a data.' ] },
  { key: 'aliquota', titulo: 'Conferir a alíquota de um estado', passos: [
    'Abra “Alíquotas por estado”.',
    'Localize o estado — a coluna “Fonte” mostra de onde o valor veio.',
    'Confira o valor no site oficial da SEFAZ do estado.',
    'Clique no selo colorido da linha e escolha a situação certa (ex.: “conferida na fonte oficial”).',
    'Selos vermelhos (“fontes não batem”) são os mais urgentes.' ] },
  { key: 'categoria', titulo: 'Corrigir a categoria de um produto', passos: [
    'Abra “Correções de categoria” e clique em “Nova correção”.',
    'Informe o código NCM completo (8 dígitos).',
    'Escolha a categoria certa na lista.',
    'Escreva o motivo — é obrigatório, para que qualquer pessoa entenda depois.',
    'Clique “Salvar correção”. Vale para todos os próximos processamentos; planilhas antigas não mudam.' ] },
  { key: 'contestacao', titulo: 'Responder uma contestação de analista', passos: [
    'Abra “Contestações” — as abertas têm selo amarelo.',
    'Leia o texto do analista e clique em “Encaminhar ▾”.',
    'Escolha: corrigir a categoria, mandar conferir a alíquota do estado, ou só responder.',
    'Escreva a resolução e clique “Resolver”. O analista vê sua resposta.' ] },
  { key: 'consultar', titulo: 'Consultar a base e levar para o Excel', passos: [
    'Abra “Consultas prontas” e escolha a pergunta à esquerda.',
    'Preencha os campos (ex.: o código NCM ou o estado).',
    'Clique “Executar” — o resultado aparece como uma tabela.',
    'Clique “Copiar p/ Excel”, abra sua planilha e cole com Ctrl+V.' ] },
  { key: 'selos', titulo: 'O que significam as cores dos selos', passos: [
    'Verde — tudo certo, ou já conferido por alguém.',
    'Amarelo — atenção: algo espera a sua ação ou conferência.',
    'Vermelho — problema: fontes não batem, ou a linha precisa de revisão.',
    'Cinza — ainda não conferido.',
    'A cor nunca vem sozinha: o texto do selo sempre diz o que é.' ] },
]
