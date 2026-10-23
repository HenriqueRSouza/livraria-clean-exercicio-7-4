"""Implementação em memória das portas — usada nos testes dos casos de uso."""
import copy
import threading

from livraria.adaptadores.persistencia.registros import UnidadeDeTrabalhoRegistros


class UnidadeDeTrabalhoMemoria(UnidadeDeTrabalhoRegistros):
    def __init__(self, dados_iniciais=None):
        self.trava = threading.RLock()
        self._confirmado = copy.deepcopy(dados_iniciais or {})

    def _carregar(self):
        return copy.deepcopy(self._confirmado)

    def _persistir(self, dados):
        self._confirmado = copy.deepcopy(dados)
