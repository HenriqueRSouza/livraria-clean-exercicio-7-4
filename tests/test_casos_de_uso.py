"""Critérios C01–C07 de docs/specs/livraria.md, executados contra o adaptador em memória."""
import unittest

from livraria.entidades import RegraInvalida
from tests.apoio import casos_em_memoria


class CasosDeUsoTest(unittest.TestCase):
    def setUp(self):
        self.c = casos_em_memoria()

    def cliente(self, email="ana@example.com"):
        return self.c.cadastrar.executar("Ana", email, "Centro", "Ficção")

    def estoque(self, edicao_id, loja_id):
        return self.c.consultar_estoque.executar(edicao_id, loja_id).quantidade

    def test_c01_busca_por_campos_combinados_e_sem_resultados(self):
        self.assertEqual(len(self.c.buscar_livros.executar()), 2)
        self.assertEqual([b.id for b in self.c.buscar_livros.executar(titulo="mares", autor="ANDRADE", genero="ficcao")], [1])
        self.assertEqual(self.c.buscar_livros.executar(titulo="inexistente"), [])

    def test_c02_detalhes_edicoes_avaliacoes_e_preco_promocional(self):
        livro = self.c.detalhar_livro.executar(1)
        self.assertTrue(livro["sinopse"])
        self.assertEqual(len(livro["edicoes"]), 2)
        self.assertTrue(livro["avaliacoes"])
        self.assertEqual(livro["edicoes"][0]["preco_centavos"], 5000)
        self.assertEqual(livro["edicoes"][0]["preco_final_centavos"], 4000)
        self.assertEqual({s["loja_id"]: s["quantidade"] for s in livro["edicoes"][0]["estoques"]}, {1: 1, 2: 2})
        with self.assertRaises(RegraInvalida):
            self.c.detalhar_livro.executar(999)

    def test_c03_lojas_bairro_dados_e_secao(self):
        lojas = self.c.listar_lojas.executar("CENTRO")
        self.assertEqual(len(lojas), 1)
        for campo in ("endereco", "horario", "pagamentos", "servicos", "cafe", "eventos"):
            self.assertTrue(hasattr(lojas[0], campo))
        self.assertEqual(self.c.consultar_estoque.executar(1, 1).secao, "Literatura")
        self.assertEqual(self.estoque(1, 2), 2)
        with self.assertRaises(RegraInvalida):
            self.c.consultar_estoque.executar(1, 99)

    def test_c04_cadastro_favoritos_recomendacoes_e_invalidos(self):
        for nome, email, bairro in (("", "ok@example.com", "Centro"), ("Ana", "ruim", "Centro"), ("Ana", "ok@example.com", "")):
            with self.assertRaises(RegraInvalida):
                self.c.cadastrar.executar(nome, email, bairro, "Ficção")
        cliente = self.cliente()
        with self.assertRaises(RegraInvalida):
            self.cliente("ANA@example.com")
        self.assertEqual([b.id for b in self.c.recomendar.executar(cliente)], [1])
        self.c.favoritar.executar(cliente, 1, True)
        self.c.favoritar.executar(cliente, 1, True)
        self.assertEqual(len(self.c.listar_favoritos.executar(cliente)), 1)
        self.assertEqual(self.c.recomendar.executar(cliente), [])
        self.c.favoritar.executar(cliente, 1, False)
        self.assertEqual(self.c.listar_favoritos.executar(cliente), [])
        self.assertTrue(any(n.tipo == "promocao" for n in self.c.listar_notificacoes.executar(cliente)))
        self.assertEqual(self.c.entrar.executar(" ANA@example.com ").id, cliente)

    def test_c05_reserva_ultimo_exemplar_sem_estoque_e_cancelamento(self):
        cliente = self.cliente()
        reserva = self.c.reservar.executar(cliente, 1, 1)
        self.assertEqual(reserva.codigo, "RES-000001")
        self.assertEqual(reserva.estado, "confirmada")
        self.assertEqual(reserva.preco_centavos, 4000)
        self.assertEqual(self.estoque(1, 1), 0)
        self.assertEqual(self.estoque(1, 2), 2)
        with self.assertRaises(RegraInvalida):
            self.c.reservar.executar(cliente, 1, 1)
        self.assertEqual(len(self.c.consultar_historico.executar(cliente)["reservas"]), 1)
        self.c.cancelar.executar(cliente, reserva.codigo)
        self.assertEqual(self.estoque(1, 1), 1)
        with self.assertRaises(RegraInvalida):
            self.c.cancelar.executar(cliente, reserva.codigo)

    def test_c06_retirada_compra_direta_pontos_e_transicoes_invalidas(self):
        cliente = self.cliente()
        outro = self.cliente("bia@example.com")
        reserva = self.c.reservar.executar(cliente, 1, 1)
        with self.assertRaises(RegraInvalida):
            self.c.retirar.executar(outro, reserva.codigo)
        self.c.retirar.executar(cliente, reserva.codigo)
        with self.assertRaises(RegraInvalida):
            self.c.retirar.executar(cliente, reserva.codigo)
        with self.assertRaises(RegraInvalida):
            self.c.cancelar.executar(cliente, reserva.codigo)
        self.assertEqual(self.estoque(1, 1), 0)
        compra = self.c.comprar.executar(cliente, 1, 2)
        self.assertEqual(compra.preco_centavos, 4000)
        self.assertEqual(self.estoque(1, 2), 1)
        self.assertEqual(self.c.consultar_historico.executar(cliente)["pontos"], 80)
        with self.assertRaises(RegraInvalida):
            self.c.comprar.executar(cliente, 2, 1)
        self.assertEqual(len(self.c.consultar_historico.executar(cliente)["compras"]), 2)

    def test_c07_alerta_reposicao_local(self):
        cliente = self.cliente()
        with self.assertRaises(RegraInvalida):
            self.c.alertar.executar(cliente, 1, 1)
        self.c.alertar.executar(cliente, 2, 1)
        self.c.alertar.executar(cliente, 2, 1)
        self.c.repor.executar(2, 1)
        self.assertEqual(self.estoque(2, 1), 1)
        self.assertEqual(sum(n.tipo == "reposicao" for n in self.c.listar_notificacoes.executar(cliente)), 1)
        self.c.repor.executar(2, 1)
        self.assertEqual(sum(n.tipo == "reposicao" for n in self.c.listar_notificacoes.executar(cliente)), 1)

    def test_falha_no_meio_do_caso_de_uso_nao_grava_nada(self):
        cliente = self.cliente()
        with self.assertRaises(RegraInvalida):
            self.c.reservar.executar(cliente, 2, 1)  # esgotado: nenhuma reserva parcial
        self.assertEqual(self.c.consultar_historico.executar(cliente)["reservas"], [])


if __name__ == "__main__":
    unittest.main()
