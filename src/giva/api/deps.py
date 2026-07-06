"""Dependências FastAPI comuns — conexão de banco e autenticação (ADR-07).

`get_conexao` abre uma conexão psycopg por request e a fecha ao final (sem pool
nesta fase — o volume esperado, ADR-01, não justifica a complexidade ainda).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Annotated

import psycopg
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from giva.api.seguranca import Papel, TokenInvalidoError, UsuarioToken, decodificar_token
from giva.config import dsn_psycopg

_bearer = HTTPBearer()


def get_conexao() -> Iterator[psycopg.Connection]:
    con = psycopg.connect(dsn_psycopg())
    try:
        yield con
    finally:
        con.close()


def get_usuario_atual(
    credenciais: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> UsuarioToken:
    """Decodifica o JWT do header `Authorization: Bearer <token>`. 401 se
    ausente, malformado, expirado ou com assinatura inválida."""
    try:
        return decodificar_token(credenciais.credentials)
    except TokenInvalidoError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


def exige_papel(*papeis: Papel) -> Callable[..., UsuarioToken]:
    """Dependency factory de RBAC: 403 se o papel do usuário autenticado não
    estiver entre os permitidos. Ex.: `Depends(exige_papel("operador", "admin"))`."""

    def _dependencia(
        usuario: Annotated[UsuarioToken, Depends(get_usuario_atual)],
    ) -> UsuarioToken:
        if usuario.papel not in papeis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Papel '{usuario.papel}' não autorizado; exige um de {papeis}.",
            )
        return usuario

    return _dependencia
