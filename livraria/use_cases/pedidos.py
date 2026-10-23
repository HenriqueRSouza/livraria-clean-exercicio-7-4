"""Casos de uso de reserva, compra, cupons, histórico, alertas e reposição (R05, R06, R08)."""
from dataclasses import asdict

from livraria.entities import (Alerta, Cliente, Compra, Cupom, Edicao, Estoque, Livro, Loja, Notificacao, Promocao,
                               RegraInvalida, Reserva, pontos, preco_promocional)
from livraria.use_cases import filtrar, obter


class Pedidos:
    def __init__(self, repo):
        self.repo = repo

    def _cliente(self, cliente_id):
        return obter(self.repo, Cliente, "Cliente inválido; cadastre-se primeiro.", id=cliente_id)

    def _estoque(self, edicao_id, loja_id):
        return obter(self.repo, Estoque, "Sem estoque nesta unidade/edição.", edicao_id=edicao_id, loja_id=loja_id)

    def _preco(self, cliente_id, edicao_id, codigo):
        """Preço promocional e, se houver, desconto do cupom (R08). Devolve (preço, código do cupom)."""
        edicao = obter(self.repo, Edicao, "Edição inválida.", id=edicao_id)
        preco = preco_promocional(edicao, filtrar(self.repo, Promocao, edicao_id=edicao_id))
        codigo = (codigo or "").strip().upper()
        if not codigo:
            return preco, None
        cupom = obter(self.repo, Cupom, f"Cupom {codigo} inexistente.", codigo=codigo)
        usado = (any(r.estado != "cancelada" for r in filtrar(self.repo, Reserva, cliente_id=cliente_id, cupom=codigo))
                 or filtrar(self.repo, Compra, cliente_id=cliente_id, cupom=codigo, reserva_id=None))
        if usado:
            raise RegraInvalida(f"Cupom {codigo} já utilizado por este cliente.")
        return cupom.aplicar(preco), codigo

    def reservar(self, cliente_id, edicao_id, loja_id, cupom=""):
        with self.repo.transacao():
            self._cliente(cliente_id)
            preco, cupom = self._preco(cliente_id, edicao_id, cupom)
            estoque = self._estoque(edicao_id, loja_id)
            estoque.debitar()
            self.repo.salvar(estoque)
            reserva = self.repo.salvar(Reserva(0, cliente_id, edicao_id, loja_id, "", "confirmada", preco, cupom))
            reserva.codigo = f"RES-{reserva.id:06d}"
            return self.repo.salvar(reserva)

    def _reserva(self, cliente_id, codigo):
        self._cliente(cliente_id)
        return obter(self.repo, Reserva, "Reserva inexistente, de outro cliente ou já finalizada.", codigo=codigo)

    def cancelar(self, cliente_id, codigo):
        with self.repo.transacao():
            reserva = self._reserva(cliente_id, codigo)
            reserva.cancelar(cliente_id)
            self.repo.salvar(reserva)
            estoque = self._estoque(reserva.edicao_id, reserva.loja_id)
            estoque.quantidade += 1
            self.repo.salvar(estoque)

    def retirar(self, cliente_id, codigo):
        with self.repo.transacao():
            reserva = self._reserva(cliente_id, codigo)
            compra = reserva.retirar(cliente_id)
            self.repo.salvar(reserva)
            return self.repo.salvar(compra)

    def comprar(self, cliente_id, edicao_id, loja_id, cupom=""):
        with self.repo.transacao():
            self._cliente(cliente_id)
            preco, cupom = self._preco(cliente_id, edicao_id, cupom)
            estoque = self._estoque(edicao_id, loja_id)
            estoque.debitar()
            self.repo.salvar(estoque)
            return self.repo.salvar(Compra(0, cliente_id, edicao_id, loja_id, preco, None, cupom))

    def historico(self, cliente_id):
        self._cliente(cliente_id)
        reservas = sorted(filtrar(self.repo, Reserva, cliente_id=cliente_id), key=lambda r: r.id, reverse=True)
        compras = sorted(filtrar(self.repo, Compra, cliente_id=cliente_id), key=lambda c: c.id, reverse=True)
        return {"reservas": [dict(self._descricao(r), secao=self._estoque(r.edicao_id, r.loja_id).secao) for r in reservas],
                "compras": [self._descricao(c) for c in compras],
                "pontos": pontos(compras)}

    def _descricao(self, pedido):
        edicao = obter(self.repo, Edicao, "Edição inválida.", id=pedido.edicao_id)
        livro = obter(self.repo, Livro, "Livro inválido.", id=edicao.livro_id)
        loja = obter(self.repo, Loja, "Loja inválida.", id=pedido.loja_id)
        return dict(asdict(pedido), titulo=livro.titulo, edicao=edicao.nome, loja=loja.nome)

    def alertar(self, cliente_id, edicao_id, loja_id):
        self._cliente(cliente_id)
        estoque = filtrar(self.repo, Estoque, edicao_id=edicao_id, loja_id=loja_id)
        if not estoque or estoque[0].quantidade != 0:
            raise RegraInvalida("Alerta permitido apenas para edição esgotada na unidade.")
        with self.repo.transacao():
            self.repo.salvar(Alerta(cliente_id, edicao_id, loja_id))

    def repor(self, edicao_id, loja_id):
        with self.repo.transacao():
            estoque = obter(self.repo, Estoque, "Edição ou loja inválida.", edicao_id=edicao_id, loja_id=loja_id)
            estoque.quantidade += 1
            self.repo.salvar(estoque)
            livro = obter(self.repo, Livro, "Livro inválido.", id=obter(self.repo, Edicao, "", id=edicao_id).livro_id)
            loja = obter(self.repo, Loja, "Loja inválida.", id=loja_id)
            for alerta in filtrar(self.repo, Alerta, edicao_id=edicao_id, loja_id=loja_id):
                self.repo.salvar(Notificacao(0, alerta.cliente_id, "reposicao", f"Reposição simulada: {livro.titulo} em {loja.nome}"))
                self.repo.remover(alerta)
