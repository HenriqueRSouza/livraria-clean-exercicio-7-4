"""Repositórios sobre "tabelas" de registros simples (dicts), compartilhados pelas implementações
em memória e em TXT. Converte entidades ↔ registros; a mídia de armazenamento fica nas subclasses."""
from dataclasses import asdict

from livraria.casos_de_uso.portas import (
    RepositorioCatalogo, RepositorioClientes, RepositorioCupons, RepositorioLojas, RepositorioPedidos,
    UnidadeDeTrabalho,
)
from livraria.entidades import (
    Alerta, Avaliacao, Cliente, Compra, Cupom, Edicao, Estoque, Livro, Loja, Notificacao, Promocao,
    Reserva,
)

# tipo do registro → (entidade, campos que formam a chave)
TIPOS = {
    "livro": (Livro, ("id",)),
    "edicao": (Edicao, ("id",)),
    "loja": (Loja, ("id",)),
    "estoque": (Estoque, ("edicao_id", "loja_id")),
    "promocao": (Promocao, ("id",)),
    "avaliacao": (Avaliacao, ("id",)),
    "cupom": (Cupom, ("codigo",)),
    "cliente": (Cliente, ("id",)),
    "favorito": (None, ("cliente_id", "livro_id")),
    "alerta": (Alerta, ("cliente_id", "edicao_id", "loja_id")),
    "notificacao": (Notificacao, ("id",)),
    "reserva": (Reserva, ("id",)),
    "compra": (Compra, ("id",)),
}


def chave(tipo, registro):
    return "|".join(str(registro[campo]) for campo in TIPOS[tipo][1])


def tabelas_vazias():
    return {tipo: {} for tipo in TIPOS}


def registro_de(entidade):
    return asdict(entidade)


class Tabelas:
    """Acesso genérico às tabelas; cada repositório usa apenas os tipos do seu agregado."""

    def __init__(self, dados):
        self.dados = dados

    def todos(self, tipo, **filtro):
        entidade = TIPOS[tipo][0]
        registros = [r for r in self.dados[tipo].values() if all(r[k] == v for k, v in filtro.items())]
        return [entidade(**r) if entidade else dict(r) for r in registros]

    def um(self, tipo, **filtro):
        return next(iter(self.todos(tipo, **filtro)), None)

    def gravar(self, tipo, entidade):
        if getattr(entidade, "id", None) == 0:
            entidade.id = max((r["id"] for r in self.dados[tipo].values()), default=0) + 1
        registro = registro_de(entidade) if TIPOS[tipo][0] else dict(entidade)
        self.dados[tipo][chave(tipo, registro)] = registro
        return entidade

    def apagar(self, tipo, **filtro):
        for k in [k for k, r in self.dados[tipo].items() if all(r[c] == v for c, v in filtro.items())]:
            del self.dados[tipo][k]


def por_id(itens):
    return sorted(itens, key=lambda item: item.id)


class CatalogoRegistros(RepositorioCatalogo):
    def __init__(self, tabelas):
        self.t = tabelas

    def listar_livros(self):
        return por_id(self.t.todos("livro"))

    def obter_livro(self, livro_id):
        return self.t.um("livro", id=livro_id)

    def edicoes_do_livro(self, livro_id):
        return por_id(self.t.todos("edicao", livro_id=livro_id))

    def obter_edicao(self, edicao_id):
        return self.t.um("edicao", id=edicao_id)

    def promocoes_da_edicao(self, edicao_id):
        return por_id(self.t.todos("promocao", edicao_id=edicao_id))

    def promocoes_ativas(self):
        return por_id(self.t.todos("promocao", ativa=True))

    def avaliacoes_do_livro(self, livro_id):
        return por_id(self.t.todos("avaliacao", livro_id=livro_id))

    def avaliacoes_do_cliente(self, cliente_id):
        return por_id(self.t.todos("avaliacao", cliente_id=cliente_id))

    def salvar_avaliacao(self, avaliacao):
        return self.t.gravar("avaliacao", avaliacao)


class LojasRegistros(RepositorioLojas):
    def __init__(self, tabelas):
        self.t = tabelas

    def listar_lojas(self):
        return por_id(self.t.todos("loja"))

    def obter_loja(self, loja_id):
        return self.t.um("loja", id=loja_id)

    def obter_estoque(self, edicao_id, loja_id):
        return self.t.um("estoque", edicao_id=edicao_id, loja_id=loja_id)

    def estoques_da_edicao(self, edicao_id):
        return sorted(self.t.todos("estoque", edicao_id=edicao_id), key=lambda s: s.loja_id)

    def salvar_estoque(self, estoque):
        return self.t.gravar("estoque", estoque)


class ClientesRegistros(RepositorioClientes):
    def __init__(self, tabelas):
        self.t = tabelas

    def obter(self, cliente_id):
        return self.t.um("cliente", id=cliente_id)

    def por_email(self, email):
        email = email.strip().casefold()
        return next((c for c in self.t.todos("cliente") if c.email.casefold() == email), None)

    def salvar(self, cliente):
        return self.t.gravar("cliente", cliente)

    def favoritos(self, cliente_id):
        return [f["livro_id"] for f in self.t.todos("favorito", cliente_id=cliente_id)]

    def adicionar_favorito(self, cliente_id, livro_id):
        self.t.gravar("favorito", {"cliente_id": cliente_id, "livro_id": livro_id})

    def remover_favorito(self, cliente_id, livro_id):
        self.t.apagar("favorito", cliente_id=cliente_id, livro_id=livro_id)

    def notificacoes(self, cliente_id):
        return por_id(self.t.todos("notificacao", cliente_id=cliente_id))

    def adicionar_notificacao(self, notificacao):
        return self.t.gravar("notificacao", notificacao)

    def alertas_de(self, edicao_id, loja_id):
        return self.t.todos("alerta", edicao_id=edicao_id, loja_id=loja_id)

    def adicionar_alerta(self, alerta):
        self.t.gravar("alerta", alerta)

    def remover_alertas(self, edicao_id, loja_id):
        self.t.apagar("alerta", edicao_id=edicao_id, loja_id=loja_id)


class PedidosRegistros(RepositorioPedidos):
    def __init__(self, tabelas):
        self.t = tabelas

    def reserva_por_codigo(self, codigo):
        return self.t.um("reserva", codigo=codigo)

    def salvar_reserva(self, reserva):
        return self.t.gravar("reserva", reserva)

    def reservas_do_cliente(self, cliente_id):
        return por_id(self.t.todos("reserva", cliente_id=cliente_id))

    def salvar_compra(self, compra):
        return self.t.gravar("compra", compra)

    def compras_do_cliente(self, cliente_id):
        return por_id(self.t.todos("compra", cliente_id=cliente_id))


class CuponsRegistros(RepositorioCupons):
    def __init__(self, tabelas):
        self.t = tabelas

    def obter(self, codigo):
        return self.t.um("cupom", codigo=codigo)


class UnidadeDeTrabalhoRegistros(UnidadeDeTrabalho):
    """Base: carrega uma cópia de trabalho ao entrar, persiste no commit, descarta o resto ao sair.

    Subclasses definem `trava` (exclusão mútua entre requisições), `_carregar()` e `_persistir(dados)`.
    """
    trava = None

    def __enter__(self):
        self.trava.acquire()
        try:
            dados = tabelas_vazias()
            for tipo, registros in self._carregar().items():
                dados[tipo].update(registros)
        except BaseException:
            self.trava.release()
            raise
        self._dados = dados
        t = Tabelas(dados)
        self.catalogo, self.lojas, self.clientes = CatalogoRegistros(t), LojasRegistros(t), ClientesRegistros(t)
        self.pedidos, self.cupons = PedidosRegistros(t), CuponsRegistros(t)
        return self

    def __exit__(self, *exc):
        self._dados = None  # rollback: alterações não confirmadas são descartadas
        self.trava.release()
        return False

    def commit(self):
        self._persistir(self._dados)

    def _carregar(self):
        raise NotImplementedError

    def _persistir(self, dados):
        raise NotImplementedError
