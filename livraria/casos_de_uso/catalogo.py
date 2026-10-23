"""Casos de uso de catálogo, lojas e avaliações (R01–R03, R07)."""
from dataclasses import asdict

from livraria.entidades import Avaliacao, RegraInvalida, media_notas, preco_promocional


class CasoDeUso:
    def __init__(self, uow):
        self.uow = uow


def exigir_livro(uow, livro_id):
    livro = uow.catalogo.obter_livro(livro_id)
    if not livro:
        raise RegraInvalida("Livro não encontrado.")
    return livro


def exigir_cliente(uow, cliente_id):
    cliente = uow.clientes.obter(cliente_id) if cliente_id else None
    if not cliente:
        raise RegraInvalida("Cliente inválido; cadastre-se primeiro.")
    return cliente


class BuscarLivros(CasoDeUso):
    def executar(self, titulo="", autor="", genero=""):
        with self.uow:
            return [livro for livro in self.uow.catalogo.listar_livros() if livro.corresponde(titulo, autor, genero)]


class DetalharLivro(CasoDeUso):
    """Monta o modelo de resposta com edições lado a lado, promoções, estoque por loja e avaliações."""

    def executar(self, livro_id):
        with self.uow:
            livro = exigir_livro(self.uow, livro_id)
            avaliacoes = self.uow.catalogo.avaliacoes_do_livro(livro_id)
            lojas = {loja.id: loja for loja in self.uow.lojas.listar_lojas()}
            edicoes = []
            for edicao in self.uow.catalogo.edicoes_do_livro(livro_id):
                promocoes = [p for p in self.uow.catalogo.promocoes_da_edicao(edicao.id) if p.ativa]
                estoques = [dict(asdict(s), loja_nome=lojas[s.loja_id].nome)
                            for s in self.uow.lojas.estoques_da_edicao(edicao.id)]
                edicoes.append(dict(asdict(edicao), promocoes=[asdict(p) for p in promocoes], estoques=estoques,
                                    preco_final_centavos=preco_promocional(edicao, promocoes)))
            return dict(asdict(livro), edicoes=edicoes, avaliacoes=[asdict(a) for a in avaliacoes],
                        media=media_notas(avaliacoes), total_avaliacoes=len(avaliacoes))


class ListarLojas(CasoDeUso):
    def executar(self, bairro=""):
        with self.uow:
            return [loja for loja in self.uow.lojas.listar_lojas() if loja.no_bairro(bairro)]


class ConsultarEstoque(CasoDeUso):
    def executar(self, edicao_id, loja_id):
        with self.uow:
            estoque = self.uow.lojas.obter_estoque(edicao_id, loja_id)
            if not estoque:
                raise RegraInvalida("Edição ou loja inválida.")
            return estoque


class Avaliar(CasoDeUso):
    """R07: uma avaliação por cliente/livro; reenviar atualiza."""

    def executar(self, cliente_id, livro_id, nota, texto=""):
        nota, texto = Avaliacao.validar(nota, texto)
        with self.uow:
            cliente = exigir_cliente(self.uow, cliente_id)
            exigir_livro(self.uow, livro_id)
            existente = next((a for a in self.uow.catalogo.avaliacoes_do_cliente(cliente_id) if a.livro_id == livro_id), None)
            avaliacao = existente or Avaliacao(0, livro_id, nota, texto, cliente.nome, cliente_id)
            avaliacao.nota, avaliacao.texto = nota, texto
            avaliacao = self.uow.catalogo.salvar_avaliacao(avaliacao)
            self.uow.commit()
            return avaliacao


class AvaliacoesDoCliente(CasoDeUso):
    def executar(self, cliente_id):
        with self.uow:
            exigir_cliente(self.uow, cliente_id)
            return [dict(asdict(a), titulo=self.uow.catalogo.obter_livro(a.livro_id).titulo)
                    for a in self.uow.catalogo.avaliacoes_do_cliente(cliente_id)]
