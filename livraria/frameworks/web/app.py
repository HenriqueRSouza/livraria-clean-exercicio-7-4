"""Interface HTTP (Flask): rotas finas que delegam ao controlador e renderizam templates."""
import os
from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from livraria.adaptadores.web import nota_media, reais
from livraria.entidades import RegraInvalida
from livraria.frameworks.composicao import montar_controlador


def create_app(caminho_txt=None):
    app = Flask(__name__)
    app.secret_key = os.environ.get("LIVRARIA_SECRET", "chave-local-apenas-demonstracao")
    controlador = montar_controlador(caminho_txt)
    app.add_template_filter(reais, "reais")
    app.add_template_filter(nota_media, "nota_media")

    @app.errorhandler(RegraInvalida)
    def erro(exc):
        flash(str(exc), "erro")
        return redirect(request.referrer or url_for("catalogo"))

    def logado(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not controlador.cliente_atual(session.get("cliente_id")):
                session.clear()
                flash("Cadastre-se ou entre para continuar.", "erro")
                return redirect(url_for("area"))
            return fn(*args, **kwargs)
        return wrapper

    def pagina(contexto):
        return render_template("index.html", **contexto)

    @app.context_processor
    def contexto():
        return {"cliente_atual": controlador.cliente_atual(session.get("cliente_id"))}

    @app.get("/")
    def catalogo():
        return pagina(controlador.catalogo(request.args))

    @app.get("/livro/<int:livro_id>")
    def livro(livro_id):
        return pagina(controlador.livro(livro_id, session.get("cliente_id")))

    @app.get("/lojas")
    def lojas():
        return pagina(controlador.lojas(request.args))

    @app.get("/cliente")
    def area():
        if not controlador.cliente_atual(session.get("cliente_id")):
            session.clear()
        return pagina(controlador.area(session.get("cliente_id")))

    @app.post("/cadastro")
    def cadastro():
        session["cliente_id"] = controlador.cadastrar(request.form)
        flash("Cadastro concluído. Esta é uma sessão local de demonstração.")
        return redirect(url_for("area"))

    @app.post("/entrar")
    def entrar():
        session["cliente_id"] = controlador.entrar(request.form)
        return redirect(url_for("area"))

    @app.post("/sair")
    def sair():
        session.clear()
        return redirect(url_for("catalogo"))

    @app.post("/favorito/<int:livro_id>/<acao>")
    @logado
    def favorito(livro_id, acao):
        if acao not in ("adicionar", "remover"):
            abort(404)
        controlador.favoritar(session["cliente_id"], livro_id, acao == "adicionar")
        return redirect(url_for("livro", livro_id=livro_id) if acao == "adicionar" else url_for("area"))

    @app.post("/reservar")
    @logado
    def reservar():
        flash(controlador.reservar(session["cliente_id"], request.form))
        return redirect(url_for("area"))

    @app.post("/comprar")
    @logado
    def comprar():
        flash(controlador.comprar(session["cliente_id"], request.form))
        return redirect(url_for("area"))

    @app.post("/reserva/<codigo>/<acao>")
    @logado
    def reserva_acao(codigo, acao):
        mensagem = controlador.reserva_acao(session["cliente_id"], codigo, acao)
        if mensagem is None:
            abort(404)
        flash(mensagem)
        return redirect(url_for("area"))

    @app.post("/alertar")
    @logado
    def alertar():
        flash(controlador.alertar(session["cliente_id"], request.form))
        return redirect(request.referrer or url_for("catalogo"))

    @app.post("/repor")
    def repor():
        flash(controlador.repor(request.form))
        return redirect(request.referrer or url_for("catalogo"))

    @app.post("/avaliar/<int:livro_id>")
    @logado
    def avaliar(livro_id):
        flash(controlador.avaliar(session["cliente_id"], livro_id, request.form))
        return redirect(url_for("livro", livro_id=livro_id))

    return app
