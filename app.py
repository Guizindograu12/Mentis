
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
import random

from sqlalchemy import select
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
    buscar_resultado,
    salvar_resultado,
    listar_perguntas,
    buscar_ultimo_resultado_usuario,
    EmotionalCheckIn,
    Teste,
    Resposta,
    Pergunta,
    Resultado
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

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ==========================================
# BANCO DE DADOS
# ==========================================

db.init_app(app)

with app.app_context():

    criar_tabelas()

    sincronizar_perguntas(PERGUNTAS)


# ==========================================
# SORTEIO DAS PERGUNTAS
# ==========================================

QUANTIDADE_PERGUNTAS = 25


def selecionar_perguntas_teste():
    """
    Sorteia 25 perguntas distintas para uma nova tentativa.

    Os IDs são guardados na sessão para manter a seleção
    durante o preenchimento do questionário.
    """

    perguntas_disponiveis = listar_perguntas()

    if len(perguntas_disponiveis) < QUANTIDADE_PERGUNTAS:

        raise RuntimeError(
            "O banco precisa ter pelo menos 25 perguntas cadastradas."
        )

    perguntas_sorteadas = random.sample(
        perguntas_disponiveis,
        QUANTIDADE_PERGUNTAS
    )

    session["perguntas_teste_ids"] = [
        pergunta.id
        for pergunta in perguntas_sorteadas
    ]

    return perguntas_sorteadas


def obter_perguntas_teste():
    """
    Recupera as perguntas da tentativa atual.

    Se a página for atualizada, mantém as mesmas perguntas.
    """

    ids_selecionados = session.get(
        "perguntas_teste_ids"
    )

    if (
        not isinstance(ids_selecionados, list)
        or len(ids_selecionados) != QUANTIDADE_PERGUNTAS
        or len(set(ids_selecionados)) != QUANTIDADE_PERGUNTAS
    ):

        return selecionar_perguntas_teste()

    perguntas_disponiveis = listar_perguntas()

    perguntas_por_id = {
        pergunta.id: pergunta
        for pergunta in perguntas_disponiveis
    }

    if any(
        pergunta_id not in perguntas_por_id
        for pergunta_id in ids_selecionados
    ):

        return selecionar_perguntas_teste()

    return [
        perguntas_por_id[pergunta_id]
        for pergunta_id in ids_selecionados
    ]


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

    try:

        selecionar_perguntas_teste()

        return redirect(url_for("teste"))

    except Exception:

        app.logger.exception(
            "Erro ao selecionar perguntas para o teste."
        )

        return (
            "Não foi possível iniciar o teste. "
            "Verifique se existem pelo menos 25 perguntas cadastradas.",
            500
        )


# ==========================================
# LOGIN
# ==========================================

@app.route("/login")
def login():

    return render_template("login.html")


@app.route("/entrar", methods=["POST"])
def entrar():

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    senha = request.form.get("senha", "")

    if not email or not senha:

        return render_template(
            "login.html",
            erro="Preencha o e-mail e a senha."
        )

    usuario_id = validar_usuario(
        email,
        senha
    )

    if usuario_id is not None:

        session.clear()

        session["usuario_id"] = usuario_id
        session["usuario"] = email

        return redirect(url_for("home"))

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
        "email",
        ""
    ).strip().lower()

    senha = request.form.get("senha", "")

    if not email or not senha:

        return render_template(
            "login.html",
            erro="Preencha o e-mail e a senha."
        )

    sucesso = cadastrar_usuario(
        email,
        senha
    )

    if sucesso:

        usuario_id = validar_usuario(
            email,
            senha
        )

        if usuario_id is None:

            return render_template(
                "login.html",
                erro="Não foi possível entrar na conta criada."
            )

        session.clear()

        session["usuario_id"] = usuario_id
        session["usuario"] = email

        return redirect(url_for("home"))

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

    try:

        perguntas = obter_perguntas_teste()

        return render_template(
            "teste.html",
            perguntas=perguntas
        )

    except Exception:

        app.logger.exception(
            "Erro ao carregar as perguntas do teste."
        )

        return (
            "Não foi possível carregar o questionário. "
            "Tente novamente mais tarde.",
            500
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

    respostas = request.get_json(silent=True)

    if not isinstance(respostas, dict) or not respostas:

        return jsonify({
            "status": "erro",
            "mensagem": "Nenhuma resposta válida foi enviada."
        }), 400

    ids_selecionados = session.get(
        "perguntas_teste_ids"
    )

    if (
        not isinstance(ids_selecionados, list)
        or len(ids_selecionados) != QUANTIDADE_PERGUNTAS
        or len(set(ids_selecionados)) != QUANTIDADE_PERGUNTAS
    ):

        return jsonify({
            "status": "erro",
            "mensagem": (
                "A seleção de perguntas expirou. "
                "Inicie um novo teste."
            )
        }), 400

    ids_enviados = set()

    for chave in respostas:

        if not isinstance(chave, str):

            return jsonify({
                "status": "erro",
                "mensagem": "Foi enviada uma pergunta inválida."
            }), 400

        if not chave.startswith("p"):

            return jsonify({
                "status": "erro",
                "mensagem": "Foi enviada uma pergunta inválida."
            }), 400

        try:

            pergunta_id = int(chave[1:])

        except (ValueError, TypeError):

            return jsonify({
                "status": "erro",
                "mensagem": "Foi enviada uma pergunta inválida."
            }), 400

        ids_enviados.add(pergunta_id)

    if (
        len(ids_enviados) != QUANTIDADE_PERGUNTAS
        or ids_enviados != set(ids_selecionados)
    ):

        return jsonify({
            "status": "erro",
            "mensagem": (
                "As respostas não correspondem às 25 perguntas "
                "deste teste. Atualize a página e tente novamente."
            )
        }), 400

    try:

        # ------------------------------------------
        # 1. CRIAR NOVA TENTATIVA
        # ------------------------------------------

        teste_db = criar_teste(usuario_id)

        # ------------------------------------------
        # 2. SALVAR RESPOSTAS
        # ------------------------------------------

        salvar_respostas(
            teste_db,
            respostas
        )

        # ------------------------------------------
        # 3. BUSCAR RESPOSTAS E DADOS DAS PERGUNTAS
        # ------------------------------------------
        #
        # Aqui selecionamos diretamente as colunas
        # da pergunta, incluindo peso e invertida.
        #
        # Assim, não precisamos acessar:
        # pergunta.peso
        # pergunta.invertida
        #
        # Isso evita o problema anterior com atributos
        # ausentes no objeto Pergunta.

        linhas = db.session.execute(
            select(
                Resposta.pergunta_id,
                Resposta.resposta,
                Pergunta.texto,
                Pergunta.categoria,
                Pergunta.peso,
                Pergunta.invertida
            )
            .join(
                Pergunta,
                Resposta.pergunta_id == Pergunta.id
            )
            .where(
                Resposta.teste_id == teste_db.id
            )
            .order_by(
                Pergunta.ordem
            )
        ).all()

        respostas_com_perguntas = []

        for linha in linhas:

            pergunta_id = linha[0]
            resposta_valor = linha[1]
            texto = linha[2]
            categoria = linha[3]
            peso = linha[4]
            invertida = linha[5]

            # Valores padrão caso algum registro antigo
            # esteja sem configuração de peso ou inversão.

            if peso is None:
                peso = 1.00

            if invertida is None:
                invertida = False

            respostas_com_perguntas.append({

                "pergunta_id": pergunta_id,

                "texto": texto,

                "categoria": categoria,

                "resposta": resposta_valor,

                "peso": float(peso),

                "invertida": bool(invertida)

            })

        # ------------------------------------------
        # 4. VALIDAR RECUPERAÇÃO DAS RESPOSTAS
        # ------------------------------------------

        if len(respostas_com_perguntas) != QUANTIDADE_PERGUNTAS:

            raise ValueError(
                "Não foi possível recuperar todas as respostas do teste."
            )

        # ------------------------------------------
        # 5. ANALISAR RESPOSTAS
        # ------------------------------------------

        analise = analisar_respostas(
            respostas_com_perguntas
        )

        # ------------------------------------------
        # 6. SALVAR RESULTADO
        # ------------------------------------------

        resultado_db = salvar_resultado(
            teste_db,
            analise
        )

        db.session.commit()

        # ------------------------------------------
        # 7. GUARDAR IDENTIFICADORES
        # ------------------------------------------

        teste_id = teste_db.id
        resultado_id = resultado_db.id

        # ------------------------------------------
        # 8. LIMPAR PERGUNTAS DA SESSÃO
        # ------------------------------------------
        #
        # Ao iniciar outro teste, serão sorteadas
        # 25 novas perguntas.

        session.pop(
            "perguntas_teste_ids",
            None
        )

        # ------------------------------------------
        # 9. REGISTRO NO TERMINAL
        # ------------------------------------------

        print()
        print("===================================")
        print("NOVO TESTE REALIZADO")
        print("Teste ID:", teste_id)
        print("Usuário ID:", usuario_id)
        print("E-mail:", session.get("usuario"))
        print(
            "Quantidade de perguntas:",
            len(respostas_com_perguntas)
        )
        print(
            "Percentual geral:",
            analise["percentual_geral"]
        )
        print(
            "Classificação:",
            analise["classificacao_geral"]
        )
        print("===================================")
        print()

        # ------------------------------------------
        # 10. RESPOSTA PARA O JAVASCRIPT
        # ------------------------------------------

        return jsonify({

            "status": "sucesso",

            "mensagem": "Respostas analisadas e salvas com sucesso.",

            "teste_id": teste_id,

            "resultado_id": resultado_id,

            "resultado_url": url_for(
                "resultado",
                teste_id=teste_id
            )

        })

    except ValueError as erro:

        db.session.rollback()

        return jsonify({

            "status": "erro",

            "mensagem": str(erro)

        }), 400

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Erro ao processar o questionário."
        )

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

    relatorio = montar_relatorio(
        resultado_db
    )

    return render_template(
        "resultado.html",
        relatorio=relatorio,
        usuario=session.get("usuario")
    )


# ==========================================
# PERFIL / PAINEL DE ACOMPANHAMENTO
# ==========================================

@app.route("/perfil")
def perfil():

    if "usuario_id" not in session:

        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]

    resultados_db = db.session.execute(
        select(
            Resultado,
            Teste.data_teste
        )
        .join(
            Teste,
            Resultado.teste_id == Teste.id
        )
        .where(
            Teste.usuario_id == usuario_id
        )
        .order_by(
            Teste.data_teste.asc(),
            Resultado.id.asc()
        )
    ).all()

    historico = []
    historico_categorias = {}

    for resultado_db, data_teste in resultados_db:

        data_formatada = (
            data_teste.strftime("%d/%m/%Y")
            if data_teste
            else "Data indisponível"
        )

        percentual = float(
            resultado_db.percentual_geral
        )

        classificacao = resultado_db.classificacao_geral

        categorias_teste = []

        for categoria in resultado_db.categorias:

            nome_categoria = categoria.categoria

            percentual_categoria = float(
                categoria.percentual
            )

            categorias_teste.append({

                "nome": nome_categoria,

                "percentual": percentual_categoria

            })

            historico_categorias.setdefault(
                nome_categoria,
                []
            ).append({

                "data": data_formatada,

                "percentual": percentual_categoria

            })

        historico.append({

            "teste_id": resultado_db.teste_id,

            "data": data_formatada,

            "data_label": data_formatada,

            "percentual": percentual,

            "classificacao": classificacao,

            "categorias": categorias_teste

        })

    # ------------------------------------------
    # CHECK-INS EMOCIONAIS
    # ------------------------------------------

    checkins_db = db.session.execute(
        select(EmotionalCheckIn)
        .where(
            EmotionalCheckIn.usuario_id == usuario_id
        )
        .order_by(
            EmotionalCheckIn.data_registro.asc()
        )
    ).scalars().all()

    checkins = [

        {
            "humor": checkin.humor,

            "data": (
                checkin.data_registro.strftime("%d/%m/%Y")
                if checkin.data_registro
                else "Data indisponível"
            )
        }

        for checkin in checkins_db

    ]

    # ------------------------------------------
    # MÉDIA DOS RESULTADOS
    # ------------------------------------------

    media_testes = (

        round(
            sum(
                item["percentual"]
                for item in historico
            ) / len(historico),
            2
        )

        if historico

        else None

    )

    # ------------------------------------------
    # MÉDIA DOS CHECK-INS
    # ------------------------------------------

    media_humor = (

        round(
            sum(
                item["humor"]
                for item in checkins
            ) / len(checkins),
            1
        )

        if checkins

        else None

    )

    ultimo = historico[-1] if historico else None

    testes = [

        {
            "teste_id": item["teste_id"],

            "data": item["data"],

            "data_label": item["data_label"],

            "percentual": item["percentual"],

            "classificacao": item["classificacao"],

            "categorias": item["categorias"]

        }

        for item in historico

    ]

    moods = checkins

    ultimo_teste = (
        dict(ultimo)
        if ultimo
        else None
    )

    categorias_media = {

        nome: round(
            sum(
                item["percentual"]
                for item in valores
            ) / len(valores),
            2
        )

        for nome, valores in historico_categorias.items()

        if valores

    }

    return render_template(

        "perfil.html",

        historico=historico,

        historico_categorias=historico_categorias,

        checkins=checkins,

        ultimo=ultimo,

        media_testes=media_testes,

        media_humor=media_humor,

        total_testes=len(historico),

        categorias_media=categorias_media,

        testes=testes,

        moods=moods,

        ultimo_teste=ultimo_teste

    )


# ==========================================
# CHECK-IN EMOCIONAL
# ==========================================

@app.route("/checkin-humor", methods=["POST"])
def checkin_humor():

    if "usuario_id" not in session:

        return jsonify({

            "mensagem": "Você precisa estar logado."

        }), 401

    dados = request.get_json(silent=True) or {}

    humor = dados.get("humor")

    if (
        not isinstance(humor, int)
        or isinstance(humor, bool)
        or humor < 1
        or humor > 10
    ):

        return jsonify({

            "mensagem": (
                "Selecione um valor de humor entre 1 e 10."
            )

        }), 400

    try:

        checkin = EmotionalCheckIn(

            usuario_id=session["usuario_id"],

            humor=humor

        )

        db.session.add(checkin)

        db.session.commit()

        checkins = db.session.execute(
            select(EmotionalCheckIn).where(
                EmotionalCheckIn.usuario_id
                == session["usuario_id"]
            )
        ).scalars().all()

        media_humor = round(

            sum(
                item.humor
                for item in checkins
            ) / len(checkins),

            1

        )

        return jsonify({

            "mensagem": "Check-in registrado com sucesso.",

            "humor": humor,

            "media_humor": media_humor

        })

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Erro ao salvar o check-in emocional."
        )

        return jsonify({

            "mensagem": "Não foi possível salvar o check-in."

        }), 500


# ==========================================
# OBRIGADO
# ==========================================

@app.route("/obrigado")
def obrigado():

    return render_template("obrigado.html")


# ==========================================
# RECUPERAÇÃO DE SENHA
# ==========================================

@app.route("/recuperar-senha", methods=["POST"])
def recuperar_senha():

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    nova_senha = request.form.get(
        "nova_senha",
        ""
    )

    confirmar_senha = request.form.get(
        "confirmar_senha",
        ""
    )

    def resposta_recuperacao(mensagem, sucesso=False):

        return render_template(

            "login.html",

            recovery_mode=True,

            erro=None if sucesso else mensagem,

            sucesso=mensagem if sucesso else None

        )

    if not email or not nova_senha or not confirmar_senha:

        return resposta_recuperacao(
            "Preencha todos os campos."
        )

    if len(nova_senha) < 8:

        return resposta_recuperacao(
            "A senha precisa ter pelo menos 8 caracteres."
        )

    if nova_senha != confirmar_senha:

        return resposta_recuperacao(
            "As senhas não são iguais."
        )

    usuario = buscar_usuario_por_email(email)

    if usuario is None:

        return resposta_recuperacao(
            "Não encontramos uma conta com esse e-mail."
        )

    if alterar_senha(email, nova_senha):

        return resposta_recuperacao(
            "Senha alterada! Agora você pode voltar ao login.",
            sucesso=True
        )

    return resposta_recuperacao(
        "Não foi possível alterar a senha. Tente novamente."
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
