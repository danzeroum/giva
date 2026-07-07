"""Schemas Pydantic do Bloco B — Operação (Fase 4)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel

StatusValidacao = Literal[
    "validada",
    "confirmada_fonte_secundaria",
    "divergencia_entre_fontes",
    "pendente_validacao",
]


class UfResposta(BaseModel):
    uf: str
    vigencia_inicio: date
    vigencia_fim: date | None
    aliquota_modal: Decimal
    fecp_percentual: Decimal | None
    fecp_incidencia: str
    status_validacao: str
    fonte_legal: str | None
    fonte_compilada: str


class AtualizarStatusUfRequest(BaseModel):
    status_validacao: StatusValidacao


class ParametroResposta(BaseModel):
    nome: str
    valor: Any
    atualizado_em: datetime


class AtualizarParametroRequest(BaseModel):
    valor: Any


class HistoricoParametroItem(BaseModel):
    quando: datetime
    quem: str
    antes: dict[str, Any] | None
    depois: dict[str, Any] | None


class ExcecaoResposta(BaseModel):
    ncm: str
    categoria: str
    justificativa: str
    versao: str
    origem_tipo: str | None
    origem_contestacao_id: int | None
    autor_id: int | None
    criado_em: datetime


class CriarExcecaoRequest(BaseModel):
    ncm: str
    categoria: str
    justificativa: str
    origem_tipo: str | None = None
    origem_contestacao_id: int | None = None


class ContestacaoOperacaoResposta(BaseModel):
    id: int
    lote_id: int
    numero_linha: int
    autor_id: int
    tipo: str
    texto: str
    status: str
    resolucao: str | None
    criado_em: datetime
    resolvido_em: datetime | None


class EncaminharContestacaoRequest(BaseModel):
    destino: Literal["excecao", "validacao_uf", "resposta"]
    resolucao: str
    categoria: str | None = None
    ncm: str | None = None


class CargaResposta(BaseModel):
    id: int
    fonte: str
    arquivo_bruto: str
    hash_arquivo: str
    data_coleta: date
    status: str
    criado_em: datetime
    promovido_em: datetime | None
    promovido_por: str | None


class DiffCargaResposta(BaseModel):
    carga_id: int
    total_producao: int
    total_staging: int
    novos: int
    removidos: int
    alterados: int
    amostra_novos: list[str]
    amostra_removidos: list[str]
    amostra_alterados: list[str]


class PromoverCargaResposta(BaseModel):
    carga_id: int
    status: str
    promovidos: int
