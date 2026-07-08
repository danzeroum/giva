/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  // Modo demo (dados fictícios, sem backend). 'true' liga; ausente/qualquer
  // outra coisa = desligado. Produção com API conectada roda com isto desligado.
  readonly VITE_DEMO_MODE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
