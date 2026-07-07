"""Exception handlers — erro de domínio nunca vira 500 genérico (ADR-07).

Duas categorias:
- **Entrada inválida do cliente** (ex.: upload sem coluna mínima) → 422, com a
  mensagem de domínio (já escrita para humano — ver `ColunaAusenteError`).
- **Invariante de dados violada** (ex.: exclusion constraint furada, mapeamento
  de categoria com buraco) → 500, mas com corpo explicando o que quebrou, para
  quem opera o sistema — nunca um traceback cru.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from giva.aliquota.resolvedor import ErroAliquota
from giva.pipeline.leitor import ColunaAusenteError


def _corpo(erro: str, detalhe: str) -> dict[str, str]:
    return {"erro": erro, "detalhe": detalhe}


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(ColunaAusenteError)
    async def _coluna_ausente(request: Request, exc: ColunaAusenteError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_corpo("colunas_minimas_ausentes", str(exc)),
        )

    @app.exception_handler(ErroAliquota)
    async def _erro_aliquota(request: Request, exc: ErroAliquota) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_corpo("invariante_aliquota_violada", str(exc)),
        )
