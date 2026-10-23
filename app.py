"""Ponto de entrada: `python app.py` sobe a livraria (Clean) com persistência em LIVRARIA_TXT."""
from livraria.frameworks.web import create_app

if __name__ == "__main__":
    create_app().run(debug=False)
