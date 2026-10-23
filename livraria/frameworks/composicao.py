"""Raiz de composição: único lugar que escolhe implementações concretas para as portas (DIP)."""
import os

from livraria.adaptadores.persistencia import UnidadeDeTrabalhoTxt, tabelas_demo
from livraria.adaptadores.web import ControladorLivraria
from livraria.casos_de_uso import criar_casos_de_uso
from livraria.frameworks.arquivo_texto import ArquivoTexto


def montar_controlador(caminho_txt=None):
    caminho = caminho_txt or os.environ.get("LIVRARIA_TXT", "livraria.txt")
    uow = UnidadeDeTrabalhoTxt(ArquivoTexto(caminho), tabelas_demo())
    return ControladorLivraria(criar_casos_de_uso(uow))
