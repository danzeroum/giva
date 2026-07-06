"""Módulo B — resolução de status e descrição de NCM (RF-12/13)."""

from giva.ncm.classif import (
    DataInvalidaError,
    ErroClassif,
    RegistroNCM,
    apenas_digitos,
    eh_ncm_8_digitos,
    parsear_registros,
)
from giva.ncm.resolvedor import (
    ProvenienciaNCM,
    RedacaoVigente,
    RepositorioNCM,
    ResolutorNCM,
    ResultadoNCM,
)

__all__ = [
    "DataInvalidaError",
    "ErroClassif",
    "ProvenienciaNCM",
    "RedacaoVigente",
    "RegistroNCM",
    "RepositorioNCM",
    "ResolutorNCM",
    "ResultadoNCM",
    "apenas_digitos",
    "eh_ncm_8_digitos",
    "parsear_registros",
]
