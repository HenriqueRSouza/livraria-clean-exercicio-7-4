"""Casos de uso de reserva, compra, cupons, histórico e reposição (R05, R06, R08)."""
from dataclasses import asdict

from livraria.casos_de_uso.catalogo import CasoDeUso, exigir_cliente
from livraria.entidades import (
    Alerta, Compra, Cupom, Notificacao, RegraInvalida, Reserva, cupom_ja_usado, pontos_fidelidade,
    preco_promocional,
)


def preco_atual(uow, edicao_id):
    edicao = uow.catalogo.obter_edicao(edicao_id)
    if not edicao:
        raise RegraInvalida("Edição inválida.")
    return preco_promocional(edicao, uow.catalogo.promocoes_da_edicao(edicao_id))


def exigir_estoque(uow, edicao_id, loja_id, erro="Sem estoque nesta unidade/edição."):
    estoque = uow.lojas.obter_estoque(edicao_id, loja_id)
    if not estoque:
        raise RegraInvalida(erro)
    return estoque


class AplicarCupom(CasoDeUso):
    """R08: valida o cupom para o cliente e devolve (preço final, código). Usado dentro de outra transação."""

    def aplicar(self, cliente_id, codigo, preco_centavos):
        codigo = Cupom.normalizar_codigo(codigo)
        if not codigo:
            return preco_centavos, None
        cupom = self.uow.cupons.obter(codigo)
        if not cupom:
            raise RegraInvalida(f"Cupom {codigo} inexistente.")
        if cupom_ja_usado(codigo, self.uow.pedidos.reservas_do_cliente(cliente_id), self.uow.pedidos.compras_do_cliente(cliente_id)):
            raise RegraInvalida(f"Cupom {codigo} já utilizado por este cliente.")
        return cupom.aplicar(preco_centavos), codigo

    def simular(self, cliente_id, edicao_id, codigo):
        with self.uow:
            exigir_cliente(self.uow, cliente_id)
            return self.aplicar(cliente_id, codigo, preco_atual(self.uow, edicao_id))[0]


class Reservar(CasoDeUso):
    def executar(self, cliente_id, edicao_id, loja_id, cupom=""):
        with self.uow:
            exigir_cliente(self.uow, cliente_id)
            preco, cupom = AplicarCupom(self.uow).aplicar(cliente_id, cupom, preco_atual(self.uow, edicao_id))
            estoque = exigir_estoque(self.uow, edicao_id, loja_id)
            estoque.debitar()
            self.uow.lojas.salvar_estoque(estoque)
            reserva = self.uow.pedidos.salvar_reserva(Reserva.nova(cliente_id, edicao_id, loja_id, preco, cupom))
            reserva.codigo = Reserva.codigo_para(reserva.id)
            reserva = self.uow.pedidos.salvar_reserva(reserva)
            self.uow.commit()
            return reserva


def reserva_do_codigo(uow, codigo):
    reserva = uow.pedidos.reserva_por_codigo(codigo)
    if not reserva:
        raise RegraInvalida("Reserva inexistente, de outro cliente ou já finalizada.")
    return reserva


class Cancelar(CasoDeUso):
    def executar(self, cliente_id, codigo):
        with self.uow:
            exigir_cliente(self.uow, cliente_id)
            reserva = reserva_do_codigo(self.uow, codigo)
            reserva.cancelar(cliente_id)
            estoque = exigir_estoque(self.uow, reserva.edicao_id, reserva.loja_id)
            estoque.repor()
            self.uow.lojas.salvar_estoque(estoque)
            self.uow.pedidos.salvar_reserva(reserva)
            self.uow.commit()


class Retirar(CasoDeUso):
    def executar(self, cliente_id, codigo):
        with self.uow:
            exigir_cliente(self.uow, cliente_id)
            reserva = reserva_do_codigo(self.uow, codigo)
            compra = reserva.retirar(cliente_id)
            self.uow.pedidos.salvar_reserva(reserva)
            compra = self.uow.pedidos.salvar_compra(compra)
            self.uow.commit()
            return compra


class Comprar(CasoDeUso):
    def executar(self, cliente_id, edicao_id, loja_id, cupom=""):
        with self.uow:
            exigir_cliente(self.uow, cliente_id)
            preco, cupom = AplicarCupom(self.uow).aplicar(cliente_id, cupom, preco_atual(self.uow, edicao_id))
            estoque = exigir_estoque(self.uow, edicao_id, loja_id)
            estoque.debitar()
            self.uow.lojas.salvar_estoque(estoque)
            compra = self.uow.pedidos.salvar_compra(Compra(0, cliente_id, edicao_id, loja_id, preco, None, cupom))
            self.uow.commit()
            return compra


class ConsultarHistorico(CasoDeUso):
    def executar(self, cliente_id):
        with self.uow:
            exigir_cliente(self.uow, cliente_id)
            reservas = sorted(self.uow.pedidos.reservas_do_cliente(cliente_id), key=lambda r: r.id, reverse=True)
            compras = sorted(self.uow.pedidos.compras_do_cliente(cliente_id), key=lambda c: c.id, reverse=True)
            return {
                "reservas": [dict(asdict(r), secao=self.uow.lojas.obter_estoque(r.edicao_id, r.loja_id).secao,
                                  **self._descricao(r)) for r in reservas],
                "compras": [dict(asdict(c), **self._descricao(c)) for c in compras],
                "pontos": pontos_fidelidade(compras),
            }

    def _descricao(self, pedido):
        edicao = self.uow.catalogo.obter_edicao(pedido.edicao_id)
        return {"titulo": self.uow.catalogo.obter_livro(edicao.livro_id).titulo, "edicao": edicao.nome,
                "loja": self.uow.lojas.obter_loja(pedido.loja_id).nome}


class Alertar(CasoDeUso):
    def executar(self, cliente_id, edicao_id, loja_id):
        with self.uow:
            exigir_cliente(self.uow, cliente_id)
            estoque = self.uow.lojas.obter_estoque(edicao_id, loja_id)
            if not estoque or not estoque.esgotado:
                raise RegraInvalida("Alerta permitido apenas para edição esgotada na unidade.")
            self.uow.clientes.adicionar_alerta(Alerta(cliente_id, edicao_id, loja_id))
            self.uow.commit()


class Repor(CasoDeUso):
    def executar(self, edicao_id, loja_id):
        with self.uow:
            estoque = exigir_estoque(self.uow, edicao_id, loja_id, "Edição ou loja inválida.")
            estoque.repor()
            self.uow.lojas.salvar_estoque(estoque)
            titulo = self.uow.catalogo.obter_livro(self.uow.catalogo.obter_edicao(edicao_id).livro_id).titulo
            mensagem = f"Reposição simulada: {titulo} em {self.uow.lojas.obter_loja(loja_id).nome}"
            for alerta in self.uow.clientes.alertas_de(edicao_id, loja_id):
                self.uow.clientes.adicionar_notificacao(Notificacao(0, alerta.cliente_id, "reposicao", mensagem))
            self.uow.clientes.remover_alertas(edicao_id, loja_id)
            self.uow.commit()
