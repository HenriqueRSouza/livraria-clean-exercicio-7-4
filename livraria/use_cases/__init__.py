"""Use cases: lógica de negócio da livraria. Só conhecem as entidades e a interface RepositorioLivraria."""
from livraria.entities import RegraInvalida


def filtrar(repo, tipo, **campos):
    return [r for r in repo.listar(tipo) if all(getattr(r, k) == v for k, v in campos.items())]


def obter(repo, tipo, erro, **campos):
    achados = filtrar(repo, tipo, **campos)
    if not achados:
        raise RegraInvalida(erro)
    return achados[0]
