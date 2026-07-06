"""Fábrica do app FastAPI (ADR-07). Ponto de entrada: `uvicorn giva.api.app:app`."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from giva.api.erros import registrar_handlers
from giva.api.routers import auth, lotes, operacao, saude

# CORS_ORIGINS: lista separada por vírgula. Default cobre o Vite dev server;
# em produção, configure via env (nunca "*" com credentials).
_ORIGENS = [
    origem.strip()
    for origem in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origem.strip()
]


def criar_app() -> FastAPI:
    app = FastAPI(title="Farol Fiscal — API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_ORIGENS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    registrar_handlers(app)
    app.include_router(saude.router)
    app.include_router(auth.router)
    app.include_router(lotes.router)
    app.include_router(operacao.router)

    return app


app = criar_app()
