"""Anel 2 — casos de uso e portas. Depende apenas de `livraria.entidades`."""
from dataclasses import dataclass, fields

from livraria.casos_de_uso.catalogo import (
    Avaliar, AvaliacoesDoCliente, BuscarLivros, ConsultarEstoque, DetalharLivro, ListarLojas,
)
from livraria.casos_de_uso.clientes import (
    Cadastrar, Entrar, Favoritar, ListarFavoritos, ListarNotificacoes, ObterCliente, Recomendar,
)
from livraria.casos_de_uso.pedidos import (
    Alertar, AplicarCupom, Cancelar, Comprar, ConsultarHistorico, Repor, Reservar, Retirar,
)
from livraria.casos_de_uso.portas import UnidadeDeTrabalho


@dataclass(frozen=True)
class CasosDeUso:
    buscar_livros: BuscarLivros
    detalhar_livro: DetalharLivro
    listar_lojas: ListarLojas
    consultar_estoque: ConsultarEstoque
    avaliar: Avaliar
    avaliacoes_do_cliente: AvaliacoesDoCliente
    cadastrar: Cadastrar
    entrar: Entrar
    obter_cliente: ObterCliente
    favoritar: Favoritar
    listar_favoritos: ListarFavoritos
    recomendar: Recomendar
    listar_notificacoes: ListarNotificacoes
    aplicar_cupom: AplicarCupom
    reservar: Reservar
    cancelar: Cancelar
    retirar: Retirar
    comprar: Comprar
    consultar_historico: ConsultarHistorico
    alertar: Alertar
    repor: Repor


def criar_casos_de_uso(uow: UnidadeDeTrabalho) -> CasosDeUso:
    """Instancia todos os casos de uso sobre qualquer implementação da porta UnidadeDeTrabalho."""
    return CasosDeUso(**{campo.name: campo.type(uow) for campo in fields(CasosDeUso)})
