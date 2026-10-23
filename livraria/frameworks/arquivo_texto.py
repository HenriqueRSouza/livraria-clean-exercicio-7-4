"""Driver de arquivo: leitura e gravação atômica (arquivo temporário + os.replace) sob trava."""
import os
import tempfile
import threading
from pathlib import Path


class ArquivoTexto:
    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self.trava = threading.RLock()

    def ler(self):
        try:
            return self.caminho.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def gravar(self, texto):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        descritor, temporario = tempfile.mkstemp(dir=self.caminho.parent, prefix=f".{self.caminho.name}.", suffix=".tmp")
        try:
            with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
                arquivo.write(texto)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, self.caminho)
        except BaseException:
            Path(temporario).unlink(missing_ok=True)
            raise
