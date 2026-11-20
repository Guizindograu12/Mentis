# backend/rh.py
#
# Monta os dados do painel da Empresa/RH.
#
# A função montar_painel_rh() é chamada pela rota /rh do app.py.
# Ela devolve um dicionário ("painel") que o rh.html usa para mostrar
# funcionários, indicadores, categorias, evolução e sinais de atenção.

from collections import defaultdict

from sqlalchemy import func, select

import backend.database as bd
from backend.database import db, Teste, Resultado, EmotionalCheckIn


# ==========================================
# AJUSTES DO PAINEL
# ==========================================

# O percentual geral alto significa MAIS estresse/sobrecarga?
#   True  -> percentual alto é ruim (ex.: 85% = situação preocupante)
#   False -> percentual alto é bom  (ex.: 85% = bem-estar elevado)
# Se os alertas ficarem invertidos no painel, troque este valor.
PERCENTUAL_ALTO_E_RUIM = True

# A partir de quantos pontos de risco a pessoa entra em "atenção" e "alerta".
LIMITE_ATENCAO = 60
LIMITE_ALERTA = 80

# Se o risco subir tantos pontos entre dois testes seguidos,
# aparece um aviso de piora.
LIMITE_PIORA = 15


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def _modelo_usuario():
    """
    Descobre a classe da tabela "usuarios" no database.py,
    mesmo que o nome da classe seja diferente de "Usuario".
    """

    modelo = getattr(bd, "Usuario", None)

    if modelo is not None:

        return modelo

    for mapeador in db.Model.registry.mappers:

        classe = mapeador.class_

        if getattr(classe, "__tablename__", None) == "usuarios":

            return classe

    raise RuntimeError(
        "Não encontrei o model da tabela 'usuarios' no database.py."
    )


def _primeira_coluna(modelo, candidatos):
    """
    Devolve o nome da primeira coluna que existir no model.
    Devolve None se nenhuma existir.
    """

    for nome in candidatos:

        if hasattr(modelo, nome):

            return nome

    return None


def _valor(objeto, candidatos, padrao=None):
    """
    Lê o primeiro atributo que existir e não estiver vazio.
    """

    for nome in candidatos:

        valor = getattr(objeto, nome, None)

        if valor not in (None, ""):

            return valor

    return padrao


def _risco(percentual):
    """
    Converte o percentual em "pontos de risco" (0 a 100),
    respeitando PERCENTUAL_ALTO_E_RUIM.
    """

    if PERCENTUAL_ALTO_E_RUIM:

        return percentual

    return 100 - percentual


def _nivel_do_risco(risco):

    if risco >= LIMITE_ALERTA:

        return "alerta"

    if risco >= LIMITE_ATENCAO:

        return "atencao"

    return "ok"


def _nome_do_funcionario(usuario):
    """
    Monta "Nome Sobrenome". Se a conta não tiver nome,
    usa a parte do e-mail antes do @.
    """

    nome = _valor(usuario, ["nome"], "")
    sobrenome = _valor(usuario, ["sobrenome"], "")

    completo = f"{nome} {sobrenome}".strip()

    if completo:

        return completo

    email = _valor(usuario, ["email"], "")

    return email.split("@")[0] if email else "Funcionário"


def _data_formatada(data):

    return data.strftime("%d/%m/%Y") if data else "Data indisponível"


# ==========================================
# BUSCAR OS FUNCIONÁRIOS DA EMPRESA
# ==========================================

def _buscar_funcionarios(Usuario, empresa):
    """
    Devolve só os funcionários ligados à empresa que está logada.

    Primeiro tenta pela chave estrangeira (empresa_id e parecidos).
    Se o banco guardar só o nome da empresa, compara pelo nome.
    """

    consulta = select(Usuario)

    coluna_tipo = _primeira_coluna(
        Usuario,
        ["tipo_conta", "tipo"]
    )

    if coluna_tipo:

        consulta = consulta.where(
            getattr(Usuario, coluna_tipo) == "funcionario"
        )

    coluna_fk = _primeira_coluna(
        Usuario,
        [
            "empresa_id",
            "empresa_rh_id",
            "rh_id",
            "empresa_usuario_id"
        ]
    )

    if coluna_fk:

        consulta = consulta.where(
            getattr(Usuario, coluna_fk) == empresa.id
        )

    else:

        nomes_possiveis = [
            "nome_empresa",
            "empresa",
            "empresa_nome"
        ]

        coluna_empresa = _primeira_coluna(Usuario, nomes_possiveis)

        nome_da_empresa = _valor(empresa, nomes_possiveis)

        if not coluna_empresa or not nome_da_empresa:

            return []

        consulta = consulta.where(
            func.lower(getattr(Usuario, coluna_empresa))
            == str(nome_da_empresa).strip().lower()
        )

    return db.session.execute(consulta).scalars().all()


# ==========================================
# PAINEL DE RH
# ==========================================

def montar_painel_rh(empresa_usuario_id):
    """
    Recebe o id da conta Empresa/RH logada e devolve os dados do painel.
    """

    Usuario = _modelo_usuario()

    empresa = db.session.get(Usuario, empresa_usuario_id)

    if empresa is None:

        raise ValueError("Conta da empresa não encontrada.")

    funcionarios = _buscar_funcionarios(Usuario, empresa)

    ids_funcionarios = [f.id for f in funcionarios]

    # ------------------------------------------
    # 1. TODOS OS RESULTADOS DOS FUNCIONÁRIOS
    # (do mais antigo para o mais novo)
    # ------------------------------------------

    resultados_por_funcionario = defaultdict(list)

    if ids_funcionarios:

        linhas = db.session.execute(
            select(
                Resultado,
                Teste.usuario_id,
                Teste.data_teste
            )
            .join(Teste, Resultado.teste_id == Teste.id)
            .where(Teste.usuario_id.in_(ids_funcionarios))
            .order_by(
                Teste.data_teste.asc(),
                Resultado.id.asc()
            )
        ).all()

        for resultado, usuario_id, data_teste in linhas:

            resultados_por_funcionario[usuario_id].append({

                "teste_id": resultado.teste_id,

                "data": data_teste,

                "percentual": float(resultado.percentual_geral),

                "classificacao": resultado.classificacao_geral,

                "categorias": [
                    {
                        "nome": categoria.categoria,
                        "percentual": float(categoria.percentual)
                    }
                    for categoria in resultado.categorias
                ]

            })

    # ------------------------------------------
    # 2. CHECK-INS DE HUMOR (média por funcionário)
    # ------------------------------------------

    humores_por_funcionario = defaultdict(list)

    if ids_funcionarios:

        checkins = db.session.execute(
            select(
                EmotionalCheckIn.usuario_id,
                EmotionalCheckIn.humor
            )
            .where(EmotionalCheckIn.usuario_id.in_(ids_funcionarios))
        ).all()

        for usuario_id, humor in checkins:

            humores_por_funcionario[usuario_id].append(humor)

    # ------------------------------------------
    # 3. UMA LINHA POR FUNCIONÁRIO + SINAIS DE ATENÇÃO
    # ------------------------------------------

    lista_funcionarios = []
    alertas = []

    ultimos_resultados = []
    todos_os_resultados = []

    for funcionario in funcionarios:

        nome = _nome_do_funcionario(funcionario)

        historico = resultados_por_funcionario.get(funcionario.id, [])

        humores = humores_por_funcionario.get(funcionario.id, [])

        media_humor = (
            round(sum(humores) / len(humores), 1)
            if humores
            else None
        )

        if not historico:

            lista_funcionarios.append({

                "id": funcionario.id,
                "nome": nome,
                "email": _valor(funcionario, ["email"], ""),
                "total_testes": 0,
                "ultimo_percentual": None,
                "ultima_classificacao": None,
                "ultima_data": None,
                "variacao": None,
                "nivel": "sem_teste",
                "media_humor": media_humor

            })

            continue

        ultimo = historico[-1]

        penultimo = historico[-2] if len(historico) >= 2 else None

        ultimos_resultados.append(ultimo)

        todos_os_resultados.extend(historico)

        risco_ultimo = _risco(ultimo["percentual"])

        nivel = _nivel_do_risco(risco_ultimo)

        variacao = None

        if penultimo:

            variacao = round(
                ultimo["percentual"] - penultimo["percentual"],
                2
            )

            piora = risco_ultimo - _risco(penultimo["percentual"])

            if piora >= LIMITE_PIORA:

                alertas.append({

                    "funcionario": nome,
                    "tipo": "piora",
                    "mensagem": (
                        f"Piora de {round(piora)} pontos "
                        "em relação ao teste anterior."
                    )

                })

        if nivel == "alerta":

            alertas.append({

                "funcionario": nome,
                "tipo": "alerta",
                "mensagem": (
                    "Resultado no nível mais alto de atenção "
                    f"({ultimo['percentual']}%)."
                )

            })

        elif nivel == "atencao":

            alertas.append({

                "funcionario": nome,
                "tipo": "atencao",
                "mensagem": (
                    "Resultado pede atenção "
                    f"({ultimo['percentual']}%)."
                )

            })

        lista_funcionarios.append({

            "id": funcionario.id,
            "nome": nome,
            "email": _valor(funcionario, ["email"], ""),
            "total_testes": len(historico),
            "ultimo_percentual": ultimo["percentual"],
            "ultima_classificacao": ultimo["classificacao"],
            "ultima_data": _data_formatada(ultimo["data"]),
            "variacao": variacao,
            "nivel": nivel,
            "media_humor": media_humor

        })

    # Quem precisa de mais atenção aparece primeiro.
    ordem_nivel = {"alerta": 0, "atencao": 1, "ok": 2, "sem_teste": 3}

    lista_funcionarios.sort(
        key=lambda item: (
            ordem_nivel[item["nivel"]],
            -(item["ultimo_percentual"] or 0)
        )
    )

    ordem_alerta = {"alerta": 0, "piora": 1, "atencao": 2}

    alertas.sort(key=lambda item: ordem_alerta[item["tipo"]])

    # ------------------------------------------
    # 4. INDICADORES GERAIS
    # (usam o ÚLTIMO resultado de cada funcionário)
    # ------------------------------------------

    media_geral = (
        round(
            sum(r["percentual"] for r in ultimos_resultados)
            / len(ultimos_resultados),
            2
        )
        if ultimos_resultados
        else None
    )

    todos_os_humores = [
        humor
        for lista in humores_por_funcionario.values()
        for humor in lista
    ]

    media_humor_empresa = (
        round(sum(todos_os_humores) / len(todos_os_humores), 1)
        if todos_os_humores
        else None
    )

    # Quantas pessoas em cada classificação.
    contagem_classificacao = defaultdict(int)

    for resultado in ultimos_resultados:

        contagem_classificacao[resultado["classificacao"]] += 1

    distribuicao = [
        {"classificacao": nome, "quantidade": quantidade}
        for nome, quantidade in contagem_classificacao.items()
    ]

    # ------------------------------------------
    # 5. MÉDIA POR CATEGORIA
    # (as categorias que mais preocupam vêm primeiro)
    # ------------------------------------------

    valores_por_categoria = defaultdict(list)

    for resultado in ultimos_resultados:

        for categoria in resultado["categorias"]:

            valores_por_categoria[categoria["nome"]].append(
                categoria["percentual"]
            )

    categorias = [

        {
            "nome": nome,
            "percentual": round(sum(valores) / len(valores), 2)
        }

        for nome, valores in valores_por_categoria.items()

    ]

    categorias.sort(
        key=lambda item: _risco(item["percentual"]),
        reverse=True
    )

    # ------------------------------------------
    # 6. EVOLUÇÃO POR MÊS
    # (média de todos os testes feitos em cada mês)
    # ------------------------------------------

    valores_por_mes = defaultdict(list)

    for resultado in todos_os_resultados:

        data = resultado["data"]

        if data is None:

            continue

        valores_por_mes[(data.year, data.month)].append(
            resultado["percentual"]
        )

    evolucao = [

        {
            "mes": f"{mes:02d}/{ano}",
            "percentual": round(sum(valores) / len(valores), 2),
            "testes": len(valores)
        }

        for (ano, mes), valores in sorted(valores_por_mes.items())

    ]

    # ------------------------------------------
    # 7. RESULTADO FINAL PARA O rh.html
    # ------------------------------------------

    return {

        "empresa": {
            "nome": _valor(
                empresa,
                ["nome_empresa", "empresa", "empresa_nome", "nome"],
                "Sua empresa"
            ),
            "email": _valor(empresa, ["email"], "")
        },

        "total_funcionarios": len(funcionarios),

        "funcionarios_com_teste": len(ultimos_resultados),

        "total_testes": len(todos_os_resultados),

        "media_geral": media_geral,

        "media_humor": media_humor_empresa,

        "distribuicao": distribuicao,

        "categorias": categorias,

        "evolucao": evolucao,

        "funcionarios": lista_funcionarios,

        "alertas": alertas,

        "percentual_alto_e_ruim": PERCENTUAL_ALTO_E_RUIM,

        "limite_atencao": LIMITE_ATENCAO,

        "limite_alerta": LIMITE_ALERTA

    }