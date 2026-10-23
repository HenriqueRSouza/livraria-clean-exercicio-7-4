"""Critérios C01–C07, C09 e C10 testados direto nos casos de uso (RepositorioTxt em arquivo temporário)."""
import tempfile
import unittest
from pathlib import Path

from livraria.entities import Cupom, RegraInvalida
from livraria.infrastructure.repositorio_txt import RepositorioTxt
from livraria.use_cases.catalogo import Catalogo
from livraria.use_cases.clientes import Clientes
from livraria.use_cases.pedidos import Pedidos


class CasosDeUsoTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = RepositorioTxt(Path(tmp.name) / "teste.txt")
        self.catalogo, self.clientes, self.pedidos = Catalogo(repo), Clientes(repo), Pedidos(repo)

    def cliente(self, email="ana@example.com"):
        return self.clientes.cadastrar("Ana", email, "Centro", "Ficção")

    def estoque(self, edicao_id, loja_id):
        return self.catalogo.estoque(edicao_id, loja_id).quantidade

    def test_c01_busca(self):
        self.assertEqual(len(self.catalogo.buscar_livros()), 2)
        self.assertEqual([b.id for b in self.catalogo.buscar_livros("mares", "ANDRADE", "ficcao")], [1])
        self.assertEqual(self.catalogo.buscar_livros(titulo="inexistente"), [])

    def test_c02_detalhes_e_preco_promocional(self):
        livro = self.catalogo.detalhes_livro(1)
        self.assertEqual(len(livro["edicoes"]), 2)
        self.assertEqual(livro["edicoes"][0]["preco_final_centavos"], 4000)
        self.assertEqual({s["loja_id"]: s["quantidade"] for s in livro["edicoes"][0]["estoques"]}, {1: 1, 2: 2})
        with self.assertRaises(RegraInvalida):
            self.catalogo.detalhes_livro(999)

    def test_c03_lojas_por_bairro(self):
        lojas = self.catalogo.listar_lojas("CENTRO")
        self.assertEqual([l.nome for l in lojas], ["Unidade Centro"])
        self.assertEqual(self.catalogo.estoque(1, 1).secao, "Literatura")

    def test_c04_cadastro_favoritos_recomendacoes(self):
        for nome, email, bairro in (("", "ok@example.com", "Centro"), ("Ana", "ruim", "Centro"), ("Ana", "ok@example.com", "")):
            with self.assertRaises(RegraInvalida):
                self.clientes.cadastrar(nome, email, bairro)
        ana = self.cliente()
        with self.assertRaises(RegraInvalida):
            self.cliente("ANA@example.com")
        self.assertEqual([b.id for b in self.clientes.recomendacoes(ana)], [1])
        self.clientes.favoritar(ana, 1)
        self.clientes.favoritar(ana, 1)
        self.assertEqual(len(self.clientes.favoritos(ana)), 1)
        self.assertEqual(self.clientes.recomendacoes(ana), [])
        self.clientes.favoritar(ana, 1, adicionar=False)
        self.assertEqual(self.clientes.favoritos(ana), [])
        self.assertTrue(any(n.tipo == "promocao" for n in self.clientes.notificacoes(ana)))

    def test_c05_reserva_ultimo_exemplar_e_cancelamento(self):
        ana = self.cliente()
        reserva = self.pedidos.reservar(ana, 1, 1)
        self.assertEqual((reserva.codigo, reserva.estado, reserva.preco_centavos), ("RES-000001", "confirmada", 4000))
        self.assertEqual((self.estoque(1, 1), self.estoque(1, 2)), (0, 2))
        with self.assertRaises(RegraInvalida):
            self.pedidos.reservar(ana, 1, 1)
        self.pedidos.cancelar(ana, reserva.codigo)
        self.assertEqual(self.estoque(1, 1), 1)
        with self.assertRaises(RegraInvalida):
            self.pedidos.cancelar(ana, reserva.codigo)

    def test_c06_retirada_compra_direta_e_pontos(self):
        ana, bia = self.cliente(), self.cliente("bia@example.com")
        reserva = self.pedidos.reservar(ana, 1, 1)
        with self.assertRaises(RegraInvalida):
            self.pedidos.retirar(bia, reserva.codigo)
        self.pedidos.retirar(ana, reserva.codigo)
        with self.assertRaises(RegraInvalida):
            self.pedidos.retirar(ana, reserva.codigo)
        self.assertEqual(self.estoque(1, 1), 0)
        self.pedidos.comprar(ana, 1, 2)
        self.assertEqual(self.estoque(1, 2), 1)
        self.assertEqual(self.pedidos.historico(ana)["pontos"], 80)
        with self.assertRaises(RegraInvalida):
            self.pedidos.comprar(ana, 2, 1)

    def test_c07_alerta_e_reposicao(self):
        ana = self.cliente()
        self.pedidos.alertar(ana, 2, 1)
        self.pedidos.alertar(ana, 2, 1)
        self.pedidos.repor(2, 1)
        self.assertEqual(self.estoque(2, 1), 1)
        self.assertEqual(sum(n.tipo == "reposicao" for n in self.clientes.notificacoes(ana)), 1)
        with self.assertRaises(RegraInvalida):
            self.pedidos.alertar(ana, 2, 1)

    def test_c09_avaliacoes(self):
        ana = self.cliente()
        self.catalogo.avaliar(ana, 1, 4, "  Bom ritmo  ")
        self.catalogo.avaliar(ana, 1, 3, "Mudei de ideia")  # atualiza, não duplica
        livro = self.catalogo.detalhes_livro(1)
        self.assertEqual((livro["media"], livro["total_avaliacoes"]), (4.0, 2))
        self.assertEqual([(a["titulo"], a["nota"]) for a in self.catalogo.avaliacoes_do_cliente(ana)], [("A Casa das Marés", 3)])
        for args in ((ana, 1, 0), (ana, 1, 6), (ana, 1, 5, "x" * 501), (ana, 99, 5), (999, 1, 5)):
            with self.assertRaises(RegraInvalida):
                self.catalogo.avaliar(*args)
        self.assertEqual(self.catalogo.detalhes_livro(2)["media"], None)

    def test_c10_cupons(self):
        self.assertEqual(Cupom("P", "", "percentual", 10, True).aplicar(4005), 3605)  # desconto arredondado para baixo
        self.assertEqual(Cupom("F", "", "fixo", 500, True).aplicar(300), 0)
        ana = self.cliente()
        reserva = self.pedidos.reservar(ana, 1, 2, " leitura10 ")
        self.assertEqual((reserva.preco_centavos, reserva.cupom), (3600, "LEITURA10"))
        for cupom in ("LEITURA10", "NAOEXISTE", "ANTIGO20"):  # já usado, inexistente, inativo
            with self.assertRaises(RegraInvalida):
                self.pedidos.comprar(ana, 1, 2, cupom)
        self.assertEqual(self.estoque(1, 2), 1)  # nada foi debitado nas falhas
        self.pedidos.cancelar(ana, reserva.codigo)  # cancelar libera o cupom
        self.assertEqual(self.pedidos.comprar(ana, 1, 2, "LEITURA10").preco_centavos, 3600)
        self.assertEqual(self.pedidos.comprar(ana, 3, 1, "BEMVINDO5").preco_centavos, 7500)


if __name__ == "__main__":
    unittest.main()
