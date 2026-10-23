"""Casos de uso de cadastro, favoritos, recomendações e notificações (R02, R04)."""
from livraria.casos_de_uso.catalogo import CasoDeUso, exigir_cliente, exigir_livro
from livraria.entidades import Cliente, Notificacao, RegraInvalida


class Cadastrar(CasoDeUso):
    def executar(self, nome, email, bairro, interesses=""):
        cliente = Cliente.novo(nome, email, bairro, interesses)
        with self.uow:
            if self.uow.clientes.por_email(cliente.email):
                raise RegraInvalida("Email já cadastrado.")
            cliente = self.uow.clientes.salvar(cliente)
            for promocao in self.uow.catalogo.promocoes_ativas():
                edicao = self.uow.catalogo.obter_edicao(promocao.edicao_id)
                if cliente.interessado_em(self.uow.catalogo.obter_livro(edicao.livro_id).genero):
                    self.uow.clientes.adicionar_notificacao(Notificacao(0, cliente.id, "promocao", promocao.descricao))
            self.uow.commit()
            return cliente.id


class Entrar(CasoDeUso):
    def executar(self, email):
        with self.uow:
            cliente = self.uow.clientes.por_email(email.strip())
            if not cliente:
                raise RegraInvalida("Email não cadastrado.")
            return cliente


class ObterCliente(CasoDeUso):
    def executar(self, cliente_id):
        with self.uow:
            return exigir_cliente(self.uow, cliente_id)


class Favoritar(CasoDeUso):
    def executar(self, cliente_id, livro_id, adicionar=True):
        with self.uow:
            exigir_cliente(self.uow, cliente_id)
            if not self.uow.catalogo.obter_livro(livro_id):
                raise RegraInvalida("Livro inválido.")
            if adicionar:
                self.uow.clientes.adicionar_favorito(cliente_id, livro_id)
            else:
                self.uow.clientes.remover_favorito(cliente_id, livro_id)
            self.uow.commit()


class ListarFavoritos(CasoDeUso):
    def executar(self, cliente_id):
        with self.uow:
            exigir_cliente(self.uow, cliente_id)
            return [exigir_livro(self.uow, i) for i in sorted(self.uow.clientes.favoritos(cliente_id))]


class Recomendar(CasoDeUso):
    def executar(self, cliente_id):
        with self.uow:
            cliente = exigir_cliente(self.uow, cliente_id)
            favoritos = set(self.uow.clientes.favoritos(cliente_id))
            return [livro for livro in self.uow.catalogo.listar_livros()
                    if livro.id not in favoritos and cliente.interessado_em(livro.genero)]


class ListarNotificacoes(CasoDeUso):
    def executar(self, cliente_id):
        with self.uow:
            exigir_cliente(self.uow, cliente_id)
            return sorted(self.uow.clientes.notificacoes(cliente_id), key=lambda n: n.id, reverse=True)
