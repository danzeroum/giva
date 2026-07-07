"""Configuração da aplicação — 12-factor (plano §8: config no ambiente).

Política **única** de resolução da URL do banco, compartilhada pelo Alembic
(migrations/env.py) e pela aplicação, para não haver dois comportamentos de
configuração no mesmo repositório:

- `DATABASE_URL` definida → usa-a (produção, homologação, CI e dev).
- ausente → **falha explícita**. O fallback para a URL de dev do `alembic.ini`
  só é permitido sob opt-in explícito (`ALEMBIC_ALLOW_INI_URL=1`), reservado ao
  desenvolvimento local — produção/homologação nunca caem silenciosamente numa
  credencial de dev.
"""

from __future__ import annotations

import os
from pathlib import Path

OPT_IN_INI = "ALEMBIC_ALLOW_INI_URL"


class ConfiguracaoAusenteError(RuntimeError):
    """DATABASE_URL ausente sem o opt-in de dev local. Mensagem acionável."""

    def __init__(self) -> None:
        super().__init__(
            "DATABASE_URL não definida. Defina DATABASE_URL no ambiente "
            "(12-factor) ou, apenas em dev local, exporte "
            f"{OPT_IN_INI}=1 para usar a URL de dev do alembic.ini."
        )


def resolver_url_banco(fallback_ini: str | None = None) -> str:
    """Resolve a URL do banco pela política 12-factor.

    `fallback_ini` é a URL de dev do `alembic.ini`, passada apenas pelo
    Alembic; a aplicação chama sem fallback, então exige `DATABASE_URL` sempre.
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    if fallback_ini is not None and os.environ.get(OPT_IN_INI) == "1":
        return fallback_ini
    raise ConfiguracaoAusenteError()


def dsn_psycopg() -> str:
    """`resolver_url_banco()` no formato que `psycopg.connect()` entende —
    remove o `+psycopg` do scheme (estilo SQLAlchemy) usado em `DATABASE_URL`.
    Único ponto de conversão; API e testes de integração devem usar esta
    função em vez de repetir `.replace("+psycopg", "")`."""
    return resolver_url_banco().replace("+psycopg", "")


class JwtSecretAusenteError(RuntimeError):
    """JWT_SECRET ausente. Mensagem acionável — mesma política 12-factor."""

    def __init__(self) -> None:
        super().__init__(
            "JWT_SECRET não definida. Defina JWT_SECRET no ambiente (12-factor) "
            "— um segredo estável e único por ambiente (gere com "
            "`openssl rand -hex 32`, por exemplo). Nunca hardcode nem reuse "
            "entre ambientes."
        )


def jwt_secret() -> str:
    """Segredo simétrico (HS256) para assinar/verificar tokens JWT (ADR-07).
    Mesma política 12-factor de `resolver_url_banco` — falha explícita se
    ausente, nunca um default silencioso."""
    segredo = os.environ.get("JWT_SECRET")
    if not segredo:
        raise JwtSecretAusenteError()
    return segredo


class DiretorioDadosAusenteError(RuntimeError):
    """DADOS_DIR ausente. Mensagem acionável — mesma política 12-factor."""

    def __init__(self) -> None:
        super().__init__(
            "DADOS_DIR não definida. Defina DADOS_DIR no ambiente (12-factor) "
            "— o caminho onde entradas/ e saídas/ de lotes são gravadas (o "
            "volume /data montado nos serviços api/worker via docker-compose)."
        )


def diretorio_dados() -> Path:
    """Raiz do armazenamento de arquivos de lote (Fase 3, ADR-01 — volume
    local, sem S3 no volume atual do projeto). Mesma política 12-factor de
    `resolver_url_banco`/`jwt_secret` — falha explícita se ausente."""
    valor = os.environ.get("DADOS_DIR")
    if not valor:
        raise DiretorioDadosAusenteError()
    return Path(valor)
