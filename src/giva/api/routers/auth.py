"""POST /auth/login, GET /auth/me (ADR-07)."""

from __future__ import annotations

from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from giva.api.deps import get_conexao, get_usuario_atual
from giva.api.schemas.auth import LoginRequest, LoginResponse, UsuarioAtual
from giva.api.seguranca import UsuarioToken, criar_token, verificar_senha

router = APIRouter(prefix="/auth", tags=["auth"])

_SQL_BUSCAR_POR_EMAIL = "SELECT id, senha_hash, papel FROM usuario WHERE email = %s"


@router.post("/login")
def login(
    dados: LoginRequest,
    con: Annotated[psycopg.Connection, Depends(get_conexao)],
) -> LoginResponse:
    row = con.execute(_SQL_BUSCAR_POR_EMAIL, (dados.email,)).fetchone()
    # Mesma mensagem para "email não existe" e "senha errada" — não revela
    # se o email está cadastrado (evita enumeração de contas).
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos."
    )
    if row is None:
        raise credenciais_invalidas
    usuario_id, senha_hash, papel = row
    if not verificar_senha(dados.senha, senha_hash):
        raise credenciais_invalidas
    token = criar_token(usuario_id=usuario_id, email=dados.email, papel=papel)
    return LoginResponse(token=token, papel=papel)


@router.get("/me")
def me(usuario: Annotated[UsuarioToken, Depends(get_usuario_atual)]) -> UsuarioAtual:
    return UsuarioAtual(id=usuario.id, email=usuario.email, papel=usuario.papel)
