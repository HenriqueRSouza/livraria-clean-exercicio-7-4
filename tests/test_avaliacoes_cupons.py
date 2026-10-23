"""C09 (avaliações de clientes) e C10 (cupons de desconto) contra o adaptador em memória."""
import unittest

from livraria.entidades import Cupom, RegraInvalida
from tests.apoio import casos_em_memoria


class AvaliacoesTest(unittest.TestCase):
    def setUp(self):
        self.c = casos_em_memoria()
        self.ana = self.c.cadastrar.executar("Ana", "ana@example.com", "Centro", "Ficção")

    def test_c09_avaliar_recalcula_media_e_aparece_na_area(self):
        self.assertEqual((self.c.detalhar_livro.executar(1)["media"], self.c.detalhar_livro.executar(1)["total_avaliacoes"]), (5.0, 1))
        self.c.avaliar.executar(self.ana, 1, 4, "  Bom ritmo  ")
        livro = self.c.detalhar_livro.executar(1)
        self.assertEqual((livro["media"], livro["total_avaliacoes"]), (4.5, 2))
        minhas = self.c.avaliacoes_do_cliente.executar(self.ana)
        self.assertEqual([(a["titulo"], a["nota"], a["texto"]) for a in minhas], [("A Casa das Marés", 4, "Bom ritmo")])
        self.assertEqual(self.c.detalhar_livro.executar(2)["media"], None)

    def test_c09_reavaliar_atualiza_sem_duplicar(self):
        self.c.avaliar.executar(self.ana, 1, 2)
        self.c.avaliar.executar(self.ana, 1, 3, "Mudei de ideia")
        livro = self.c.detalhar_livro.executar(1)
        self.assertEqual(livro["total_avaliacoes"], 2)
        self.assertEqual(livro["media"], 4.0)
        self.assertEqual(len(self.c.avaliacoes_do_cliente.executar(self.ana)), 1)

    def test_c09_entradas_invalidas_nao_gravam(self):
        for args in ((self.ana, 1, 0), (self.ana, 1, 6), (self.ana, 1, 5, "x" * 501), (self.ana, 99, 5), (999, 1, 5)):
            with self.assertRaises(RegraInvalida):
                self.c.avaliar.executar(*args)
        self.assertEqual(self.c.detalhar_livro.executar(1)["total_avaliacoes"], 1)
        self.c.avaliar.executar(self.ana, 1, 5, "x" * 500)


class CuponsTest(unittest.TestCase):
    def setUp(self):
        self.c = casos_em_memoria()
        self.ana = self.c.cadastrar.executar("Ana", "ana@example.com", "Centro", "Ficção")

    def estoque(self, edicao_id, loja_id):
        return self.c.consultar_estoque.executar(edicao_id, loja_id).quantidade

    def test_c10_regra_de_desconto_da_entidade(self):
        percentual = Cupom("P", "", "percentual", 10, True)
        self.assertEqual(percentual.aplicar(4000), 3600)
        self.assertEqual(percentual.aplicar(4005), 3605)  # desconto 400,5 → 400 (para baixo)
        self.assertEqual(Cupom("F", "", "fixo", 500, True).aplicar(300), 0)
        with self.assertRaises(RegraInvalida):
            Cupom("X", "", "fixo", 1, False).aplicar(100)

    def test_c10_reserva_e_compra_com_cupom_registram_preco_e_codigo(self):
        reserva = self.c.reservar.executar(self.ana, 1, 2, " leitura10 ")
        self.assertEqual((reserva.preco_centavos, reserva.cupom), (3600, "LEITURA10"))
        compra = self.c.comprar.executar(self.ana, 3, 1, "BEMVINDO5")
        self.assertEqual((compra.preco_centavos, compra.cupom), (7500, "BEMVINDO5"))
        retirada = self.c.retirar.executar(self.ana, reserva.codigo)
        self.assertEqual((retirada.preco_centavos, retirada.cupom), (3600, "LEITURA10"))
        historico = self.c.consultar_historico.executar(self.ana)
        self.assertEqual(historico["pontos"], 36 + 75)
        self.assertEqual({c["cupom"] for c in historico["compras"]}, {"LEITURA10", "BEMVINDO5"})
        self.assertEqual(self.c.aplicar_cupom.simular(self.ana, 1, ""), 4000)

    def test_c10_cupom_usado_inexistente_ou_inativo_falha_sem_debitar(self):
        self.c.comprar.executar(self.ana, 1, 2, "LEITURA10")
        for cupom in ("LEITURA10", "NAOEXISTE", "ANTIGO20"):
            with self.assertRaises(RegraInvalida):
                self.c.reservar.executar(self.ana, 1, 2, cupom)
            with self.assertRaises(RegraInvalida):
                self.c.comprar.executar(self.ana, 1, 2, cupom)
        self.assertEqual(self.estoque(1, 2), 1)
        self.assertEqual(len(self.c.consultar_historico.executar(self.ana)["reservas"]), 0)
        outra = self.c.cadastrar.executar("Bia", "bia@example.com", "Jardim")
        self.assertEqual(self.c.comprar.executar(outra, 1, 2, "LEITURA10").preco_centavos, 3600)

    def test_c10_cancelar_reserva_libera_cupom_e_retirada_mantem_uso(self):
        reserva = self.c.reservar.executar(self.ana, 1, 2, "BEMVINDO5")
        with self.assertRaises(RegraInvalida):
            self.c.comprar.executar(self.ana, 1, 2, "BEMVINDO5")
        self.c.cancelar.executar(self.ana, reserva.codigo)
        nova = self.c.reservar.executar(self.ana, 1, 2, "BEMVINDO5")
        self.assertEqual(nova.preco_centavos, 3500)
        self.c.retirar.executar(self.ana, nova.codigo)
        with self.assertRaises(RegraInvalida):
            self.c.reservar.executar(self.ana, 1, 1, "BEMVINDO5")
        self.assertEqual(self.estoque(1, 1), 1)


if __name__ == "__main__":
    unittest.main()
