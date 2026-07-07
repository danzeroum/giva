// Ressalvas obrigatórias, sempre visíveis (nunca em rodapé ignorável) —
// renderizadas pelo componente <Ressalva>. A ressalva da CATEGORIA é o disclaimer
// exigido no brief e deve aparecer junto da coluna de categoria e na prévia de
// saída: "categoria é sugestão operacional, não substitui enquadramento fiscal".
export const RESSALVAS: readonly string[] = [
  'A alíquota interna apresentada é a regra geral do estado no período; tratamentos específicos por produto (ex.: alimentos, medicamentos, cesta básica) não estão verificados nesta versão.',
  'A categoria macro é uma sugestão operacional para análise de gastos; não substitui o enquadramento fiscal nem constitui classificação fiscal.',
]

// Índice estável das ressalvas (evita "número mágico" nas chamadas <Ressalva only>).
export const RESSALVA_ALIQUOTA = 0
export const RESSALVA_CATEGORIA = 1
