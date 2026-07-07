"""Unidade do Categorizador das 18 categorias EFD — precedência, confiança e
o catch-all `Indefinido` (doc 04). Sem banco: repositório fake em memória."""

from __future__ import annotations

from giva.categoria.categorizador import CATEGORIA_INDEFINIDA, Categorizador

_ACENTOS = str.maketrans("áàâãéêíóôõúüç", "aaaaeeiooouuc")


def _sem_acento(texto: str) -> str:
    return texto.lower().translate(_ACENTOS)


class FakeRepo:
    """Espelha o comportamento do RepositorioCategoriaSQL (prefixo mais longo
    vence; palavra casa sem acento/caixa)."""

    def __init__(self, ncm=(), palavra=(), excecoes=None, versao="1.0"):
        self._ncm = list(ncm)  # (prefixo, categoria)
        self._palavra = [(_sem_acento(p), c) for p, c in palavra]
        self._exc = dict(excecoes or {})
        self._versao = versao

    def versao_vigente(self) -> str:
        return self._versao

    def buscar_excecao(self, ncm: str, versao: str):
        return self._exc.get(ncm)

    def buscar_por_ncm(self, ncm: str, versao: str):
        casam = [(p, c) for p, c in self._ncm if ncm.startswith(p)]
        if not casam:
            return None
        return max(casam, key=lambda t: len(t[0]))[1]

    def buscar_por_palavra(self, descricao: str, versao: str):
        d = _sem_acento(descricao)
        return sorted({c for pal, c in self._palavra if pal in d})


def test_excecao_exata_vence_tudo_com_confianca_alta():
    repo = FakeRepo(
        ncm=[("84", "Peça de máquina")],
        excecoes={"84129999": "Serviço"},
    )
    r = Categorizador(repo).categorizar("84129999", "qualquer coisa")
    assert r.categoria == "Serviço"
    assert r.confianca == "alta"
    assert r.proveniencia.caminho == "excecao"


def test_ncm_e_descricao_concordam_confianca_alta():
    repo = FakeRepo(
        ncm=[("8482", "Peça de máquina")],
        palavra=[("rolamento", "Peça de máquina")],
    )
    r = Categorizador(repo).categorizar("84821000", "Rolamento rígido de esferas")
    assert r.categoria == "Peça de máquina"
    assert r.confianca == "alta"
    assert r.proveniencia.caminho == "ncm+descricao"


def test_so_ncm_confianca_alta():
    # Opção B: sinal único forte (NCM) já dá Alta.
    repo = FakeRepo(ncm=[("8482", "Peça de máquina")])
    r = Categorizador(repo).categorizar("84821000", "descrição sem gatilho")
    assert r.categoria == "Peça de máquina"
    assert r.confianca == "alta"
    assert r.proveniencia.caminho == "ncm"


def test_ncm_e_autoritativo_mesmo_com_descricao_divergente():
    # Opção B: o NCM decide com Alta; a divergência com a descrição é sinalizada
    # à parte (similaridade), não rebaixa a confiança da categoria.
    repo = FakeRepo(
        ncm=[("8482", "Peça de máquina")],
        palavra=[("luva", "EPI")],
    )
    r = Categorizador(repo).categorizar("84821000", "Luva de proteção")
    assert r.categoria == "Peça de máquina"  # NCM tem prioridade
    assert r.confianca == "alta"
    assert r.proveniencia.caminho == "ncm"
    assert r.conflito_descricao is True  # descrição diverge do NCM → divergência forte


def test_sem_conflito_quando_ncm_e_descricao_concordam():
    repo = FakeRepo(
        ncm=[("8482", "Peça de máquina")],
        palavra=[("rolamento", "Peça de máquina")],
    )
    r = Categorizador(repo).categorizar("84821000", "Rolamento de esferas")
    assert r.conflito_descricao is False


def test_so_descricao_ncm_presente_sem_regra_confianca_alta():
    # NCM presente mas sem regra de faixa → sinal único da descrição → Alta.
    repo = FakeRepo(palavra=[("caneta", "Material de escritório e informática")])
    r = Categorizador(repo).categorizar("99999999", "Caneta esferográfica azul")
    assert r.categoria == "Material de escritório e informática"
    assert r.confianca == "alta"
    assert r.proveniencia.caminho == "descricao"


def test_so_descricao_ncm_ausente_confianca_media():
    # NCM ausente (branco/00000000) → categoria veio só do texto → Média.
    repo = FakeRepo(palavra=[("cafe", "Alimentação")])
    r = Categorizador(repo).categorizar(None, "Cafe em graos")
    assert r.categoria == "Alimentação"
    assert r.confianca == "media"


def test_descricao_ambigua_vira_indefinido():
    repo = FakeRepo(palavra=[("cabo", "Material elétrico"), ("cabo", "Ferramentas")])
    r = Categorizador(repo).categorizar("99999999", "Cabo genérico")
    assert r.categoria == CATEGORIA_INDEFINIDA
    assert r.confianca == "baixa"
    assert r.motivo_indefinido == "ambiguo"


def test_sem_pista_vira_indefinido_sem_match():
    repo = FakeRepo()
    r = Categorizador(repo).categorizar("99999999", "haste grande")
    assert r.categoria == CATEGORIA_INDEFINIDA
    assert r.motivo_indefinido == "sem_match"


def test_ncm_zerado_tratado_como_ausente_cai_na_descricao():
    repo = FakeRepo(
        ncm=[("00", "Peça de máquina")],  # não deve casar: 00000000 é ausente
        palavra=[("cafe", "Alimentação")],
    )
    r = Categorizador(repo).categorizar("00000000", "Café em grãos")
    assert r.categoria == "Alimentação"
    assert r.proveniencia.caminho == "descricao"


def test_ncm_none_cai_na_descricao():
    repo = FakeRepo(palavra=[("cafe", "Alimentação")])
    r = Categorizador(repo).categorizar(None, "Café torrado")
    assert r.categoria == "Alimentação"


def test_saida_e_sempre_sugestiva():
    r = Categorizador(FakeRepo()).categorizar("99999999", "x")
    assert r.sugestivo is True
