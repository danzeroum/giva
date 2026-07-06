"""Schemas Pydantic de autenticação (ADR-07)."""

from __future__ import annotations

from pydantic import BaseModel

from giva.api.seguranca import Papel


class LoginRequest(BaseModel):
    email: str
    senha: str


class LoginResponse(BaseModel):
    token: str
    papel: Papel


class UsuarioAtual(BaseModel):
    id: int
    email: str
    papel: Papel
