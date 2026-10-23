"""Entidades da livraria e regras que valem independentemente de interface ou armazenamento."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from livraria.entidades.erros import RegraInvalida

TEXTO_AVALIACAO_MAX = 500


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", str(texto)).casefold()
                   if not unicodedata.combining(c))


@dataclass
class Livro:
    id: int
    titulo: str
    autor: str
    genero: str
    sinopse: str

    def corresponde(self, titulo="", autor="", genero=""):
        return all(normalizar(termo) in normalizar(valor)
                   for valor, termo in ((self.titulo, titulo), (self.autor, autor), (self.genero, genero)) if termo)


@dataclass
class Edicao:
    id: int
    livro_id: int
    nome: str
    ano: int
    preco_centavos: int


@dataclass
class Promocao:
    id: int
    edicao_id: int
    descricao: str
    desconto_centavos: int
    ativa: bool


def preco_promocional(edicao, promocoes):
    """Preço da edição menos promoções ativas, nunca negativo."""
    return max(0, edicao.preco_centavos - sum(p.desconto_centavos for p in promocoes if p.ativa))


@dataclass
class Loja:
    id: int
    nome: str
    bairro: str
    endereco: str
    horario: str
    pagamentos: str
    servicos: str
    cafe: bool
    eventos: str

    def no_bairro(self, bairro=""):
        return normalizar(bairro) in normalizar(self.bairro)


@dataclass
class Estoque:
    edicao_id: int
    loja_id: int
    quantidade: int
    secao: str

    def debitar(self):
        if self.quantidade <= 0:
            raise RegraInvalida("Sem estoque nesta unidade/edição.")
        self.quantidade -= 1

    def repor(self):
        self.quantidade += 1

    @property
    def esgotado(self):
        return self.quantidade == 0


@dataclass
class Cliente:
    id: int
    nome: str
    email: str
    bairro: str
    interesses: list[str] = field(default_factory=list)

    @classmethod
    def novo(cls, nome, email, bairro, interesses=""):
        nome, email, bairro = nome.strip(), email.strip().lower(), bairro.strip()
        if not nome or not bairro or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise RegraInvalida("Informe nome, email válido e bairro.")
        return cls(0, nome, email, bairro, [p.strip() for p in interesses.split(",") if p.strip()])

    def interessado_em(self, genero):
        return normalizar(genero) in [normalizar(i) for i in self.interesses]


@dataclass
class Cupom:
    codigo: str
    descricao: str
    tipo: str  # "percentual" ou "fixo"
    valor: int
    ativo: bool

    @staticmethod
    def normalizar_codigo(codigo):
        return (codigo or "").strip().upper()

    def aplicar(self, preco_centavos):
        if not self.ativo:
            raise RegraInvalida(f"Cupom {self.codigo} inativo.")
        desconto = preco_centavos * self.valor // 100 if self.tipo == "percentual" else self.valor
        return max(0, preco_centavos - desconto)


@dataclass
class Reserva:
    id: int
    cliente_id: int
    edicao_id: int
    loja_id: int
    codigo: str | None
    estado: str
    preco_centavos: int
    cupom: str | None = None

    @classmethod
    def nova(cls, cliente_id, edicao_id, loja_id, preco_centavos, cupom=None):
        return cls(0, cliente_id, edicao_id, loja_id, None, "confirmada", preco_centavos, cupom)

    @staticmethod
    def codigo_para(identificador):
        return f"RES-{identificador:06d}"

    def _exigir_confirmada_de(self, cliente_id):
        if self.estado != "confirmada" or self.cliente_id != cliente_id:
            raise RegraInvalida("Reserva inexistente, de outro cliente ou já finalizada.")

    def cancelar(self, cliente_id):
        self._exigir_confirmada_de(cliente_id)
        self.estado = "cancelada"

    def retirar(self, cliente_id):
        """Muda para retirada e devolve a compra correspondente, sem novo débito de estoque."""
        self._exigir_confirmada_de(cliente_id)
        self.estado = "retirada"
        return Compra(0, self.cliente_id, self.edicao_id, self.loja_id, self.preco_centavos, self.id, self.cupom)


@dataclass
class Compra:
    id: int
    cliente_id: int
    edicao_id: int
    loja_id: int
    preco_centavos: int
    reserva_id: int | None = None
    cupom: str | None = None

    @property
    def pontos(self):
        return self.preco_centavos // 100


def pontos_fidelidade(compras):
    return sum(c.pontos for c in compras)


def cupom_ja_usado(codigo, reservas, compras):
    """Uso conta em reservas não canceladas e em compras diretas (retiradas herdam da reserva)."""
    return (any(r.cupom == codigo and r.estado != "cancelada" for r in reservas)
            or any(c.cupom == codigo and c.reserva_id is None for c in compras))


@dataclass
class Avaliacao:
    id: int
    livro_id: int
    nota: int
    texto: str
    autor: str
    cliente_id: int | None = None

    @staticmethod
    def validar(nota, texto):
        if not isinstance(nota, int) or not 1 <= nota <= 5:
            raise RegraInvalida("A nota deve ser um inteiro de 1 a 5.")
        texto = (texto or "").strip()
        if len(texto) > TEXTO_AVALIACAO_MAX:
            raise RegraInvalida(f"O texto da avaliação deve ter até {TEXTO_AVALIACAO_MAX} caracteres.")
        return nota, texto


def media_notas(avaliacoes):
    return round(sum(a.nota for a in avaliacoes) / len(avaliacoes), 1) if avaliacoes else None


@dataclass
class Alerta:
    cliente_id: int
    edicao_id: int
    loja_id: int


@dataclass
class Notificacao:
    id: int
    cliente_id: int
    tipo: str
    mensagem: str
