"""Hash de senha (argon2) e tokens JWT (ADR-07). HS256 simétrico — segredo
único via `giva.config.jwt_secret()`, mesma política 12-factor de
`resolver_url_banco`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from giva.config import jwt_secret

Papel = Literal["analista", "operador", "admin"]

_ALGORITMO = "HS256"
_VALIDADE = timedelta(hours=8)
_hasher = PasswordHasher()


def hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    try:
        return _hasher.verify(hash_armazenado, senha)
    except VerifyMismatchError:
        return False


@dataclass(frozen=True)
class UsuarioToken:
    """O que o JWT decodificado carrega — o suficiente para RBAC sem nova
    consulta ao banco a cada request."""

    id: int
    email: str
    papel: Papel


def criar_token(*, usuario_id: int, email: str, papel: Papel) -> str:
    agora = datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),
        "email": email,
        "papel": papel,
        "iat": agora,
        "exp": agora + _VALIDADE,
    }
    return jwt.encode(payload, jwt_secret(), algorithm=_ALGORITMO)


class TokenInvalidoError(Exception):
    """Token ausente, malformado, expirado ou com assinatura inválida."""


def decodificar_token(token: str) -> UsuarioToken:
    try:
        payload = jwt.decode(token, jwt_secret(), algorithms=[_ALGORITMO])
    except jwt.InvalidTokenError as exc:
        raise TokenInvalidoError(str(exc)) from exc
    return UsuarioToken(id=int(payload["sub"]), email=payload["email"], papel=payload["papel"])
