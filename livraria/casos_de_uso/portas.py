"""Portas de saída (DIP): o núcleo declara o que precisa; os adaptadores implementam.

Nenhuma porta menciona arquivo, SQL ou formato de serialização.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class RepositorioCatalogo(ABC):
    @abstractmethod
    def listar_livros(self): ...

    @abstractmethod
    def obter_livro(self, livro_id): ...

    @abstractmethod
    def edicoes_do_livro(self, livro_id): ...

    @abstractmethod
    def obter_edicao(self, edicao_id): ...

    @abstractmethod
    def promocoes_da_edicao(self, edicao_id): ...

    @abstractmethod
    def promocoes_ativas(self): ...

    @abstractmethod
    def avaliacoes_do_livro(self, livro_id): ...

    @abstractmethod
    def avaliacoes_do_cliente(self, cliente_id): ...

    @abstractmethod
    def salvar_avaliacao(self, avaliacao):
        """Insere (id 0) ou atualiza; devolve a avaliação com id."""


class RepositorioLojas(ABC):
    @abstractmethod
    def listar_lojas(self): ...

    @abstractmethod
    def obter_loja(self, loja_id): ...

    @abstractmethod
    def obter_estoque(self, edicao_id, loja_id): ...

    @abstractmethod
    def estoques_da_edicao(self, edicao_id): ...

    @abstractmethod
    def salvar_estoque(self, estoque): ...


class RepositorioClientes(ABC):
    @abstractmethod
    def obter(self, cliente_id): ...

    @abstractmethod
    def por_email(self, email): ...

    @abstractmethod
    def salvar(self, cliente):
        """Insere (id 0) ou atualiza; devolve o cliente com id."""

    @abstractmethod
    def favoritos(self, cliente_id):
        """IDs de livros favoritos."""

    @abstractmethod
    def adicionar_favorito(self, cliente_id, livro_id): ...

    @abstractmethod
    def remover_favorito(self, cliente_id, livro_id): ...

    @abstractmethod
    def notificacoes(self, cliente_id): ...

    @abstractmethod
    def adicionar_notificacao(self, notificacao): ...

    @abstractmethod
    def alertas_de(self, edicao_id, loja_id): ...

    @abstractmethod
    def adicionar_alerta(self, alerta): ...

    @abstractmethod
    def remover_alertas(self, edicao_id, loja_id): ...


class RepositorioPedidos(ABC):
    @abstractmethod
    def reserva_por_codigo(self, codigo): ...

    @abstractmethod
    def salvar_reserva(self, reserva):
        """Insere (id 0) ou atualiza; devolve a reserva com id."""

    @abstractmethod
    def reservas_do_cliente(self, cliente_id): ...

    @abstractmethod
    def salvar_compra(self, compra):
        """Insere (id 0) ou atualiza; devolve a compra com id."""

    @abstractmethod
    def compras_do_cliente(self, cliente_id): ...


class RepositorioCupons(ABC):
    @abstractmethod
    def obter(self, codigo): ...


class UnidadeDeTrabalho(ABC):
    """Transação de negócio: `with uow:` isola o trabalho; só `commit()` torna as mudanças duráveis.

    Sair do bloco sem commit descarta as alterações (rollback).
    """
    catalogo: RepositorioCatalogo
    lojas: RepositorioLojas
    clientes: RepositorioClientes
    pedidos: RepositorioPedidos
    cupons: RepositorioCupons

    @abstractmethod
    def __enter__(self): ...

    @abstractmethod
    def __exit__(self, *exc): ...

    @abstractmethod
    def commit(self): ...
