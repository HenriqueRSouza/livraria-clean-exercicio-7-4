"""Recebe os dados da tela (dicionários de texto), converte, chama o caso de uso e devolve dados/mensagens."""
from livraria.controllers.formatos import reais
from livraria.entities import RegraInvalida


def inteiro(form, campo):
    try:
        return int(form[campo])
    except (KeyError, TypeError, ValueError) as exc:
        raise RegraInvalida("Dados do formulário inválidos.") from exc


def com_cupom(pedido):
    return f" com cupom {pedido.cupom}" if pedido.cupom else ""


class LivrariaController:
    def __init__(self, catalogo, clientes, pedidos):
        self.catalogo = catalogo
        self.clientes = clientes
        self.pedidos = pedidos

    # páginas
    def cliente_atual(self, cliente_id):
        try:
            return self.clientes.obter(cliente_id) if cliente_id else None
        except RegraInvalida:  # sessão antiga de um cliente que não existe mais no arquivo
            return None

    def pagina_catalogo(self, args):
        return {"pagina": "catalogo", "livros": self.catalogo.buscar_livros(
            args.get("titulo", ""), args.get("autor", ""), args.get("genero", ""))}

    def pagina_livro(self, livro_id, cliente_id=None):
        livro = self.catalogo.detalhes_livro(livro_id)
        minha = next((a for a in livro["avaliacoes"] if cliente_id and a.cliente_id == cliente_id), None)
        return {"pagina": "livro", "livro": livro, "minha_avaliacao": minha}

    def pagina_lojas(self, args):
        return {"pagina": "lojas", "lojas": self.catalogo.listar_lojas(args.get("bairro", ""))}

    def pagina_cliente(self, cliente_id):
        if not cliente_id:
            return {"pagina": "entrada"}
        return {"pagina": "cliente", "historico": self.pedidos.historico(cliente_id),
                "favoritos": self.clientes.favoritos(cliente_id),
                "recomendacoes": self.clientes.recomendacoes(cliente_id),
                "notificacoes": self.clientes.notificacoes(cliente_id),
                "avaliacoes": self.catalogo.avaliacoes_do_cliente(cliente_id)}

    # ações (devolvem a mensagem para o usuário)
    def cadastrar(self, form):
        return self.clientes.cadastrar(form.get("nome", ""), form.get("email", ""), form.get("bairro", ""),
                                       form.get("interesses", ""))

    def entrar(self, form):
        return self.clientes.entrar(form.get("email", "")).id

    def favoritar(self, cliente_id, livro_id, adicionar):
        self.clientes.favoritar(cliente_id, livro_id, adicionar)

    def reservar(self, cliente_id, form):
        r = self.pedidos.reservar(cliente_id, inteiro(form, "edicao_id"), inteiro(form, "loja_id"), form.get("cupom", ""))
        return (f"Reserva confirmada: {r.codigo} por {reais(r.preco_centavos)}{com_cupom(r)}. "
                "Retire na unidade selecionada; pagamento simulado apenas na retirada.")

    def comprar(self, cliente_id, form):
        c = self.pedidos.comprar(cliente_id, inteiro(form, "edicao_id"), inteiro(form, "loja_id"), form.get("cupom", ""))
        return f"Compra presencial simulada registrada: #{c.id} por {reais(c.preco_centavos)}{com_cupom(c)} (sem cobrança real)."

    def retirar(self, cliente_id, codigo):
        self.pedidos.retirar(cliente_id, codigo)
        return f"Retirada de {codigo} concluída; compra simulada registrada."

    def cancelar(self, cliente_id, codigo):
        self.pedidos.cancelar(cliente_id, codigo)
        return f"Reserva {codigo} cancelada; estoque devolvido."

    def alertar(self, cliente_id, form):
        self.pedidos.alertar(cliente_id, inteiro(form, "edicao_id"), inteiro(form, "loja_id"))
        return "Alerta local registrado; consulte sua área após simular reposição."

    def repor(self, form):
        self.pedidos.repor(inteiro(form, "edicao_id"), inteiro(form, "loja_id"))
        return "Reposição simulada: uma unidade adicionada e notificações locais geradas."

    def avaliar(self, cliente_id, livro_id, form):
        self.catalogo.avaliar(cliente_id, livro_id, inteiro(form, "nota"), form.get("texto", ""))
        return "Avaliação registrada. Obrigado!"
