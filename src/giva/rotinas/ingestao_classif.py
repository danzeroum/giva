"""Ingestão da base de NCM vigente a partir do JSON do Classif/Siscomex
(Fase 5 — operação da base).

Rodar:

    python -m giva.rotinas.ingestao_classif [caminho.json] [--promover]

Sem argumento, usa o snapshot versionado em `dados/classif/` (fonte oficial,
público — não carrega dado de cliente, RNF-02).

Por padrão a carga entra na **sala de espera** (`ncm_vigente_staging`,
`carga.status='staging'`) e o comando mostra o diff contra a produção — nada
afeta o motor até um humano promover (revisão antes de valer). Com `--promover`,
a carga é promovida na hora (bootstrap/dev). `ncm_historico`/`ncm_correlacao`
têm sua própria trilha (export histórico do Classif).

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
from giva.ncm.carga import sha256_arquivo
from giva.ncm.staging import carregar_staging, diff_carga, promover_carga

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


def ingerir_staging(con: psycopg.Connection[Any], caminho: Path) -> tuple[int, int]:
    """Carrega o snapshot de `caminho` para a sala de espera (staging).
    Devolve (carga_id, n_ncm). Não faz commit."""
    doc: dict[str, Any] = json.loads(caminho.read_text(encoding="utf-8"))
    return carregar_staging(
        con,
        doc,
        arquivo=str(caminho),
        hash_arquivo=sha256_arquivo(str(caminho)),
        data_coleta=_data_coleta(doc, caminho),
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    promover = "--promover" in args
    posicionais = [a for a in args if not a.startswith("--")]
    caminho = Path(posicionais[0]) if posicionais else _SNAPSHOT_PADRAO
    if not caminho.exists():
        print(f"snapshot não encontrado: {caminho}", file=sys.stderr)
        return 2

    with psycopg.connect(dsn_psycopg()) as con:
        carga_id, n = ingerir_staging(con, caminho)
        diff = diff_carga(con, carga_id)
        print(
            f"carga {carga_id} em staging: {n} códigos de {caminho.name} | "
            f"vs produção: +{diff.novos} novos, -{diff.removidos} removidos, "
            f"~{diff.alterados} alterados"
        )
        if promover:
            promovidos = promover_carga(con, carga_id, por="ingestao-cli")
            con.commit()
            print(f"carga {carga_id} PROMOVIDA: {promovidos} códigos em produção.")
        else:
            con.commit()
            print(
                f"Revise e promova: POST /cargas/{carga_id}/promover (ou rode com "
                f"--promover)."
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
