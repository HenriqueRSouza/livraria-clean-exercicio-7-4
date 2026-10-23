"""Controlador: converte dados da requisição (dicts de texto) em chamadas de casos de uso e devolve
modelos de visão ou mensagens. Não conhece Flask: recebe `args`/`form` como mapeamentos simples."""
from livraria.adaptadores.web.apresentador import reais
from livraria.entidades import RegraInvalida


def inteiro(form, campo):
    try:
        return int(form[campo])
    except (KeyError, TypeError, ValueError) as exc:
        raise RegraInvalida("Dados do formulário inválidos.") from exc


def com_cupom(pedido):
    return f" com cupom {pedido.cupom}" if pedido.cupom else ""


class ControladorLivraria:
    def __init__(self, casos):
        self.casos = casos

    # Consultas -------------------------------------------------------------
    def cliente_atual(self, cliente_id):
        if not cliente_id:
            return None
        try:
            return self.casos.obter_cliente.executar(cliente_id)
        except RegraInvalida:
            return None

    def catalogo(self, args):
        return {"pagina": "catalogo", "livros": self.casos.buscar_livros.executar(
            args.get("titulo", ""), args.get("autor", ""), args.get("genero", ""))}

    def livro(self, livro_id, cliente_id=None):
        livro = self.casos.detalhar_livro.executar(livro_id)
        minha = next((a for a in livro["avaliacoes"] if cliente_id and a["cliente_id"] == cliente_id), None)
        return {"pagina": "livro", "livro": livro, "minha_avaliacao": minha}

    def lojas(self, args):
        return {"pagina": "lojas", "lojas": self.casos.listar_lojas.executar(args.get("bairro", ""))}

    def area(self, cliente_id):
        if not cliente_id:
            return {"pagina": "entrada"}
        return {"pagina": "cliente", "historico": self.casos.consultar_historico.executar(cliente_id),
                "favoritos": self.casos.listar_favoritos.executar(cliente_id),
                "recomendacoes": self.casos.recomendar.executar(cliente_id),
                "notificacoes": self.casos.listar_notificacoes.executar(cliente_id),
                "avaliacoes": self.casos.avaliacoes_do_cliente.executar(cliente_id)}

    # Comandos (devolvem mensagens para o usuário) -------------------------
    def cadastrar(self, form):
        return self.casos.cadastrar.executar(form.get("nome", ""), form.get("email", ""),
                                             form.get("bairro", ""), form.get("interesses", ""))

    def entrar(self, form):
        return self.casos.entrar.executar(form.get("email", "")).id

    def favoritar(self, cliente_id, livro_id, adicionar):
        self.casos.favoritar.executar(cliente_id, livro_id, adicionar)

    def reservar(self, cliente_id, form):
        reserva = self.casos.reservar.executar(cliente_id, inteiro(form, "edicao_id"), inteiro(form, "loja_id"),
                                               form.get("cupom", ""))
        return (f"Reserva confirmada: {reserva.codigo} por {reais(reserva.preco_centavos)}{com_cupom(reserva)}. "
                "Retire na unidade selecionada; pagamento simulado apenas na retirada.")

    def comprar(self, cliente_id, form):
        compra = self.casos.comprar.executar(cliente_id, inteiro(form, "edicao_id"), inteiro(form, "loja_id"),
                                             form.get("cupom", ""))
        return (f"Compra presencial simulada registrada: #{compra.id} por {reais(compra.preco_centavos)}"
                f"{com_cupom(compra)} (sem cobrança real).")

    def reserva_acao(self, cliente_id, codigo, acao):
        if acao == "retirar":
            self.casos.retirar.executar(cliente_id, codigo)
            return f"Retirada de {codigo} concluída; compra simulada registrada."
        if acao == "cancelar":
            self.casos.cancelar.executar(cliente_id, codigo)
            return f"Reserva {codigo} cancelada; estoque devolvido."
        return None

    def alertar(self, cliente_id, form):
        self.casos.alertar.executar(cliente_id, inteiro(form, "edicao_id"), inteiro(form, "loja_id"))
        return "Alerta local registrado; consulte sua área após simular reposição."

    def repor(self, form):
        self.casos.repor.executar(inteiro(form, "edicao_id"), inteiro(form, "loja_id"))
        return "Reposição simulada: uma unidade adicionada e notificações locais geradas."

    def avaliar(self, cliente_id, livro_id, form):
        self.casos.avaliar.executar(cliente_id, livro_id, inteiro(form, "nota"), form.get("texto", ""))
        return "Avaliação registrada. Obrigado!"
