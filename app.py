"""Ponto de entrada: monta as dependências de fora para dentro (TXT -> casos de uso -> controller -> Flask)."""
import os

from livraria.controllers.livraria_controller import LivrariaController
from livraria.infrastructure.repositorio_txt import RepositorioTxt
from livraria.ui.web import create_app
from livraria.use_cases.catalogo import Catalogo
from livraria.use_cases.clientes import Clientes
from livraria.use_cases.pedidos import Pedidos


def criar_app(caminho_txt=None):
    repo = RepositorioTxt(caminho_txt or os.environ.get("LIVRARIA_TXT", "livraria.txt"))
    controller = LivrariaController(Catalogo(repo), Clientes(repo), Pedidos(repo))
    return create_app(controller)


if __name__ == "__main__":
    criar_app().run(debug=False)
