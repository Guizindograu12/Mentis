import json
import logging
import os
import secrets
import threading
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from flask import jsonify, request
from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

from backend.database import Usuario, alterar_senha, db


logger = logging.getLogger("mentis.recuperacao")


# ==========================================
# REGRAS DA RECUPERAÇÃO DE SENHA
# ==========================================

VALIDADE_MINUTOS = 15
MAX_TENTATIVAS = 5
INTERVALO_REENVIO_SEGUNDOS = 60
MAX_CODIGOS_POR_HORA = 5

MENSAGEM_ENVIO = (
    "Se esse e-mail estiver cadastrado, enviamos um código "
    "de 6 dígitos para ele. Confira também a caixa de spam."
)

MENSAGEM_CODIGO_INVALIDO = (
    "Código inválido ou expirado. "
    "Confira o código ou peça um novo."
)

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def agora():
    return datetime.now(timezone.utc)


# ==========================================
# TABELA DOS CÓDIGOS
# ==========================================

class CodigoRecuperacao(db.Model):

    __tablename__ = "codigos_recuperacao"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "usuarios.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # Guardamos só o hash do código, nunca o código em si.
    codigo_hash = db.Column(
        db.String(255),
        nullable=False
    )

    expira_em = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    tentativas = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    usado = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    criado_em = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=agora
    )


# ==========================================
# ENVIO DO E-MAIL (BREVO, POR API HTTPS)
# ==========================================

def enviar_email_codigo(destino, codigo):
    """
    Envia o código para UM destinatário usando a API do Brevo.
    Devolve True se o Brevo aceitou o envio.
    """

    chave_api = os.getenv("BREVO_API_KEY")
    remetente = os.getenv("EMAIL_REMETENTE")

    if not chave_api or not remetente:

        logger.error(
            "BREVO_API_KEY ou EMAIL_REMETENTE não configurados."
        )

        return False

    html = (
        "<div style=\"font-family:Arial,sans-serif;max-width:480px;"
        "margin:0 auto;color:#222;\">"
        "<h2 style=\"margin-bottom:8px;\">Recuperação de senha</h2>"
        "<p>Use o código abaixo para criar uma nova senha "
        "na Mentis:</p>"
        "<p style=\"font-size:32px;font-weight:bold;"
        "letter-spacing:8px;margin:24px 0;\">"
        + codigo +
        "</p>"
        "<p>Ele vale por "
        + str(VALIDADE_MINUTOS) +
        " minutos.</p>"
        "<p style=\"color:#777;font-size:13px;\">"
        "Se você não pediu isso, ignore este e-mail. "
        "Sua senha continua a mesma.</p>"
        "</div>"
    )

    corpo = {
        "sender": {
            "name": "Mentis",
            "email": remetente
        },
        "to": [
            {
                "email": destino
            }
        ],
        "subject": "Seu código de recuperação - Mentis",
        "htmlContent": html
    }

    pedido = urllib.request.Request(
        BREVO_URL,
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "api-key": chave_api,
            "accept": "application/json",
            "content-type": "application/json"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(pedido, timeout=15) as resposta:

            return 200 <= resposta.status < 300

    except urllib.error.HTTPError as erro:

        detalhe = ""

        try:
            detalhe = erro.read().decode("utf-8")[:500]
        except Exception:
            pass

        logger.error(
            "Brevo recusou o envio (HTTP %s): %s",
            erro.code,
            detalhe
        )

        return False

    except Exception:

        logger.exception(
            "Falha ao chamar a API do Brevo."
        )

        return False


def enviar_em_segundo_plano(destino, codigo):
    """
    Envia sem fazer a pessoa esperar. Também evita que o tempo
    de resposta revele se o e-mail existe ou não.
    """

    threading.Thread(
        target=enviar_email_codigo,
        args=(destino, codigo),
        daemon=True
    ).start()


# ==========================================
# ROTAS
# ==========================================

def registrar_rotas_recuperacao(app):

    # ------------------------------------------
    # 1. PEDIR O CÓDIGO
    # ------------------------------------------

    @app.route(
        "/recuperar-senha/enviar-codigo",
        methods=["POST"]
    )
    def recuperacao_enviar_codigo():

        dados = request.get_json(silent=True)

        if not isinstance(dados, dict):
            dados = {}

        email = dados.get("email", "")

        if not isinstance(email, str):
            email = ""

        email = email.strip().lower()

        if not email or "@" not in email or len(email) > 320:

            return jsonify({

                "status": "erro",

                "mensagem": "Digite um e-mail válido."

            }), 400

        # A resposta é sempre a mesma, exista o e-mail ou não.
        resposta = jsonify({

            "status": "sucesso",

            "mensagem": MENSAGEM_ENVIO

        })

        try:

            usuario_id = db.session.execute(
                select(Usuario.id).where(
                    Usuario.email == email
                )
            ).scalar_one_or_none()

            if usuario_id is None:
                return resposta

            momento = agora()

            # Intervalo mínimo entre dois envios.
            ultimo_envio = db.session.execute(
                select(
                    func.max(CodigoRecuperacao.criado_em)
                ).where(
                    CodigoRecuperacao.usuario_id == usuario_id
                )
            ).scalar()

            if (
                ultimo_envio is not None
                and (momento - ultimo_envio).total_seconds()
                < INTERVALO_REENVIO_SEGUNDOS
            ):
                return resposta

            # Limite de pedidos por hora.
            na_ultima_hora = db.session.execute(
                select(
                    func.count(CodigoRecuperacao.id)
                ).where(
                    CodigoRecuperacao.usuario_id == usuario_id,
                    CodigoRecuperacao.criado_em
                    >= momento - timedelta(hours=1)
                )
            ).scalar()

            if na_ultima_hora >= MAX_CODIGOS_POR_HORA:
                return resposta

            # Invalida os códigos antigos ainda não usados.
            antigos = db.session.execute(
                select(CodigoRecuperacao).where(
                    CodigoRecuperacao.usuario_id == usuario_id,
                    CodigoRecuperacao.usado.is_(False)
                )
            ).scalars().all()

            for antigo in antigos:
                antigo.usado = True

            codigo = f"{secrets.randbelow(1000000):06d}"

            db.session.add(
                CodigoRecuperacao(
                    usuario_id=usuario_id,
                    codigo_hash=generate_password_hash(codigo),
                    expira_em=momento + timedelta(
                        minutes=VALIDADE_MINUTOS
                    )
                )
            )

            db.session.commit()

            enviar_em_segundo_plano(email, codigo)

        except Exception:

            db.session.rollback()

            logger.exception(
                "Erro ao gerar o código de recuperação."
            )

        return resposta

    # ------------------------------------------
    # 2. CONFERIR O CÓDIGO E TROCAR A SENHA
    # ------------------------------------------

    @app.route(
        "/recuperar-senha/redefinir",
        methods=["POST"]
    )
    def recuperacao_redefinir():

        dados = request.get_json(silent=True)

        if not isinstance(dados, dict):
            dados = {}

        email = dados.get("email", "")
        codigo = dados.get("codigo", "")
        nova_senha = dados.get("nova_senha", "")
        confirmar_senha = dados.get("confirmar_senha", "")

        if not all(
            isinstance(valor, str)
            for valor in (email, codigo, nova_senha, confirmar_senha)
        ):

            return jsonify({

                "status": "erro",

                "mensagem": "Dados inválidos."

            }), 400

        email = email.strip().lower()
        codigo = codigo.strip()

        if not email or not codigo or not nova_senha or not confirmar_senha:

            return jsonify({

                "status": "erro",

                "mensagem": "Preencha todos os campos."

            }), 400

        if len(nova_senha) < 8:

            return jsonify({

                "status": "erro",

                "mensagem": (
                    "A senha precisa ter pelo menos 8 caracteres."
                )

            }), 400

        if nova_senha != confirmar_senha:

            return jsonify({

                "status": "erro",

                "mensagem": "As senhas não são iguais."

            }), 400

        invalido = jsonify({

            "status": "erro",

            "mensagem": MENSAGEM_CODIGO_INVALIDO

        })

        try:

            usuario_id = db.session.execute(
                select(Usuario.id).where(
                    Usuario.email == email
                )
            ).scalar_one_or_none()

            if usuario_id is None:
                return invalido, 400

            registro = db.session.execute(
                select(CodigoRecuperacao).where(
                    CodigoRecuperacao.usuario_id == usuario_id,
                    CodigoRecuperacao.usado.is_(False)
                ).order_by(
                    CodigoRecuperacao.criado_em.desc()
                ).limit(1)
            ).scalar_one_or_none()

            if (
                registro is None
                or registro.expira_em < agora()
                or registro.tentativas >= MAX_TENTATIVAS
            ):
                return invalido, 400

            if not check_password_hash(registro.codigo_hash, codigo):

                registro.tentativas += 1

                if registro.tentativas >= MAX_TENTATIVAS:
                    registro.usado = True

                db.session.commit()

                return invalido, 400

            # Código certo: gasta o código e troca a senha.
            registro.usado = True

            if alterar_senha(email, nova_senha):

                return jsonify({

                    "status": "sucesso",

                    "mensagem": (
                        "Senha alterada! Agora você pode "
                        "voltar ao login."
                    )

                })

            db.session.rollback()

            return jsonify({

                "status": "erro",

                "mensagem": (
                    "Não foi possível alterar a senha. "
                    "Tente novamente."
                )

            }), 500

        except Exception:

            db.session.rollback()

            logger.exception(
                "Erro ao redefinir a senha."
            )

            return jsonify({

                "status": "erro",

                "mensagem": (
                    "Não foi possível alterar a senha. "
                    "Tente novamente."
                )

            }), 500