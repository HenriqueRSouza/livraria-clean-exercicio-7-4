"""Casos de uso de cadastro, favoritos, recomendações e notificações (R02, R04)."""
from livraria.entities import Cliente, Edicao, Favorito, Livro, Notificacao, Promocao, RegraInvalida
from livraria.use_cases import filtrar, obter


class Clientes:
    def __init__(self, repo):
        self.repo = repo

    def obter(self, cliente_id):
        return obter(self.repo, Cliente, "Cliente inválido; cadastre-se primeiro.", id=cliente_id)

    def cadastrar(self, nome, email, bairro, interesses=""):
        cliente = Cliente.novo(nome, email, bairro, interesses)
        with self.repo.transacao():
            if filtrar(self.repo, Cliente, email=cliente.email):
                raise RegraInvalida("Email já cadastrado.")
            cliente = self.repo.salvar(cliente)
            for promocao in filtrar(self.repo, Promocao, ativa=True):
                edicao = obter(self.repo, Edicao, "Edição inválida.", id=promocao.edicao_id)
                livro = obter(self.repo, Livro, "Livro inválido.", id=edicao.livro_id)
                if cliente.interessado_em(livro.genero):
                    self.repo.salvar(Notificacao(0, cliente.id, "promocao", promocao.descricao))
            return cliente.id

    def entrar(self, email):
        return obter(self.repo, Cliente, "Email não cadastrado.", email=email.strip().lower())

    def favoritar(self, cliente_id, livro_id, adicionar=True):
        self.obter(cliente_id)
        obter(self.repo, Livro, "Livro inválido.", id=livro_id)
        with self.repo.transacao():
            if adicionar:
                self.repo.salvar(Favorito(cliente_id, livro_id))
            else:
                self.repo.remover(Favorito(cliente_id, livro_id))

    def favoritos(self, cliente_id):
        ids = {f.livro_id for f in filtrar(self.repo, Favorito, cliente_id=self.obter(cliente_id).id)}
        return [livro for livro in self.repo.listar(Livro) if livro.id in ids]

    def recomendacoes(self, cliente_id):
        cliente = self.obter(cliente_id)
        favoritos = {f.livro_id for f in filtrar(self.repo, Favorito, cliente_id=cliente_id)}
        return [livro for livro in self.repo.listar(Livro) if livro.id not in favoritos and cliente.interessado_em(livro.genero)]

    def notificacoes(self, cliente_id):
        return sorted(filtrar(self.repo, Notificacao, cliente_id=self.obter(cliente_id).id), key=lambda n: n.id, reverse=True)
