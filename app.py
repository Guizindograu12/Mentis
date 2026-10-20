
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session
)

import os

from dotenv import load_dotenv

from backend.database import (
    db,
    criar_tabelas,
    sincronizar_perguntas,
    cadastrar_usuario,
    validar_usuario,
    criar_teste,
    salvar_respostas,
    buscar_usuario_por_email,
    alterar_senha,
    buscar_teste,
    buscar_resultado,
    salvar_resultado,
    listar_perguntas,
    buscar_ultimo_resultado_usuario
)

from backend.perguntas import PERGUNTAS
from backend.analise import analisar_respostas
from backend.relatorio import montar_relatorio


# ==========================================
# CONFIGURAÇÕES
# ==========================================

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY não configurada. "
        "Adicione uma chave secreta ao arquivo .env."
    )

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não configurada. "
        "Crie um arquivo .env na raiz do projeto."
    )

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ==========================================
# BANCO DE DADOS
# ==========================================

db.init_app(app)

with app.app_context():
    criar_tabelas()
    sincronizar_perguntas(PERGUNTAS)


# ==========================================
# USUÁRIO DISPONÍVEL NOS HTMLS
# ==========================================

@app.context_processor
def dados_usuario():
    return {
        "usuario": session.get("usuario"),
        "usuario_id": session.get("usuario_id")
    }


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    ultimo_resultado_id = None

    if "usuario_id" in session:
        ultimo_resultado_id = buscar_ultimo_resultado_usuario(
            session["usuario_id"]
        )

    return render_template(
        "index.html",
        ultimo_resultado_id=ultimo_resultado_id
    )


# ==========================================
# INICIAR TESTE
# ==========================================

@app.route("/iniciar-teste")
def iniciar_teste():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    ultimo_resultado_id = buscar_ultimo_resultado_usuario(
        session["usuario_id"]
    )

    if ultimo_resultado_id is not None:
        return redirect(
            url_for(
                "resultado",
                teste_id=ultimo_resultado_id
            )
        )

    return redirect(url_for("teste"))


# ==========================================
# LOGIN
# ==========================================

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/entrar", methods=["POST"])
def entrar():
    email = request.form.get(
        "email", ""
    ).strip().lower()

    senha = request.form.get("senha", "")

    if not email or not senha:
        return render_template(
            "login.html",
            erro="Preencha o e-mail e a senha."
        )

    usuario_id = validar_usuario(email, senha)

    if usuario_id is not None:
        session["usuario_id"] = usuario_id
        session["usuario"] = email

        return redirect(url_for("iniciar_teste"))

    return render_template(
        "login.html",
        erro="E-mail ou senha incorretos."
    )


# ==========================================
# CADASTRO
# ==========================================

@app.route("/cadastro", methods=["POST"])
def cadastro():
    email = request.form.get(
        "email", ""
    ).strip().lower()

    senha = request.form.get("senha", "")

    if not email or not senha:
        return render_template(
            "login.html",
            erro="Preencha o e-mail e a senha."
        )

    sucesso = cadastrar_usuario(email, senha)

    if sucesso:
        usuario_id = validar_usuario(email, senha)

        if usuario_id is None:
            return render_template(
                "login.html",
                erro="Não foi possível entrar na conta criada."
            )

        session["usuario_id"] = usuario_id
        session["usuario"] = email

        return redirect(url_for("iniciar_teste"))

    return render_template(
        "login.html",
        erro="Este e-mail já está cadastrado."
    )


# ==========================================
# TESTE
# ==========================================

@app.route("/teste")
def teste():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    ultimo_resultado_id = buscar_ultimo_resultado_usuario(
        session["usuario_id"]
    )

    if ultimo_resultado_id is not None:
        return redirect(
            url_for(
                "resultado",
                teste_id=ultimo_resultado_id
            )
        )

    perguntas = listar_perguntas()

    return render_template(
        "teste.html",
        perguntas=perguntas
    )


# ==========================================
# ANALISAR, SALVAR E GERAR RESULTADO
# ==========================================

@app.route("/analisar", methods=["POST"])
def analisar():
    if "usuario_id" not in session:
        return jsonify({
            "status": "erro",
            "mensagem": "Você precisa estar logado."
        }), 401

    usuario_id = session.get("usuario_id")

    # Impede o envio de um novo teste caso já exista
    # um resultado concluído para esta conta.
    ultimo_resultado_id = buscar_ultimo_resultado_usuario(
        usuario_id
    )

    if ultimo_resultado_id is not None:
        return jsonify({
            "status": "ja_concluido",
            "mensagem": "Você já concluiu o questionário.",
            "resultado_url": url_for(
                "resultado",
                teste_id=ultimo_resultado_id
            )
        }), 409

    respostas = request.get_json(silent=True)

    if not respostas:
        return jsonify({
            "status": "erro",
            "mensagem": "Nenhuma resposta foi enviada."
        }), 400

    try:
        # ----------------------------------
        # CRIA O TESTE
        # ----------------------------------

        teste = criar_teste(usuario_id)

        # ----------------------------------
        # SALVA RESPOSTAS
        # ----------------------------------

        salvar_respostas(teste, respostas)

        # ----------------------------------
        # MONTA DADOS PARA ANÁLISE
        # ----------------------------------

        linhas = buscar_teste(
            teste.id,
            usuario_id
        )

        respostas_com_perguntas = [
            {
                "pergunta_id": linha[4],
                "texto": linha[5],
                "categoria": linha[6],
                "resposta": linha[7]
            }
            for linha in linhas
        ]

        # ----------------------------------
        # CALCULA RESULTADO
        # ----------------------------------

        analise = analisar_respostas(
            respostas_com_perguntas
        )

        # ----------------------------------
        # SALVA RESULTADO
        # ----------------------------------

        resultado = salvar_resultado(
            teste,
            analise
        )

        db.session.commit()

        print()
        print("===================================")
        print("NOVO TESTE REALIZADO")
        print("===================================")
        print("Teste ID:", teste.id)
        print("Usuário ID:", usuario_id)
        print("E-mail:", session.get("usuario"))
        print("Resultado:", analise)
        print("===================================")
        print()

        return jsonify({
            "status": "sucesso",
            "mensagem": "Respostas analisadas e salvas com sucesso.",
            "teste_id": teste.id,
            "resultado_id": resultado.id,
            "resultado_url": url_for(
                "resultado",
                teste_id=teste.id
            )
        })

    except ValueError as erro:
        db.session.rollback()

        return jsonify({
            "status": "erro",
            "mensagem": str(erro)
        }), 400

    except Exception as erro:
        db.session.rollback()

        print("Erro ao processar teste:", erro)

        return jsonify({
            "status": "erro",
            "mensagem": "Não foi possível processar o teste."
        }), 500


# ==========================================
# RESULTADO / RELATÓRIO
# ==========================================

@app.route("/resultado/<int:teste_id>")
def resultado(teste_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    resultado_db = buscar_resultado(
        teste_id,
        session.get("usuario_id")
    )

    if resultado_db is None:
        return redirect(url_for("iniciar_teste"))

    relatorio = montar_relatorio(resultado_db)

    return render_template(
        "resultado.html",
        relatorio=relatorio,
        usuario=session.get("usuario")
    )


# ==========================================
# OBRIGADO
# ==========================================

@app.route("/obrigado")
def obrigado():
    return render_template("obrigado.html")


# ==========================================
# ESQUECI MINHA SENHA
# ==========================================

@app.route("/esqueci-senha")
def esqueci_senha():
    return render_template("esqueci_senha.html")


@app.route("/recuperar-senha", methods=["POST"])
def recuperar_senha():
    email = request.form.get(
        "email", ""
    ).strip().lower()

    nova_senha = request.form.get("nova_senha", "")
    confirmar_senha = request.form.get("confirmar_senha", "")

    if nova_senha != confirmar_senha:
        return render_template(
            "esqueci_senha.html",
            erro="As senhas não são iguais."
        )

    usuario = buscar_usuario_por_email(email)

    if usuario is None:
        return render_template(
            "esqueci_senha.html",
            erro="Nenhuma conta foi encontrada com esse e-mail."
        )

    sucesso = alterar_senha(email, nova_senha)

    if sucesso:
        return render_template(
            "esqueci_senha.html",
            sucesso=(
                "Senha alterada com sucesso! "
                "Agora você pode entrar na sua conta."
            )
        )

    return render_template(
        "esqueci_senha.html",
        erro="Não foi possível alterar a senha."
    )


# ==========================================
# SAIR
# ==========================================

@app.route("/logout")
def logout():
    session.clear()

    return redirect(url_for("home"))


# ==========================================
# SERVIDOR
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
