
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import (
    select,
    update,
    UniqueConstraint,
    text
)

from sqlalchemy.exc import IntegrityError

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# ==========================================
# SQLALCHEMY
# ==========================================

db = SQLAlchemy()


# ==========================================
# CONFIGURAÇÃO DAS PERGUNTAS
# ==========================================

# Formato: ID: (peso, invertida)
#
# Peso:
# 1.00 = Alta relevância
# 0.70 = Média relevância
# 0.50 = Baixa relevância
#
# invertida:
# False = Pergunta negativa
# True = Pergunta positiva

CONFIGURACAO_PERGUNTAS = {
    1: (1.00, False),
    2: (0.70, True),
    3: (1.00, False),
    4: (0.70, True),
    5: (1.00, False),
    6: (0.70, False),
    7: (1.00, False),
    8: (0.70, True),
    9: (0.70, False),
    10: (0.70, False),
    11: (1.00, False),
    12: (0.70, False),
    13: (0.70, True),
    14: (0.70, False),
    15: (0.70, True),
    16: (1.00, False),
    17: (0.70, False),
    18: (0.70, False),
    19: (1.00, False),
    20: (0.70, True),
    21: (1.00, False),
    22: (0.70, False),
    23: (0.50, False),
    24: (0.70, False),
    25: (0.70, True),
    26: (0.70, False),
    27: (0.70, True),
    28: (1.00, False),
    29: (0.70, True),
    30: (1.00, False),
    31: (0.70, True),
    32: (1.00, False),
    33: (0.70, True),
    34: (0.70, True),
    35: (1.00, False),
    36: (0.70, True),
    37: (0.70, True),
    38: (0.70, True),
    39: (0.70, True),
    40: (1.00, False)
}


def configuracao_pergunta(pergunta_id):
    return CONFIGURACAO_PERGUNTAS.get(
        pergunta_id,
        (1.00, False)
    )


# ==========================================
# MODELOS / TABELAS
# ==========================================

class Usuario(db.Model):

    __tablename__ = "usuarios"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    email = db.Column(
        db.String(320),
        unique=True,
        nullable=False,
        index=True
    )

    senha = db.Column(
        db.String(255),
        nullable=False
    )

    testes = db.relationship(
        "Teste",
        back_populates="usuario",
        cascade="all, delete-orphan"
    )


class Pergunta(db.Model):

    __tablename__ = "perguntas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    texto = db.Column(
        db.Text,
        nullable=False
    )

    categoria = db.Column(
        db.String(120),
        nullable=False,
        index=True
    )

    ordem = db.Column(
        db.Integer,
        unique=True,
        nullable=False,
        index=True
    )

    sub_concorda = db.Column(
        db.JSON,
        nullable=True
    )

    sub_discorda = db.Column(
        db.JSON,
        nullable=True
    )

    # IMPORTANTE:
    # Estes dois campos são utilizados pelo sistema
    # de pontuação ponderada e inversão das perguntas.

    peso = db.Column(
        db.Numeric(3, 2),
        nullable=False,
        default=1.00,
        server_default="1.00"
    )

    invertida = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE")
    )

    respostas = db.relationship(
        "Resposta",
        back_populates="pergunta"
    )


class Teste(db.Model):

    __tablename__ = "testes"

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

    data_teste = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        nullable=False
    )

    usuario = db.relationship(
        "Usuario",
        back_populates="testes"
    )

    respostas = db.relationship(
        "Resposta",
        back_populates="teste",
        cascade="all, delete-orphan"
    )

    resultado = db.relationship(
        "Resultado",
        back_populates="teste",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Resposta(db.Model):

    __tablename__ = "respostas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    teste_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "testes.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    pergunta_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "perguntas.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    resposta = db.Column(
        db.Integer,
        nullable=False
    )

    teste = db.relationship(
        "Teste",
        back_populates="respostas"
    )

    pergunta = db.relationship(
        "Pergunta",
        back_populates="respostas"
    )

    __table_args__ = (
        UniqueConstraint(
            "teste_id",
            "pergunta_id",
            name="uq_resposta_teste_pergunta"
        ),
    )


class Resultado(db.Model):

    __tablename__ = "resultados"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    teste_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "testes.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False,
        index=True
    )

    percentual_geral = db.Column(
        db.Numeric(5, 2),
        nullable=False
    )

    classificacao_geral = db.Column(
        db.String(50),
        nullable=False
    )

    data_geracao = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        nullable=False
    )

    teste = db.relationship(
        "Teste",
        back_populates="resultado"
    )

    categorias = db.relationship(
        "ResultadoCategoria",
        back_populates="resultado",
        cascade="all, delete-orphan",
        order_by="ResultadoCategoria.categoria"
    )


class ResultadoCategoria(db.Model):

    __tablename__ = "resultado_categorias"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    resultado_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "resultados.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    categoria = db.Column(
        db.String(120),
        nullable=False
    )

    percentual = db.Column(
        db.Numeric(5, 2),
        nullable=False
    )

    classificacao = db.Column(
        db.String(50),
        nullable=False
    )

    resultado = db.relationship(
        "Resultado",
        back_populates="categorias"
    )

    __table_args__ = (
        UniqueConstraint(
            "resultado_id",
            "categoria",
            name="uq_resultado_categoria"
        ),
    )


class EmotionalCheckIn(db.Model):

    __tablename__ = "emotional_checkins"

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

    humor = db.Column(
        db.Integer,
        nullable=False
    )

    data_registro = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        nullable=False
    )


# ==========================================
# BANCO DE DADOS
# ==========================================

def criar_tabelas():

    db.create_all()

    # Garante que bancos já existentes também
    # recebam as colunas peso e invertida.

    with db.engine.begin() as conexao:

        conexao.execute(
            text("""
                ALTER TABLE public.perguntas
                ADD COLUMN IF NOT EXISTS peso
                NUMERIC(3,2) NOT NULL DEFAULT 1.00
            """)
        )

        conexao.execute(
            text("""
                ALTER TABLE public.perguntas
                ADD COLUMN IF NOT EXISTS invertida
                BOOLEAN NOT NULL DEFAULT FALSE
            """)
        )


# ==========================================
# SINCRONIZAR PERGUNTAS
# ==========================================

def sincronizar_perguntas(perguntas):

    try:

        for dados in perguntas:

            pergunta_id = dados["id"]

            peso, invertida = configuracao_pergunta(
                pergunta_id
            )

            pergunta = db.session.get(
                Pergunta,
                pergunta_id
            )

            if pergunta is None:

                pergunta = Pergunta(
                    id=pergunta_id,
                    texto=dados["texto"],
                    categoria=dados["categoria"],
                    ordem=pergunta_id,
                    sub_concorda=dados.get("sub_concorda", []),
                    sub_discorda=dados.get("sub_discorda", []),
                    peso=peso,
                    invertida=invertida
                )

                db.session.add(pergunta)

            else:

                pergunta.texto = dados["texto"]
                pergunta.categoria = dados["categoria"]
                pergunta.ordem = pergunta_id

                pergunta.sub_concorda = dados.get(
                    "sub_concorda",
                    []
                )

                pergunta.sub_discorda = dados.get(
                    "sub_discorda",
                    []
                )

                pergunta.peso = peso
                pergunta.invertida = invertida

        db.session.commit()

    except Exception:

        db.session.rollback()
        raise


# ==========================================
# USUÁRIOS
# ==========================================

def cadastrar_usuario(email, senha):

    senha_hash = generate_password_hash(senha)

    usuario = Usuario(
        email=email,
        senha=senha_hash
    )

    try:

        db.session.add(usuario)
        db.session.commit()

        return True

    except IntegrityError:

        db.session.rollback()
        return False


def validar_usuario(email, senha):

    usuario = db.session.execute(
        select(
            Usuario.id,
            Usuario.senha
        ).where(
            Usuario.email == email
        )
    ).first()

    if usuario is None:
        return None

    usuario_id = usuario[0]
    senha_hash = usuario[1]

    if check_password_hash(senha_hash, senha):
        return usuario_id

    return None


def buscar_usuario_por_email(email):

    usuario = db.session.execute(
        select(
            Usuario.id,
            Usuario.email
        ).where(
            Usuario.email == email
        )
    ).first()

    if usuario is None:
        return None

    return (
        usuario[0],
        usuario[1]
    )


def alterar_senha(email, nova_senha):

    senha_hash = generate_password_hash(nova_senha)

    try:

        resultado = db.session.execute(
            update(Usuario)
            .where(
                Usuario.email == email
            )
            .values(
                senha=senha_hash
            )
        )

        db.session.commit()

        return resultado.rowcount > 0

    except Exception:

        db.session.rollback()
        return False


# ==========================================
# TESTES E RESPOSTAS
# ==========================================

def criar_teste(usuario_id):

    teste = Teste(
        usuario_id=usuario_id
    )

    db.session.add(teste)
    db.session.flush()

    return teste


def salvar_respostas(teste, respostas):

    perguntas_disponiveis = set(
        db.session.execute(
            select(Pergunta.id)
        ).scalars().all()
    )

    respostas_normalizadas = {}

    for chave, valor in respostas.items():

        if not isinstance(chave, str):
            raise ValueError(
                "Foi enviada uma pergunta inválida."
            )

        if not chave.startswith("p"):
            raise ValueError(
                "Foi enviada uma pergunta inválida."
            )

        try:

            pergunta_id = int(chave[1:])

            resposta = int(valor)

        except (ValueError, TypeError):

            raise ValueError(
                "Foi enviada uma resposta inválida."
            )

        if pergunta_id in respostas_normalizadas:

            raise ValueError(
                "Uma pergunta não pode ter mais de uma resposta."
            )

        respostas_normalizadas[pergunta_id] = resposta

    if len(respostas_normalizadas) != 25:

        raise ValueError(
            "O teste precisa conter exatamente 25 respostas."
        )

    if not set(respostas_normalizadas).issubset(
        perguntas_disponiveis
    ):

        raise ValueError(
            "O teste contém uma pergunta que não existe no banco."
        )

    if any(
        valor < 1 or valor > 7
        for valor in respostas_normalizadas.values()
    ):

        raise ValueError(
            "Todas as respostas precisam estar entre 1 e 7."
        )

    for pergunta_id, valor in respostas_normalizadas.items():

        db.session.add(
            Resposta(
                teste_id=teste.id,
                pergunta_id=pergunta_id,
                resposta=valor
            )
        )

    return respostas_normalizadas


def buscar_teste(teste_id, usuario_id=None):

    consulta = (
        select(
            Teste.id,
            Teste.data_teste,
            Usuario.id,
            Usuario.email,
            Resposta.pergunta_id,
            Pergunta.texto,
            Pergunta.categoria,
            Resposta.resposta,
            Pergunta.peso,
            Pergunta.invertida
        )
        .join(
            Usuario,
            Teste.usuario_id == Usuario.id
        )
        .join(
            Resposta,
            Teste.id == Resposta.teste_id
        )
        .join(
            Pergunta,
            Resposta.pergunta_id == Pergunta.id
        )
        .where(
            Teste.id == teste_id
        )
        .order_by(
            Pergunta.ordem
        )
    )

    if usuario_id is not None:

        consulta = consulta.where(
            Teste.usuario_id == usuario_id
        )

    resultados = db.session.execute(
        consulta
    ).all()

    return [
        tuple(linha)
        for linha in resultados
    ]


def listar_perguntas():

    return db.session.execute(
        select(Pergunta)
        .order_by(
            Pergunta.ordem
        )
    ).scalars().all()


# ==========================================
# RESULTADOS / RELATÓRIO
# ==========================================

def salvar_resultado(teste, analise):

    resultado = Resultado(
        teste_id=teste.id,
        percentual_geral=analise["percentual_geral"],
        classificacao_geral=analise["classificacao_geral"]
    )

    db.session.add(resultado)
    db.session.flush()

    for categoria in analise["categorias"]:

        db.session.add(
            ResultadoCategoria(
                resultado_id=resultado.id,
                categoria=categoria["categoria"],
                percentual=categoria["percentual"],
                classificacao=categoria["classificacao"]
            )
        )

    return resultado


def buscar_resultado(teste_id, usuario_id=None):

    consulta = (
        select(Resultado)
        .join(
            Teste,
            Resultado.teste_id == Teste.id
        )
        .where(
            Resultado.teste_id == teste_id
        )
    )

    if usuario_id is not None:

        consulta = consulta.where(
            Teste.usuario_id == usuario_id
        )

    return db.session.execute(
        consulta
    ).scalar_one_or_none()


def buscar_ultimo_resultado_usuario(usuario_id):

    consulta = (
        select(Resultado.teste_id)
        .join(
            Teste,
            Resultado.teste_id == Teste.id
        )
        .where(
            Teste.usuario_id == usuario_id
        )
        .order_by(
            Resultado.data_geracao.desc()
        )
        .limit(1)
    )

    return db.session.execute(
        consulta
    ).scalar_one_or_none()
