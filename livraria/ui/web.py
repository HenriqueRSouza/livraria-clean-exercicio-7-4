import os
from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from livraria.controllers.formatos import nota_media, reais
from livraria.entities import RegraInvalida


def create_app(controller):
    app = Flask(__name__)
    app.secret_key = os.environ.get("LIVRARIA_SECRET", "chave-local-apenas-demonstracao")
    app.add_template_filter(reais, "reais")
    app.add_template_filter(nota_media, "nota_media")

    @app.errorhandler(RegraInvalida)
    def erro(exc):
        flash(str(exc), "erro")
        return redirect(request.referrer or url_for("catalogo"))

    def logado(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("cliente_id"):
                flash("Cadastre-se ou entre para continuar.", "erro")
                return redirect(url_for("area"))
            return fn(*args, **kwargs)
        return wrapper

    @app.context_processor
    def contexto():
        return {"cliente_atual": controller.cliente_atual(session.get("cliente_id"))}

    @app.get("/")
    def catalogo():
        return render_template("index.html", **controller.pagina_catalogo(request.args))

    @app.get("/livro/<int:livro_id>")
    def livro(livro_id):
        return render_template("index.html", **controller.pagina_livro(livro_id, session.get("cliente_id")))

    @app.get("/lojas")
    def lojas():
        return render_template("index.html", **controller.pagina_lojas(request.args))

    @app.get("/cliente")
    def area():
        return render_template("index.html", **controller.pagina_cliente(session.get("cliente_id")))

    @app.post("/cadastro")
    def cadastro():
        session["cliente_id"] = controller.cadastrar(request.form)
        flash("Cadastro concluído. Esta é uma sessão local de demonstração.")
        return redirect(url_for("area"))

    @app.post("/entrar")
    def entrar():
        session["cliente_id"] = controller.entrar(request.form)
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
        controller.favoritar(session["cliente_id"], livro_id, acao == "adicionar")
        return redirect(url_for("livro", livro_id=livro_id) if acao == "adicionar" else url_for("area"))

    @app.post("/reservar")
    @logado
    def reservar():
        flash(controller.reservar(session["cliente_id"], request.form))
        return redirect(url_for("area"))

    @app.post("/comprar")
    @logado
    def comprar():
        flash(controller.comprar(session["cliente_id"], request.form))
        return redirect(url_for("area"))

    @app.post("/reserva/<codigo>/<acao>")
    @logado
    def reserva_acao(codigo, acao):
        if acao == "retirar":
            flash(controller.retirar(session["cliente_id"], codigo))
        elif acao == "cancelar":
            flash(controller.cancelar(session["cliente_id"], codigo))
        else:
            abort(404)
        return redirect(url_for("area"))

    @app.post("/alertar")
    @logado
    def alertar():
        flash(controller.alertar(session["cliente_id"], request.form))
        return redirect(request.referrer or url_for("catalogo"))

    @app.post("/repor")
    def repor():
        flash(controller.repor(request.form))
        return redirect(request.referrer or url_for("catalogo"))

    @app.post("/avaliar/<int:livro_id>")
    @logado
    def avaliar(livro_id):
        flash(controller.avaliar(session["cliente_id"], livro_id, request.form))
        return redirect(url_for("livro", livro_id=livro_id))

    return app
