"""Fábricas de teste: o mesmo núcleo montado sobre implementações diferentes das portas."""
from livraria.adaptadores.persistencia import UnidadeDeTrabalhoMemoria, tabelas_demo
from livraria.casos_de_uso import criar_casos_de_uso


def casos_em_memoria():
    return criar_casos_de_uso(UnidadeDeTrabalhoMemoria(tabelas_demo()))
