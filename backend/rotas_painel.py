# backend/rotas_painel.py
#
# Rotas da área do Funcionário e do painel da Empresa/RH.
#
# São registradas no app.py com registrar_rotas_painel(app).
# Os nomes das rotas (url_for) continuam simples:
# "funcionario_area", "rh_painel", "rh_funcionarios" etc.

from flask import (
    abort,
    current_app,
    redirect,
    render_template,
    session,
    url_for
)

from backend.permissoes import exigir_conta
from backend.rh import montar_painel_rh

from backend.painel_dados import (
    buscar_resultado_empresa,
    dados_empresa,
    detalhe_funcionario,
    listar_funcionarios,
    listar_testes,
    montar_area_funcionario
)


def registrar_rotas_painel(app):

    # ==========================================
    # ÁREA DO FUNCIONÁRIO
    # ==========================================

    @app.route("/funcionario")
    @exigir_conta("funcionario")
    def funcionario_area():

        area = montar_area_funcionario(
            session["usuario_id"],
            teste_em_andamento=bool(
                session.get("perguntas_teste_ids")
            )
        )

        if area is None:

            return redirect(url_for("logout"))

        return render_template(
            "funcionario.html",
            area=area
        )


    # ==========================================
    # PAINEL DA EMPRESA / RH
    # Cada rota só mostra dados da empresa da conta logada.
    # ==========================================

    @app.route("/rh")
    @exigir_conta("empresa_rh")
    def rh_painel():

        rh_id = session["usuario_id"]

        try:

            painel = montar_painel_rh(rh_id)

            ultimos_envios = listar_testes(
                rh_id,
                limite=5
            )

            empresa = dados_empresa(rh_id)

        except Exception:

            current_app.logger.exception(
                "Erro ao montar o painel de RH."
            )

            return (
                "Não foi possível carregar o painel de RH. "
                "Tente novamente mais tarde.",
                500
            )

        # Usa o dashboard novo quando ele existir;
        # enquanto isso, continua usando o rh.html atual.

        return render_template(
            ["rh_dashboard.html", "rh.html"],
            painel=painel,
            ultimos_envios=ultimos_envios,
            empresa=empresa,
            pagina="dashboard"
        )


    @app.route("/rh/funcionarios")
    @exigir_conta("empresa_rh")
    def rh_funcionarios():

        rh_id = session["usuario_id"]

        funcionarios = listar_funcionarios(rh_id)

        com_teste = sum(
            1
            for funcionario in funcionarios
            if funcionario["ultimo"]
        )

        return render_template(
            "rh_funcionarios.html",
            funcionarios=funcionarios,
            total=len(funcionarios),
            com_teste=com_teste,
            sem_teste=len(funcionarios) - com_teste,
            empresa=dados_empresa(rh_id),
            pagina="funcionarios"
        )


    @app.route("/rh/funcionarios/<int:funcionario_id>")
    @exigir_conta("empresa_rh")
    def rh_funcionario(funcionario_id):

        rh_id = session["usuario_id"]

        detalhe = detalhe_funcionario(
            rh_id,
            funcionario_id
        )

        # Funcionário de outra empresa (ou que não existe): 404.

        if detalhe is None:

            abort(404)

        return render_template(
            "rh_funcionario.html",
            funcionario=detalhe,
            empresa=dados_empresa(rh_id),
            pagina="funcionarios"
        )


    @app.route("/rh/testes")
    @exigir_conta("empresa_rh")
    def rh_testes():

        rh_id = session["usuario_id"]

        return render_template(
            "rh_testes.html",
            testes=listar_testes(
                rh_id,
                so_ultimo_de_cada=True
            ),
            empresa=dados_empresa(rh_id),
            pagina="testes"
        )


    @app.route("/rh/testes/<int:teste_id>")
    @exigir_conta("empresa_rh")
    def rh_resultado(teste_id):

        rh_id = session["usuario_id"]

        resultado = buscar_resultado_empresa(
            rh_id,
            teste_id
        )

        # Teste de outra empresa (ou que não existe): 404.

        if resultado is None:

            abort(404)

        return render_template(
            "rh_resultado.html",
            resultado=resultado,
            empresa=dados_empresa(rh_id),
            pagina="testes"
        )


    @app.route("/rh/historico")
    @exigir_conta("empresa_rh")
    def rh_historico():

        rh_id = session["usuario_id"]

        return render_template(
            "rh_historico.html",
            testes=listar_testes(rh_id),
            empresa=dados_empresa(rh_id),
            pagina="historico"
        )


    @app.route("/rh/empresa")
    @exigir_conta("empresa_rh")
    def rh_empresa():

        rh_id = session["usuario_id"]

        return render_template(
            "rh_empresa.html",
            empresa=dados_empresa(rh_id),
            pagina="empresa"
        )