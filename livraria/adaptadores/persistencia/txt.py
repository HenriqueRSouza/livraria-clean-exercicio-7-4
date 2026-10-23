"""Implementação das portas sobre um arquivo TXT legível: uma linha por registro, `<tipo>\\t<json>`.

O adaptador conhece o formato; o acesso físico ao arquivo (leitura, gravação atômica, trava)
é um driver do anel de frameworks, injetado pela raiz de composição.
"""
import json

from livraria.adaptadores.persistencia.registros import TIPOS, UnidadeDeTrabalhoRegistros, chave

CABECALHO = "# livraria — persistência TXT: uma linha por registro, <tipo><TAB><json>"


def serializar(dados):
    linhas = [CABECALHO]
    for tipo in TIPOS:
        for registro in dados.get(tipo, {}).values():
            linhas.append(f"{tipo}\t{json.dumps(registro, ensure_ascii=False, sort_keys=True)}")
    return "\n".join(linhas) + "\n"


def desserializar(texto):
    dados = {tipo: {} for tipo in TIPOS}
    for numero, linha in enumerate(texto.splitlines(), 1):
        if not linha.strip() or linha.startswith("#"):
            continue
        tipo, _, conteudo = linha.partition("\t")
        if tipo not in TIPOS:
            raise ValueError(f"Linha {numero}: tipo de registro desconhecido {tipo!r}.")
        registro = json.loads(conteudo)
        dados[tipo][chave(tipo, registro)] = registro
    return dados


class UnidadeDeTrabalhoTxt(UnidadeDeTrabalhoRegistros):
    """`arquivo` precisa oferecer `trava`, `ler() -> str` ("" se ausente) e `gravar(texto)`."""

    def __init__(self, arquivo, dados_iniciais=None):
        self.arquivo = arquivo
        self.trava = arquivo.trava
        self.dados_iniciais = dados_iniciais or {}

    def _carregar(self):
        texto = self.arquivo.ler()
        if texto.strip():
            return desserializar(texto)
        self.arquivo.gravar(serializar(self.dados_iniciais))  # primeira execução: semeia o catálogo
        return desserializar(self.arquivo.ler())

    def _persistir(self, dados):
        self.arquivo.gravar(serializar(dados))
