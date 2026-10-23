"""Persistência em TXT: formato legível e dados que continuam lá ao reabrir o arquivo."""
import json
import tempfile
import unittest
from pathlib import Path

from livraria.entities import Estoque, Livro
from livraria.infrastructure.repositorio_txt import RepositorioTxt
from livraria.use_cases.clientes import Clientes
from livraria.use_cases.pedidos import Pedidos
from livraria.use_cases.repositorio import RepositorioLivraria


class RepositorioTxtTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.caminho = Path(tmp.name) / "livraria.txt"

    def test_implementa_a_interface_e_grava_dados_de_exemplo(self):
        repo = RepositorioTxt(self.caminho)
        self.assertIsInstance(repo, RepositorioLivraria)
        self.assertEqual(len(repo.listar(Livro)), 2)
        linhas = self.caminho.read_text(encoding="utf-8").splitlines()
        self.assertTrue(linhas[0].startswith("#"))
        for linha in linhas[1:]:
            tipo, conteudo = linha.split("\t")
            self.assertIsInstance(json.loads(conteudo), dict)
        self.assertIn('livro\t{"autor": "L. Andrade"', "\n".join(linhas))
        RepositorioTxt(self.caminho)  # reabrir não duplica os dados de exemplo
        self.assertEqual(len(RepositorioTxt(self.caminho).listar(Livro)), 2)

    def test_dados_persistem_ao_reabrir(self):
        repo = RepositorioTxt(self.caminho)
        ana = Clientes(repo).cadastrar("Ana", "ana@example.com", "Centro")
        reserva = Pedidos(repo).reservar(ana, 1, 1, "LEITURA10")
        reaberto = RepositorioTxt(self.caminho)
        estoque = [e for e in reaberto.listar(Estoque) if (e.edicao_id, e.loja_id) == (1, 1)][0]
        self.assertEqual(estoque.quantidade, 0)
        self.assertEqual(Pedidos(reaberto).historico(ana)["reservas"][0]["codigo"], reserva.codigo)

    def test_erro_no_meio_da_operacao_nao_grava_nada(self):
        repo = RepositorioTxt(self.caminho)
        antes = self.caminho.read_text(encoding="utf-8")
        with self.assertRaises(RuntimeError):
            with repo.transacao():
                repo.salvar(Livro(0, "Rascunho", "X", "Y", "Z"))
                raise RuntimeError("falha simulada")
        self.assertEqual(self.caminho.read_text(encoding="utf-8"), antes)


if __name__ == "__main__":
    unittest.main()
