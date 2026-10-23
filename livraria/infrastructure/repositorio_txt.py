"""RepositorioTxt: implementa RepositorioLivraria guardando tudo em um arquivo texto.

Formato: uma linha por registro, "<tipo><TAB><json>", por exemplo:
    livro	{"autor": "L. Andrade", "genero": "Ficção", "id": 1, ...}
"""
import copy
import json
import os
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from livraria.entities import (Alerta, Avaliacao, Cliente, Compra, Cupom, Edicao, Estoque, Favorito, Livro, Loja,
                               Notificacao, Promocao, Reserva)
from livraria.infrastructure.dados_exemplo import dados_exemplo
from livraria.use_cases.repositorio import RepositorioLivraria

TIPOS = {classe.__name__.lower(): classe for classe in (Livro, Edicao, Promocao, Loja, Estoque, Cliente, Favorito,
                                                        Cupom, Reserva, Compra, Avaliacao, Alerta, Notificacao)}
# registros sem "id" são identificados por estes campos
CHAVES = {Estoque: ("edicao_id", "loja_id"), Favorito: ("cliente_id", "livro_id"),
          Alerta: ("cliente_id", "edicao_id", "loja_id"), Cupom: ("codigo",)}
CABECALHO = "# livraria — uma linha por registro: <tipo><TAB><json>"


class RepositorioTxt(RepositorioLivraria):
    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self.trava = threading.RLock()
        self.aberta = None  # dados da transação em andamento
        with self.transacao():
            if not any(self.aberta.values()):
                for registro in dados_exemplo():
                    self.salvar(registro)

    def listar(self, tipo):
        with self.trava:
            dados = self.aberta if self.aberta is not None else self._ler()
            return [copy.deepcopy(r) for r in dados.get(tipo.__name__.lower(), [])]

    def salvar(self, registro):
        with self.transacao():
            lista = self.aberta.setdefault(type(registro).__name__.lower(), [])
            campos = CHAVES.get(type(registro), ("id",))
            if campos == ("id",) and registro.id == 0:
                registro.id = max((r.id for r in lista), default=0) + 1
            chave = tuple(getattr(registro, c) for c in campos)
            for i, atual in enumerate(lista):
                if tuple(getattr(atual, c) for c in campos) == chave:
                    lista[i] = copy.deepcopy(registro)
                    break
            else:
                lista.append(copy.deepcopy(registro))
            return registro

    def remover(self, registro):
        with self.transacao():
            lista = self.aberta.get(type(registro).__name__.lower(), [])
            campos = CHAVES.get(type(registro), ("id",))
            chave = tuple(getattr(registro, c) for c in campos)
            lista[:] = [r for r in lista if tuple(getattr(r, c) for c in campos) != chave]

    @contextmanager
    def transacao(self):
        with self.trava:
            if self.aberta is not None:  # já dentro de uma transação
                yield
                return
            self.aberta = self._ler()
            try:
                yield
                self._gravar(self.aberta)
            finally:
                self.aberta = None  # em caso de erro nada é gravado

    def _ler(self):
        dados = {tipo: [] for tipo in TIPOS}
        if self.caminho.exists():
            for linha in self.caminho.read_text(encoding="utf-8").splitlines():
                if linha and not linha.startswith("#"):
                    tipo, conteudo = linha.split("\t", 1)
                    dados[tipo].append(TIPOS[tipo](**json.loads(conteudo)))
        return dados

    def _gravar(self, dados):
        linhas = [CABECALHO] + [f"{tipo}\t{json.dumps(asdict(r), ensure_ascii=False, sort_keys=True)}"
                                for tipo, registros in dados.items() for r in registros]
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        descritor, temporario = tempfile.mkstemp(dir=self.caminho.parent, suffix=".tmp")
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas) + "\n")
        os.replace(temporario, self.caminho)  # troca atômica: o arquivo nunca fica pela metade
