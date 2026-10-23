"""Adaptador TXT: formato legível, semente idempotente, persistência entre instâncias e DIP."""
import json
import tempfile
import unittest
from pathlib import Path

from livraria.adaptadores.persistencia import UnidadeDeTrabalhoMemoria, UnidadeDeTrabalhoTxt, tabelas_demo
from livraria.adaptadores.persistencia.txt import desserializar
from livraria.casos_de_uso import criar_casos_de_uso
from livraria.frameworks.arquivo_texto import ArquivoTexto


class PersistenciaTxtTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.caminho = Path(tmp.name) / "dados" / "livraria.txt"

    def casos(self):
        return criar_casos_de_uso(UnidadeDeTrabalhoTxt(ArquivoTexto(self.caminho), tabelas_demo()))

    def test_semente_e_formato_uma_linha_por_registro(self):
        self.assertEqual(len(self.casos().buscar_livros.executar()), 2)
        linhas = self.caminho.read_text(encoding="utf-8").splitlines()
        self.assertTrue(linhas[0].startswith("#"))
        for linha in linhas[1:]:
            tipo, conteudo = linha.split("\t")
            self.assertTrue(tipo.isidentifier())
            self.assertIsInstance(json.loads(conteudo), dict)
        self.assertIn('livro\t{"autor": "L. Andrade"', "\n".join(linhas))
        self.assertIn("Marés", self.caminho.read_text(encoding="utf-8"))  # UTF-8 legível, sem escapes

    def test_dados_persistem_entre_instancias_e_semente_nao_se_repete(self):
        casos = self.casos()
        ana = casos.cadastrar.executar("Ana", "ana@example.com", "Centro", "Ficção")
        reserva = casos.reservar.executar(ana, 1, 1, "LEITURA10")
        casos.avaliar.executar(ana, 1, 3, "Ok")
        novo = self.casos()  # nova instância lendo o mesmo arquivo
        self.assertEqual(novo.consultar_estoque.executar(1, 1).quantidade, 0)
        self.assertEqual(novo.consultar_historico.executar(ana)["reservas"][0]["codigo"], reserva.codigo)
        self.assertEqual(novo.detalhar_livro.executar(1)["total_avaliacoes"], 2)
        self.assertEqual(len(novo.buscar_livros.executar()), 2)
        self.assertEqual(novo.reservar.executar(ana, 1, 2).codigo, "RES-000002")

    def test_falha_nao_altera_o_arquivo(self):
        casos = self.casos()
        ana = casos.cadastrar.executar("Ana", "ana@example.com", "Centro")
        antes = self.caminho.read_text(encoding="utf-8")
        with self.assertRaises(ValueError):
            casos.reservar.executar(ana, 2, 1)
        with self.assertRaises(ValueError):
            casos.comprar.executar(ana, 1, 1, "ANTIGO20")
        self.assertEqual(self.caminho.read_text(encoding="utf-8"), antes)
        self.assertEqual(list(self.caminho.parent.glob("*.tmp")), [])

    def test_dip_mesmo_nucleo_mesmo_resultado_em_memoria_e_txt(self):
        def roteiro(casos):
            ana = casos.cadastrar.executar("Ana", "ana@example.com", "Centro", "Ficção")
            reserva = casos.reservar.executar(ana, 1, 1, "BEMVINDO5")
            casos.retirar.executar(ana, reserva.codigo)
            casos.comprar.executar(ana, 3, 1)
            return casos.consultar_historico.executar(ana)
        memoria = criar_casos_de_uso(UnidadeDeTrabalhoMemoria(tabelas_demo()))
        self.assertEqual(roteiro(memoria), roteiro(self.casos()))

    def test_linha_com_tipo_desconhecido_e_rejeitada(self):
        with self.assertRaises(ValueError):
            desserializar("tabela_estranha\t{}\n")


if __name__ == "__main__":
    unittest.main()
