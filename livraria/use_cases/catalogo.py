"""Casos de uso de catálogo, lojas e avaliações (R01–R03, R07)."""
from dataclasses import asdict

from livraria.entities import (Avaliacao, Cliente, Edicao, Estoque, Livro, Loja, Promocao, media, normalizar,
                               preco_promocional)
from livraria.use_cases import filtrar, obter


class Catalogo:
    def __init__(self, repo):
        self.repo = repo

    def buscar_livros(self, titulo="", autor="", genero=""):
        filtros = {"titulo": titulo, "autor": autor, "genero": genero}
        return [livro for livro in self.repo.listar(Livro)
                if all(normalizar(termo) in normalizar(getattr(livro, campo)) for campo, termo in filtros.items() if termo)]

    def detalhes_livro(self, livro_id):
        livro = obter(self.repo, Livro, "Livro não encontrado.", id=livro_id)
        lojas = {loja.id: loja.nome for loja in self.repo.listar(Loja)}
        edicoes = []
        for edicao in filtrar(self.repo, Edicao, livro_id=livro_id):
            promocoes = filtrar(self.repo, Promocao, edicao_id=edicao.id, ativa=True)
            estoques = [dict(asdict(e), loja_nome=lojas[e.loja_id]) for e in filtrar(self.repo, Estoque, edicao_id=edicao.id)]
            edicoes.append(dict(asdict(edicao), promocoes=promocoes, estoques=estoques,
                                preco_final_centavos=preco_promocional(edicao, promocoes)))
        avaliacoes = filtrar(self.repo, Avaliacao, livro_id=livro_id)
        return dict(asdict(livro), edicoes=edicoes, avaliacoes=avaliacoes, media=media(avaliacoes),
                    total_avaliacoes=len(avaliacoes))

    def listar_lojas(self, bairro=""):
        return [loja for loja in self.repo.listar(Loja) if normalizar(bairro) in normalizar(loja.bairro)]

    def estoque(self, edicao_id, loja_id):
        return obter(self.repo, Estoque, "Edição ou loja inválida.", edicao_id=edicao_id, loja_id=loja_id)

    def avaliar(self, cliente_id, livro_id, nota, texto=""):
        """R07: uma avaliação por cliente e livro; avaliar de novo atualiza."""
        nota, texto = Avaliacao.validar(nota, texto)
        with self.repo.transacao():
            cliente = obter(self.repo, Cliente, "Cliente inválido; cadastre-se primeiro.", id=cliente_id)
            obter(self.repo, Livro, "Livro não encontrado.", id=livro_id)
            existentes = filtrar(self.repo, Avaliacao, cliente_id=cliente_id, livro_id=livro_id)
            avaliacao = existentes[0] if existentes else Avaliacao(0, livro_id, nota, texto, cliente.nome, cliente_id)
            avaliacao.nota, avaliacao.texto = nota, texto
            return self.repo.salvar(avaliacao)

    def avaliacoes_do_cliente(self, cliente_id):
        titulos = {livro.id: livro.titulo for livro in self.repo.listar(Livro)}
        return [dict(asdict(a), titulo=titulos[a.livro_id]) for a in filtrar(self.repo, Avaliacao, cliente_id=cliente_id)]
