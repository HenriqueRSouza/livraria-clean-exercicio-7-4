"""Regra da dependência (Clean): imports só apontam para anéis mais internos."""
import ast
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "livraria"
STDLIB = set(sys.stdlib_module_names)


def imports(anel):
    for arquivo in (RAIZ / anel).rglob("*.py"):
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if isinstance(no, ast.Import):
                yield from ((arquivo.name, a.name) for a in no.names)
            elif isinstance(no, ast.ImportFrom):
                yield arquivo.name, ("." * no.level) + (no.module or "")


def violacoes(anel, permitido):
    return [(arquivo, modulo) for arquivo, modulo in imports(anel) if not permitido(modulo)]


class ArquiteturaTest(unittest.TestCase):
    def test_entidades_nao_dependem_de_nada_externo(self):
        permitidos = {"__future__", "dataclasses", "re", "unicodedata", "typing"}
        self.assertEqual(violacoes("entidades", lambda m: m.split(".")[0] in permitidos or m.startswith("livraria.entidades")), [])

    def test_casos_de_uso_dependem_so_de_entidades_e_abstracoes(self):
        permitidos = {"__future__", "abc", "dataclasses", "typing"}
        self.assertEqual(violacoes("casos_de_uso", lambda m: m.split(".")[0] in permitidos
                                   or m.startswith(("livraria.entidades", "livraria.casos_de_uso"))), [])

    def test_adaptadores_nao_conhecem_flask_nem_frameworks(self):
        def permitido(m):
            raiz = m.split(".")[0]
            if m.startswith("livraria."):
                return not m.startswith("livraria.frameworks")
            return raiz in STDLIB and raiz not in {"sqlite3", "os", "pathlib", "tempfile"}
        self.assertEqual(violacoes("adaptadores", permitido), [])

    def test_somente_frameworks_importa_flask(self):
        for anel in ("entidades", "casos_de_uso", "adaptadores"):
            self.assertFalse([m for _, m in imports(anel) if m.split(".")[0] == "flask"], anel)
        self.assertTrue(any(m == "flask" for _, m in imports("frameworks")))


if __name__ == "__main__":
    unittest.main()
