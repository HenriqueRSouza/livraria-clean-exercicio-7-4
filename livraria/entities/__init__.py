"""Entities: entidades fundamentais da livraria e regras que não dependem de tela nem de armazenamento."""
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional


class RegraInvalida(ValueError):
    """Operação não permitida pela especificação."""


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", str(texto)).casefold() if not unicodedata.combining(c))


@dataclass
class Livro:
    id: int
    titulo: str
    autor: str
    genero: str
    sinopse: str


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


@dataclass
class Cliente:
    id: int
    nome: str
    email: str
    bairro: str
    interesses: list = field(default_factory=list)

    @classmethod
    def novo(cls, nome, email, bairro, interesses=""):
        nome, email, bairro = nome.strip(), email.strip().lower(), bairro.strip()
        if not nome or not bairro or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise RegraInvalida("Informe nome, email válido e bairro.")
        return cls(0, nome, email, bairro, [p.strip() for p in interesses.split(",") if p.strip()])

    def interessado_em(self, genero):
        return normalizar(genero) in [normalizar(i) for i in self.interesses]


@dataclass
class Favorito:
    cliente_id: int
    livro_id: int


@dataclass
class Cupom:
    codigo: str
    descricao: str
    tipo: str  # "percentual" ou "fixo"
    valor: int
    ativo: bool

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
    codigo: str
    estado: str  # confirmada, retirada ou cancelada
    preco_centavos: int
    cupom: Optional[str] = None

    def _confirmada_de(self, cliente_id):
        if self.estado != "confirmada" or self.cliente_id != cliente_id:
            raise RegraInvalida("Reserva inexistente, de outro cliente ou já finalizada.")

    def cancelar(self, cliente_id):
        self._confirmada_de(cliente_id)
        self.estado = "cancelada"

    def retirar(self, cliente_id):
        """Vira compra sem novo débito de estoque."""
        self._confirmada_de(cliente_id)
        self.estado = "retirada"
        return Compra(0, self.cliente_id, self.edicao_id, self.loja_id, self.preco_centavos, self.id, self.cupom)


@dataclass
class Compra:
    id: int
    cliente_id: int
    edicao_id: int
    loja_id: int
    preco_centavos: int
    reserva_id: Optional[int] = None
    cupom: Optional[str] = None


@dataclass
class Avaliacao:
    id: int
    livro_id: int
    nota: int
    texto: str
    autor: str
    cliente_id: Optional[int] = None

    @staticmethod
    def validar(nota, texto):
        if not 1 <= nota <= 5:
            raise RegraInvalida("A nota deve ser um inteiro de 1 a 5.")
        texto = (texto or "").strip()
        if len(texto) > 500:
            raise RegraInvalida("O texto da avaliação deve ter até 500 caracteres.")
        return nota, texto


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


def preco_promocional(edicao, promocoes):
    return max(0, edicao.preco_centavos - sum(p.desconto_centavos for p in promocoes if p.ativa))


def pontos(compras):
    return sum(c.preco_centavos // 100 for c in compras)


def media(avaliacoes):
    return round(sum(a.nota for a in avaliacoes) / len(avaliacoes), 1) if avaliacoes else None
