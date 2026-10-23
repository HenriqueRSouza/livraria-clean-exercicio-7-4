"""Catálogo de exemplo gravado na primeira execução (mesmo do exercício 6, mais cupons)."""
from livraria.entities import Avaliacao, Cupom, Edicao, Estoque, Livro, Loja, Promocao


def dados_exemplo():
    return [
        Livro(1, "A Casa das Marés", "L. Andrade", "Ficção", "Uma viagem às memórias de uma cidade costeira."),
        Livro(2, "Python para Todos", "Ana Ribeiro", "Tecnologia", "Introdução prática à programação."),
        Edicao(1, 1, "Brochura", 2024, 5000), Edicao(2, 1, "Capa dura", 2025, 7500), Edicao(3, 2, "Brochura", 2024, 8000),
        Loja(1, "Unidade Centro", "Centro", "Rua das Flores, 10", "Seg–Sáb 9h–18h", "Pix, cartão (simulados)",
             "Retirada, acessibilidade", True, "Clube do livro aos sábados"),
        Loja(2, "Unidade Jardim", "Jardim", "Av. Verde, 22", "Seg–Sáb 10h–19h", "Pix, cartão (simulados)",
             "Retirada", False, "Oficina de leitura mensal"),
        Estoque(1, 1, 1, "Literatura"), Estoque(1, 2, 2, "Ficção"), Estoque(2, 1, 0, "Literatura"),
        Estoque(2, 2, 1, "Ficção"), Estoque(3, 1, 2, "Tecnologia"), Estoque(3, 2, 0, "Tecnologia"),
        Avaliacao(1, 1, 5, "Envolvente", "Leitora demo"),
        Promocao(1, 1, "Oferta de demonstração", 1000, True),
        Cupom("LEITURA10", "10% de desconto", "percentual", 10, True),
        Cupom("BEMVINDO5", "R$ 5,00 de desconto", "fixo", 500, True),
        Cupom("ANTIGO20", "Cupom expirado de demonstração", "percentual", 20, False),
    ]
