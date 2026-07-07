"""Armazenamento de arquivos de lote — entradas e saídas (Fase 3, ADR-01).

Volume local (sem S3 no volume atual do projeto — ADR-01 já decidiu monólito
de 1 nó): um volume Docker nomeado monta em `DADOS_DIR` tanto na API quanto
no worker (`docker-compose.yml`), então um arquivo gravado por uma request da
API é visível ao worker no mesmo caminho. Caminhos absolutos são gravados em
`lote.arquivo_entrada`/`arquivo_saida` — mesma convenção que os testes do
worker já usam (`Path(arquivo).read_text(...)`), sem mudança de contrato.

Módulo neutro (fora de `api/`): tanto a API (upload síncrono) quanto o worker
(fila) precisam gravar/ler destes diretórios, e o worker não deve depender do
pacote `api`.
"""

from __future__ import annotations

import uuid

from giva.config import diretorio_dados


def salvar_entrada(conteudo: bytes) -> str:
    """Grava o CSV enviado em `entradas/` com um nome único; devolve o
    caminho absoluto para gravar em `lote.arquivo_entrada`."""
    diretorio = diretorio_dados() / "entradas"
    diretorio.mkdir(parents=True, exist_ok=True)
    caminho = diretorio / f"{uuid.uuid4().hex}.csv"
    caminho.write_bytes(conteudo)
    return str(caminho)


def caminho_saida(lote_id: int) -> str:
    """Caminho onde o `.xlsx` de saída de um lote é gravado, em `saidas/`."""
    diretorio = diretorio_dados() / "saidas"
    diretorio.mkdir(parents=True, exist_ok=True)
    return str(diretorio / f"lote_{lote_id}.xlsx")
