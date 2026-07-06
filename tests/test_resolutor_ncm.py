"""ResolutorNCM period-aware — o coração do GIVA (critério de aceite nº 1):
o mesmo código com redações diferentes em 2017 e 2024 devolve a descrição
vigente NAQUELE período. Sem banco: repositório fake em memória."""

from __future__ import annotations

from datetime import date

from giva.ncm.resolvedor import RedacaoPeriodo, RedacaoVigente, ResolutorNCM


class FakeRepo:
    def __init__(self, historico=(), vigentes=None, correlacoes=()):
        self._hist = list(historico)  # RedacaoPeriodo
        self._vig = dict(vigentes or {})  # codigo -> RedacaoVigente
        self._corr = set(correlacoes)

    def buscar_redacao_periodo(self, codigo, periodo):
        for r in self._hist:
            fim = r.vigencia_fim or date.max
            if r.codigo == codigo and r.vigencia_inicio <= periodo < fim:
                return r
        return None

    def buscar_vigente(self, codigo):
        return self._vig.get(codigo)

    def existe_correlacao(self, codigo):
        return codigo in self._corr


def _periodo(cod, ini, fim, desc):
    return RedacaoPeriodo(cod, desc, ini, fim, "Resolução", "x", "20", date(2026, 7, 1), 1)


def _vigente(cod, ini, desc):
    return RedacaoVigente(cod, desc, ini, "Resolução", "272", "2021", date(2026, 7, 1), 1)


def test_descricao_da_epoca_muda_com_o_periodo():
    repo = FakeRepo(historico=[
        _periodo("84821000", date(2017, 1, 1), date(2022, 4, 1), "Redação de 2017"),
        _periodo("84821000", date(2022, 4, 1), None, "Redação atual"),
    ])
    r = ResolutorNCM(repo)
    assert r.resolver("84821000", date(2017, 6, 1)).descricao == "Redação de 2017"
    assert r.resolver("84821000", date(2024, 6, 1)).descricao == "Redação atual"
    # ambos ok — temos a redação de época dos dois lados da virada
    assert r.resolver("84821000", date(2017, 6, 1)).status_ncm == "ok"


def test_fronteira_exata_da_virada_pertence_a_nova_redacao():
    repo = FakeRepo(historico=[
        _periodo("84821000", date(2017, 1, 1), date(2022, 4, 1), "Antiga"),
        _periodo("84821000", date(2022, 4, 1), None, "Nova"),
    ])
    # intervalo semiaberto [ini, fim): 01/04/2022 já é a nova redação
    assert ResolutorNCM(repo).resolver("84821000", date(2022, 4, 1)).descricao == "Nova"


def test_sem_historico_cai_na_vigente_quando_periodo_cobre():
    repo = FakeRepo(vigentes={"22030000": _vigente("22030000", date(2022, 4, 1), "Cervejas")})
    r = ResolutorNCM(repo).resolver("22030000", date(2023, 1, 1))
    assert r.status_ncm == "ok"
    assert r.descricao == "Cervejas"


def test_sem_historico_periodo_anterior_a_vigente_nao_inventa():
    repo = FakeRepo(vigentes={"22030000": _vigente("22030000", date(2022, 4, 1), "Cervejas")})
    r = ResolutorNCM(repo).resolver("22030000", date(2018, 1, 1))
    assert r.status_ncm == "descricao_vigente_periodo_nao_carregado"


def test_codigo_inexistente():
    r = ResolutorNCM(FakeRepo()).resolver("99999999", date(2023, 1, 1))
    assert r.status_ncm == "codigo_inexistente"
    assert r.descricao is None


def test_codigo_extinto_com_correlacao_sh():
    repo = FakeRepo(correlacoes={"84829900"})
    r = ResolutorNCM(repo).resolver("84829900", date(2023, 1, 1))
    assert r.status_ncm == "codigo_alterado_pela_revisao_sh"
