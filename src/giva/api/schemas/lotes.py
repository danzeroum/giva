"""Schemas Pydantic de lotes, linhas e contestações (Fase 3)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class LoteResposta(BaseModel):
    id: int
    nome_arquivo: str | None
    status: str
    total_linhas: int | None
    linhas_processadas: int
    criado_por: str
    criado_em: datetime
    concluido_em: datetime | None
    resumo: dict[str, Any] | None


class LinhaLoteResposta(BaseModel):
    numero: int
    originais: dict[str, str]
    enriquecimento: dict[str, str]
    status: str
    uf: str | None
    proveniencia: dict[str, Any]


class ContestacaoRequest(BaseModel):
    tipo: str
    texto: str


class ContestacaoResposta(BaseModel):
    id: int
    lote_id: int
    numero_linha: int
    autor_id: int
    tipo: str
    texto: str
    status: str
    criado_em: datetime
