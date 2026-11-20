from functools import wraps

from flask import (
    session,
    redirect,
    url_for,
    jsonify
)

from backend.validacoes import TIPOS_CONTA


# ==========================================
# TIPO DA CONTA LOGADA
# ==========================================

def tipo_conta_da_sessao():
    """
    Devolve "funcionario" ou "empresa_rh" para quem está logado.

    O tipo fica guardado na sessão. Caso a sessão ainda não tenha
    essa informação, o tipo é buscado no banco de dados.

    Devolve None se não houver ninguém logado ou se a conta
    não existir mais.
    """

    # Importação local para evitar importação circular
    from backend.database import buscar_tipo_conta

    tipo = session.get("tipo_conta")

    if tipo in TIPOS_CONTA:
        return tipo

    usuario_id = session.get("usuario_id")

    if usuario_id is None:
        return None

    tipo = buscar_tipo_conta(usuario_id)

    if tipo in TIPOS_CONTA:
        session["tipo_conta"] = tipo
        return tipo

    return None


# ==========================================
# PROTEÇÃO DAS ROTAS
# ==========================================

def _negar(codigo, mensagem, destino, resposta_json):

    if resposta_json:
        return jsonify({
            "status": "erro",
            "mensagem": mensagem
        }), codigo

    return redirect(destino)


def exigir_conta(tipo_exigido, resposta_json=False):
    """
    Protege uma rota de acordo com o tipo de conta.

    Exemplo:

        @app.route("/rh")
        @exigir_conta("empresa_rh")
        def rh_painel():
            ...

    Sem login:
        - Redireciona para a tela de login.
        - Em rotas JSON, retorna erro 401.

    Tipo de conta incorreto:
        - Empresa/RH vai para o painel de RH.
        - Funcionário vai para a página inicial.
        - Em rotas JSON, retorna erro 403.
    """

    def decorador(rota):

        @wraps(rota)
        def rota_protegida(*args, **kwargs):

            # ==========================================
            # VERIFICA SE ESTÁ LOGADO
            # ==========================================

            if "usuario_id" not in session:

                return _negar(
                    401,
                    "Você precisa estar logado.",
                    url_for("login"),
                    resposta_json
                )

            # ==========================================
            # DESCOBRE O TIPO DA CONTA
            # ==========================================

            tipo_atual = tipo_conta_da_sessao()

            if tipo_atual is None:

                session.clear()

                return _negar(
                    401,
                    "Sua sessão expirou. Entre novamente.",
                    url_for("login"),
                    resposta_json
                )

            # ==========================================
            # VERIFICA SE O TIPO É PERMITIDO
            # ==========================================

            if tipo_atual != tipo_exigido:

                if tipo_atual == "empresa_rh":
                    destino = url_for("rh_painel")
                else:
                    destino = url_for("home")

                return _negar(
                    403,
                    "Esta ação não está disponível para o seu tipo de conta.",
                    destino,
                    resposta_json
                )

            # ==========================================
            # ACESSO PERMITIDO
            # ==========================================

            return rota(*args, **kwargs)

        return rota_protegida

    return decorador