"""Apresentador: formata saídas dos casos de uso para exibição (independente de Flask)."""


def reais(centavos):
    return f"R$ {centavos / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def nota_media(media):
    return "sem avaliações" if media is None else f"{media:.1f}".replace(".", ",")
