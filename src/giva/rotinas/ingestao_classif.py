"""Ingestão da base de NCM vigente a partir do JSON do Classif/Siscomex
(Fase 5 — operação da base). Substitui o seed de demonstração (migration 0003)
pela base oficial completa.

Rodar:

    python -m giva.rotinas.ingestao_classif [caminho.json]

Sem argumento, usa o snapshot versionado em `dados/classif/` (fonte oficial,
público — não carrega dado de cliente, RNF-02). A operação é um **full refresh**
do vigente numa única transação: registra a `carga` (proveniência: hash do
arquivo + data de coleta, §3.2), limpa `ncm_vigente` e recarrega. `ncm_historico`
e `ncm_correlacao` (redações de época/correlação SH) NÃO são tocados aqui — têm
sua própria trilha (export histórico do Classif).

Decisão GIVA §2: a fonte de NCM é o Classif (JSON máquina-legível), não a TIPI.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import psycopg

from giva.config import dsn_psycopg
from giva.ncm.carga import carregar_snapshot_vigente, sha256_arquivo

# Snapshot oficial versionado no repositório (raiz do projeto / dados/classif).
_SNAPSHOT_PADRAO = (
    Path(__file__).resolve().parents[3]
    / "dados" / "classif" / "nomenclatura_vigente_2026-07-02.json"
)


def _data_coleta(doc: dict[str, Any], caminho: Path) -> date:
    """Data de coleta = a que o Classif declara ('Vigente em dd/mm/aaaa'); se
    ausente, a data de modificação do arquivo. Nunca `date.today()` (quebraria a
    reprodutibilidade — RNF-04)."""
    marca = str(doc.get("Data_Ultima_Atualizacao_NCM", ""))
    for token in marca.replace("Vigente em", "").strip().split():
        try:
            return datetime.strptime(token, "%d/%m/%Y").date()
        except ValueError:
            continue
    return datetime.fromtimestamp(caminho.stat().st_mtime, tz=UTC).date()


def ingerir(con: psycopg.Connection[Any], caminho: Path) -> tuple[int, int]:
    """Full refresh de `ncm_vigente` a partir do snapshot em `caminho`.
    Devolve (carga_id, n_ncm). Não faz commit — quem chama controla a transação."""
    doc: dict[str, Any] = json.loads(caminho.read_text(encoding="utf-8"))
    with con.cursor() as cur:
        cur.execute("DELETE FROM ncm_vigente")
    return carregar_snapshot_vigente(
        con,
        doc,
        arquivo=str(caminho),
        hash_arquivo=sha256_arquivo(str(caminho)),
        data_coleta=_data_coleta(doc, caminho),
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    caminho = Path(args[0]) if args else _SNAPSHOT_PADRAO
    if not caminho.exists():
        print(f"snapshot não encontrado: {caminho}", file=sys.stderr)
        return 2
    with psycopg.connect(dsn_psycopg()) as con:
        carga_id, n = ingerir(con, caminho)
        con.commit()
    print(f"ncm_vigente recarregado: {n} códigos (carga_id={carga_id}) de {caminho.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
