# backend/painel_dados.py
#
# Consultas do painel da Empresa/RH e da área do Funcionário.
#
# REGRA DE SEGURANÇA DESTE ARQUIVO:
# toda consulta do RH filtra por Usuario.empresa_id == id da conta
# Empresa/RH que está logada. Assim, nenhuma função devolve dados de
# outra empresa, mesmo que alguém troque o ID na URL.

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from backend.database import db, Usuario, Teste, Resultado
from backend.relatorio import montar_relatorio


# ==========================================
# CLASSIFICAÇÕES (já existentes no Mentis)
# ==========================================

# Nome usado nas cores dos badges. Quanto maior o percentual,
# maior a dificuldade indicada (veja analise.py).

NIVEIS = {
    "Muito Baixo": "muito-baixo",
    "Baixo": "baixo",
    "Moderado": "moderado",
    "Elevado": "elevado",
    "Muito Elevado": "muito-elevado"
}


def nivel_da_classificacao(classificacao):

    return NIVEIS.get(classificacao, "neutro")


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def _nome_exibicao(usuario):
    """
    "Nome Sobrenome". Se a conta não tiver nome (contas antigas),
    usa a parte do e-mail antes do @.
    """

    nome = (usuario.nome or "").strip()
    sobrenome = (usuario.sobrenome or "").strip()

    completo = f"{nome} {sobrenome}".strip()

    if completo:

        return completo

    if usuario.email:

        return usuario.email.split("@")[0]

    return "Funcionário"


def _formatar_data(data):

    return data.strftime("%d/%m/%Y") if data else "—"


def _formatar_cnpj(cnpj):

    numeros = "".join(
        caractere
        for caractere in (cnpj or "")
        if caractere.isdigit()
    )

    if len(numeros) != 14:

        return None

    return (
        f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/"
        f"{numeros[8:12]}-{numeros[12:]}"
    )


def _data_cadastro(usuario):
    """
    A tabela usuarios ainda não tem coluna de data de cadastro.
    Se ela for criada com o nome criado_em, a data passa a
    aparecer sozinha. Sem a coluna, devolve None.
    """

    data = getattr(usuario, "criado_em", None)

    return _formatar_data(data) if data else None


def _item_teste(resultado, data_teste, funcionario):
    """
    Uma linha de teste (usada nas telas de Testes e Histórico).
    Só traz o resultado e as categorias, nunca as respostas
    pergunta por pergunta.
    """

    categorias = [

        {
            "nome": categoria.categoria,
            "percentual": float(categoria.percentual),
            "classificacao": categoria.classificacao,
            "nivel": nivel_da_classificacao(categoria.classificacao)
        }

        for categoria in resultado.categorias

    ]

    mais_altas = sorted(
        categorias,
        key=lambda item: item["percentual"],
        reverse=True
    )[:3]

    return {

        "teste_id": resultado.teste_id,

        "funcionario_id": funcionario.id,

        "funcionario": _nome_exibicao(funcionario),

        "email": funcionario.email,

        "data": _formatar_data(data_teste),

        "percentual": float(resultado.percentual_geral),

        "classificacao": resultado.classificacao_geral,

        "nivel": nivel_da_classificacao(
            resultado.classificacao_geral
        ),

        "status": "Recebido",

        "categorias": categorias,

        "categorias_mais_altas": mais_altas

    }


def _consulta_testes_da_empresa(rh_id):
    """
    Base de todas as consultas de testes do RH:
    só testes de funcionários ligados à empresa logada.
    """

    return (
        select(
            Resultado,
            Teste.data_teste,
            Usuario
        )
        .join(
            Teste,
            Resultado.teste_id == Teste.id
        )
        .join(
            Usuario,
            Teste.usuario_id == Usuario.id
        )
        .where(
            Usuario.empresa_id == rh_id,
            Usuario.tipo_conta == "funcionario"
        )
        .options(
            selectinload(Resultado.categorias)
        )
    )


# ==========================================
# EMPRESA / RH
# ==========================================

def dados_empresa(rh_id):
    """
    Perfil da empresa (conta Empresa/RH logada).
    """

    conta = db.session.get(Usuario, rh_id)

    if conta is None or conta.tipo_conta != "empresa_rh":

        return None

    total_funcionarios = db.session.execute(
        select(func.count(Usuario.id)).where(
            Usuario.empresa_id == rh_id,
            Usuario.tipo_conta == "funcionario"
        )
    ).scalar_one()

    return {

        "nome": conta.empresa or "Sua empresa",

        "cnpj": _formatar_cnpj(conta.cnpj),

        "email": conta.email,

        "total_funcionarios": total_funcionarios,

        "cadastro": _data_cadastro(conta)

    }


def listar_testes(
    rh_id,
    funcionario_id=None,
    limite=None,
    so_ultimo_de_cada=False
):
    """
    Testes recebidos pela empresa, do mais novo para o mais antigo.

    - funcionario_id: só os testes de um funcionário.
    - limite: quantidade máxima de linhas.
    - so_ultimo_de_cada: uma linha por funcionário (o teste mais recente).
    """

    consulta = _consulta_testes_da_empresa(rh_id).order_by(
        Teste.data_teste.desc(),
        Resultado.id.desc()
    )

    if funcionario_id is not None:

        consulta = consulta.where(
            Usuario.id == funcionario_id
        )

    linhas = db.session.execute(consulta).all()

    itens = []
    ja_vistos = set()

    for resultado, data_teste, funcionario in linhas:

        if so_ultimo_de_cada:

            if funcionario.id in ja_vistos:

                continue

            ja_vistos.add(funcionario.id)

        itens.append(
            _item_teste(
                resultado,
                data_teste,
                funcionario
            )
        )

        if limite and len(itens) >= limite:

            break

    return itens


def listar_funcionarios(rh_id):
    """
    Funcionários ligados à empresa, com o último teste de cada um.

    status:
    - "concluido": já fez pelo menos um teste
    - "pendente": ainda não fez nenhum teste
    """

    funcionarios = db.session.execute(
        select(Usuario).where(
            Usuario.empresa_id == rh_id,
            Usuario.tipo_conta == "funcionario"
        )
    ).scalars().all()

    ultimos = {
        item["funcionario_id"]: item
        for item in listar_testes(
            rh_id,
            so_ultimo_de_cada=True
        )
    }

    totais = dict(

        db.session.execute(
            select(
                Teste.usuario_id,
                func.count(Resultado.id)
            )
            .select_from(Resultado)
            .join(
                Teste,
                Resultado.teste_id == Teste.id
            )
            .join(
                Usuario,
                Teste.usuario_id == Usuario.id
            )
            .where(
                Usuario.empresa_id == rh_id
            )
            .group_by(
                Teste.usuario_id
            )
        ).all()

    )

    lista = []

    for funcionario in funcionarios:

        ultimo = ultimos.get(funcionario.id)

        lista.append({

            "id": funcionario.id,

            "nome": _nome_exibicao(funcionario),

            "email": funcionario.email,

            "cadastro": _data_cadastro(funcionario),

            "total_testes": totais.get(funcionario.id, 0),

            "status": "concluido" if ultimo else "pendente",

            "status_rotulo": (
                "Teste concluído" if ultimo else "Sem teste"
            ),

            "ultimo": ultimo

        })

    lista.sort(
        key=lambda item: item["nome"].lower()
    )

    return lista


def detalhe_funcionario(rh_id, funcionario_id):
    """
    Dados permitidos de UM funcionário e o histórico dele.
    Devolve None se ele não for da empresa logada.

    Não traz data de nascimento, respostas individuais nem
    check-ins de humor: o RH só vê o que é necessário.
    """

    funcionario = db.session.execute(
        select(Usuario).where(
            Usuario.id == funcionario_id,
            Usuario.empresa_id == rh_id,
            Usuario.tipo_conta == "funcionario"
        )
    ).scalar_one_or_none()

    if funcionario is None:

        return None

    testes = listar_testes(
        rh_id,
        funcionario_id=funcionario_id
    )

    return {

        "id": funcionario.id,

        "nome": _nome_exibicao(funcionario),

        "email": funcionario.email,

        "cadastro": _data_cadastro(funcionario),

        "total_testes": len(testes),

        "status": "concluido" if testes else "pendente",

        "status_rotulo": (
            "Teste concluído" if testes else "Sem teste"
        ),

        "ultimo": testes[0] if testes else None,

        "testes": testes

    }


def buscar_resultado_empresa(rh_id, teste_id):
    """
    Resultado de um teste, para o RH abrir o relatório.
    Devolve None se o teste não for de um funcionário da empresa logada.

    Reaproveita montar_relatorio() (relatorio.py).
    """

    linha = db.session.execute(
        _consulta_testes_da_empresa(rh_id).where(
            Resultado.teste_id == teste_id
        )
    ).first()

    if linha is None:

        return None

    resultado, data_teste, funcionario = linha

    relatorio = montar_relatorio(resultado)

    categorias = [

        {
            "nome": categoria["categoria"],
            "percentual": categoria["percentual"],
            "classificacao": categoria["classificacao"],
            "nivel": nivel_da_classificacao(
                categoria["classificacao"]
            )
        }

        for categoria in relatorio["categorias"]

    ]

    # Teste anterior do mesmo funcionário (para comparar).

    anterior_linha = db.session.execute(
        select(
            Resultado.percentual_geral,
            Resultado.classificacao_geral,
            Teste.data_teste
        )
        .join(
            Teste,
            Resultado.teste_id == Teste.id
        )
        .where(
            Teste.usuario_id == funcionario.id,
            Teste.id < teste_id
        )
        .order_by(
            Teste.id.desc()
        )
        .limit(1)
    ).first()

    anterior = None

    if anterior_linha is not None:

        percentual_anterior = float(anterior_linha[0])

        anterior = {

            "percentual": percentual_anterior,

            "classificacao": anterior_linha[1],

            "data": _formatar_data(anterior_linha[2]),

            "variacao": round(
                relatorio["percentual_geral"] - percentual_anterior,
                2
            )

        }

    return {

        "teste_id": teste_id,

        "funcionario": {
            "id": funcionario.id,
            "nome": _nome_exibicao(funcionario),
            "email": funcionario.email
        },

        "data": _formatar_data(data_teste),

        "percentual": relatorio["percentual_geral"],

        "classificacao": relatorio["classificacao_geral"],

        "nivel": nivel_da_classificacao(
            relatorio["classificacao_geral"]
        ),

        "categorias": categorias,

        "anterior": anterior

    }


# ==========================================
# FUNCIONÁRIO
# ==========================================

STATUS_FUNCIONARIO = {

    "pendente": (
        "Pendente",
        "Você ainda não respondeu ao teste."
    ),

    "em_andamento": (
        "Em andamento",
        "Você iniciou um teste e ainda não o enviou."
    ),

    "concluido": (
        "Concluído",
        "Você concluiu o teste. Sua conta não está vinculada a uma "
        "empresa, então nenhum RH recebeu o resultado."
    ),

    "enviado": (
        "Enviado ao RH",
        "Você concluiu o teste e o resultado está disponível "
        "para o RH da sua empresa."
    )

}


def montar_area_funcionario(usuario_id, teste_em_andamento=False):
    """
    Dados da área do Funcionário logado: empresa, status e último
    resultado. Só usa dados da própria conta e da empresa vinculada.

    teste_em_andamento: True quando a sessão já tem perguntas
    sorteadas e o teste ainda não foi enviado.
    """

    usuario = db.session.get(Usuario, usuario_id)

    if usuario is None or usuario.tipo_conta != "funcionario":

        return None

    # Informações básicas da empresa (nome e CNPJ).
    # Nada de dados administrativos.

    empresa = None

    if usuario.empresa_id is not None:

        conta_rh = db.session.get(
            Usuario,
            usuario.empresa_id
        )

        if conta_rh is not None:

            empresa = {

                "nome": (
                    conta_rh.empresa
                    or usuario.empresa
                    or "Empresa"
                ),

                "cnpj": _formatar_cnpj(conta_rh.cnpj)

            }

    ultimo_registro = db.session.execute(
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
            Teste.data_teste.desc(),
            Resultado.id.desc()
        )
        .limit(1)
    ).first()

    total_testes = db.session.execute(
        select(func.count(Resultado.id))
        .select_from(Resultado)
        .join(
            Teste,
            Resultado.teste_id == Teste.id
        )
        .where(
            Teste.usuario_id == usuario_id
        )
    ).scalar_one()

    ja_respondeu = total_testes > 0

    enviado_ao_rh = ja_respondeu and empresa is not None

    if teste_em_andamento:

        status = "em_andamento"

    elif enviado_ao_rh:

        status = "enviado"

    elif ja_respondeu:

        status = "concluido"

    else:

        status = "pendente"

    ultimo = None

    if ultimo_registro is not None:

        resultado, data_teste = ultimo_registro

        ultimo = {

            "teste_id": resultado.teste_id,

            "data": _formatar_data(data_teste),

            "percentual": float(resultado.percentual_geral),

            "classificacao": resultado.classificacao_geral,

            "nivel": nivel_da_classificacao(
                resultado.classificacao_geral
            )

        }

    rotulo, descricao = STATUS_FUNCIONARIO[status]

    return {

        "nome": (usuario.nome or "").strip() or None,

        "email": usuario.email,

        "empresa": empresa,

        "status": status,

        "status_rotulo": rotulo,

        "status_descricao": descricao,

        "total_testes": total_testes,

        "ja_respondeu": ja_respondeu,

        "enviado_ao_rh": enviado_ao_rh,

        "ultimo": ultimo

    }