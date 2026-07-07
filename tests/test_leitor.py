"""Leitor de entrada — CSV e XLSX pelo mesmo contrato de colunas; NCM ausente
não derruba a linha; despacho por assinatura de arquivo."""

from __future__ import annotations

import io

import pytest

from giva.pipeline.leitor import ColunaAusenteError, ler_csv, ler_planilha, ler_xlsx

_CSV = (
    "NCM,Periodo,Descricao,UF,Centro de Custo\n"
    "8482.10.00,03/2026,Rolamento,SP,CC-1\n"
    ",07/2022,LUVA,SP,CC-2\n"
)


def _xlsx_bytes(cabecalho, linhas):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(cabecalho)
    for r in linhas:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_csv_preserva_colunas_e_mapeia():
    lote = ler_csv(_CSV)
    assert lote.colunas_originais == ["NCM", "Periodo", "Descricao", "UF", "Centro de Custo"]
    assert lote.linhas[0].bruto_ncm == "8482.10.00"
    assert lote.linhas[1].bruto_ncm == ""  # NCM em branco preservado (vira ausente depois)


def test_xlsx_mesmo_contrato_do_csv():
    conteudo = _xlsx_bytes(
        ["NCM", "Periodo", "Descricao", "UF"],
        [["8482.10.00", "03/2026", "Rolamento", "SP"], ["", "07/2022", "LUVA", "SP"]],
    )
    lote = ler_xlsx(conteudo)
    assert lote.colunas_originais == ["NCM", "Periodo", "Descricao", "UF"]
    assert lote.linhas[0].bruto_descricao == "Rolamento"
    assert lote.linhas[1].bruto_ncm == ""


def test_ler_planilha_despacha_por_assinatura():
    xlsx = _xlsx_bytes(["NCM", "Periodo", "Descricao", "UF"], [["840999", "2024", "x", "SP"]])
    assert ler_planilha(xlsx, "qualquer.bin").linhas  # detecta pelo PK\x03\x04
    assert ler_planilha(_CSV.encode("utf-8"), "in.csv").colunas_originais[0] == "NCM"


def test_coluna_minima_ausente_rejeita_lote():
    with pytest.raises(ColunaAusenteError):
        ler_csv("NCM,Periodo,UF\n8482,2024,SP\n")  # falta Descricao
