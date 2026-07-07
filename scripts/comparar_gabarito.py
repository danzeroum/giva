"""Compara a saída do GIVA para a planilha-teste contra o gabarito esperado.

Ferramenta de validação (não roda no CI — depende de dois `.xlsx` externos).
Sobe a base real do Classif antes de comparar; use um banco de dev.

    export DATABASE_URL=postgresql+psycopg://giva@/giva
    alembic upgrade head
    python -m giva.rotinas.ingestao_classif --promover
    python scripts/comparar_gabarito.py 05-planilha-teste.xlsx 06-gabarito.xlsx

Compara as colunas OBJETIVAS (categoria, confiança, alíquota, divergência) e
imprime a taxa de acerto por coluna + amostras de divergência.
"""

from __future__ import annotations

import collections
import sys
from pathlib import Path

import openpyxl
import psycopg

from giva.aliquota.repositorio_sql import RepositorioAliquotaSQL
from giva.aliquota.resolvedor import ResolutorAliquota
from giva.categoria.categorizador import Categorizador
from giva.categoria.repositorio_sql import RepositorioCategoriaSQL
from giva.config import dsn_psycopg
from giva.ncm.repositorio_sql import RepositorioNCMSQL
from giva.ncm.resolvedor import ResolutorNCM
from giva.pipeline.etapas import (
    EtapaAliquota,
    EtapaCategoria,
    EtapaNCM,
    EtapaNormalizacao,
    EtapaSimilaridade,
)
from giva.pipeline.leitor import ler_planilha
from giva.pipeline.modelo import LinhaLote
from giva.pipeline.pipeline import Pipeline
from giva.similaridade.avaliador import AvaliadorSimilaridade
from giva.similaridade.repositorio_sql import RepositorioParametrosSQL


def _fmt_aliquota(linha: LinhaLote) -> str:
    e = linha.enriquecimento
    if e.get("status_aliquota") == "pendente_validacao_uf":
        return "REQUER VALIDACAO MANUAL"
    valor = e.get("aliquota_icms_interna")
    if not valor:
        return ""
    f = float(valor)
    return f"{int(f)}%" if f == int(f) else f"{str(f).replace('.', ',')}%"


def _categoria(linha: LinhaLote) -> str:
    e = linha.enriquecimento
    cat = e.get("categoria_macro", "")
    if cat == "Indefinido":
        motivo = linha.proveniencia.get("categoria", {}).get("motivo_indefinido")
        if motivo == "ambiguo":
            return "Indefinido — ambiguo"
        if motivo == "sem_match":
            return "Indefinido — sem match"
    return cat


def _divergencia(linha: LinhaLote) -> str:
    return {"ok": "nenhuma", "alerta_similaridade": "leve", "requer_revisao": "forte"}.get(
        linha.enriquecimento.get("status_descricao", ""), "-"
    )


def _norm(x: object) -> str:
    return " ".join(str(x).strip().lower().split())


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("uso: comparar_gabarito.py <entrada.xlsx> <gabarito.xlsx>", file=sys.stderr)
        return 2
    entrada, gabarito = Path(argv[0]), Path(argv[1])
    lote = ler_planilha(entrada.read_bytes(), entrada.name)

    aba = openpyxl.load_workbook(gabarito, data_only=True)["Gabarito"]
    linhas_gab = list(aba.iter_rows(values_only=True))
    cabec = list(linhas_gab[0])
    esperado = [dict(zip(cabec, r, strict=False)) for r in linhas_gab[1:]]

    con = psycopg.connect(dsn_psycopg())
    pipe = Pipeline([
        EtapaNormalizacao(),
        EtapaNCM(ResolutorNCM(RepositorioNCMSQL(con))),
        EtapaAliquota(ResolutorAliquota(RepositorioAliquotaSQL(con))),
        EtapaCategoria(Categorizador(RepositorioCategoriaSQL(con))),
        EtapaSimilaridade(AvaliadorSimilaridade(RepositorioParametrosSQL(con))),
    ])
    linhas = pipe.processar(lote.linhas)

    acertos: collections.Counter[str] = collections.Counter()
    amostras: dict[str, list[str]] = collections.defaultdict(list)
    for linha, g in zip(linhas, esperado, strict=False):
        checks = {
            "categoria": (_categoria(linha), g.get("categoria_macro", "")),
            "confianca": (linha.enriquecimento.get("confianca_categorizacao", ""),
                          g.get("confianca_categorizacao", "")),
            "aliquota": (_fmt_aliquota(linha), g.get("aliquota_icms_interna", "")),
            "divergencia": (_divergencia(linha), g.get("divergencia_descricao", "")),
        }
        for coluna, (obtido, esper) in checks.items():
            if _norm(obtido) == _norm(esper):
                acertos[coluna] += 1
            elif len(amostras[coluna]) < 5:
                amostras[coluna].append(f"{linha.bruto_ncm!r}: giva={obtido!r} gab={esper!r}")

    n = len(linhas)
    print(f"comparadas {n} linhas")
    for coluna in ("categoria", "confianca", "aliquota", "divergencia"):
        print(f"  {coluna:12}: {acertos[coluna]}/{n} ({100 * acertos[coluna] // n}%)")
        for a in amostras[coluna]:
            print(f"       x {a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
