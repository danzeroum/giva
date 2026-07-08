import { useEffect, useState } from 'react'

// Menus suspensos do Bloco B: um aberto por vez (estado global por tela).
// Clique em qualquer lugar fecha (listener no document); o gatilho faz
// stopPropagation para não fechar o menu que acabou de abrir. Espelha o padrão
// do protótipo (README §Interações).
export function useMenuGlobal() {
  const [menu, setMenu] = useState<string | null>(null)

  useEffect(() => {
    if (!menu) return
    const fechar = () => setMenu(null)
    document.addEventListener('click', fechar)
    return () => document.removeEventListener('click', fechar)
  }, [menu])

  /** Handler para o botão-gatilho: alterna o menu `id` e barra a propagação. */
  const alternar = (id: string) => (e: React.MouseEvent) => {
    e.stopPropagation()
    setMenu((m) => (m === id ? null : id))
  }

  return { menu, setMenu, alternar }
}
