from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, update, UniqueConstraint
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
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
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
# BANCO
# ==========================================

def criar_tabelas():
    db.create_all()


# ==========================================
# SINCRONIZAR PERGUNTAS
# ==========================================

def sincronizar_perguntas(perguntas):

    try:

        for dados in perguntas:

            pergunta = db.session.get(
                Pergunta,
                dados["id"]
            )

            if pergunta is None:

                pergunta = Pergunta(
                    id=dados["id"]
                )

                db.session.add(pergunta)


            pergunta.texto = dados["texto"]
            pergunta.categoria = dados["categoria"]
            pergunta.ordem = dados["id"]
            pergunta.sub_concorda = dados.get(
                "sub_concorda",
                []
            )
            pergunta.sub_discorda = dados.get(
                "sub_discorda",
                []
            )

        db.session.commit()

    except Exception:

        db.session.rollback()

        raise


# ==========================================
# USUÁRIOS
# ==========================================

def cadastrar_usuario(
    email,
    senha
):

    senha_hash = generate_password_hash(
        senha
    )

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


def validar_usuario(
    email,
    senha
):

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


    if check_password_hash(
        senha_hash,
        senha
    ):

        return usuario_id


    return None


def buscar_usuario_por_email(
    email
):

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


def alterar_senha(
    email,
    nova_senha
):

    senha_hash = generate_password_hash(
        nova_senha
    )

    resultado = db.session.execute(

        update(Usuario)

        .where(
            Usuario.email == email
        )

        .values(
            senha=senha_hash
        )

    )

    try:

        db.session.commit()

        return resultado.rowcount > 0

    except Exception:

        db.session.rollback()

        return False


# ==========================================
# TESTES E RESPOSTAS
# ==========================================

def criar_teste(
    usuario_id
):

    teste = Teste(
        usuario_id=usuario_id
    )

    db.session.add(teste)
    db.session.flush()

    return teste


def salvar_respostas(
    teste,
    respostas
):

    perguntas = db.session.execute(

        select(Pergunta.id)

        .order_by(
            Pergunta.ordem
        )

    ).scalars().all()


    respostas_normalizadas = {}

    for chave, valor in respostas.items():

        if not isinstance(chave, str):
            continue

        if not chave.startswith("p"):
            continue

        try:
            pergunta_id = int(chave[1:])
            resposta = int(valor)
        except (ValueError, TypeError):
            continue

        respostas_normalizadas[pergunta_id] = resposta


    if set(respostas_normalizadas.keys()) != set(perguntas):

        raise ValueError(
            "O teste precisa conter uma resposta para todas as perguntas."
        )


    if any(
        valor < 1 or valor > 7
        for valor in respostas_normalizadas.values()
    ):

        raise ValueError(
            "Todas as respostas precisam estar entre 1 e 7."
        )


    for pergunta_id in perguntas:

        db.session.add(

            Resposta(
                teste_id=teste.id,
                pergunta_id=pergunta_id,
                resposta=respostas_normalizadas[
                    pergunta_id
                ]
            )

        )


    return respostas_normalizadas


def buscar_teste(
    teste_id,
    usuario_id=None
):

    consulta = (

        select(
            Teste.id,
            Teste.data_teste,
            Usuario.id,
            Usuario.email,
            Resposta.pergunta_id,
            Pergunta.texto,
            Pergunta.categoria,
            Resposta.resposta
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

def salvar_resultado(
    teste,
    analise
):

    resultado = Resultado(
        teste_id=teste.id,
        percentual_geral=analise["percentual_geral"],
        classificacao_geral=analise[
            "classificacao_geral"
        ]
    )

    db.session.add(resultado)

    db.session.flush()


    for categoria in analise["categorias"]:

        db.session.add(

            ResultadoCategoria(
                resultado_id=resultado.id,
                categoria=categoria["categoria"],
                percentual=categoria["percentual"],
                classificacao=categoria[
                    "classificacao"
                ]
            )

        )


    return resultado


def buscar_resultado(
    teste_id,
    usuario_id=None
):

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


    resultado = db.session.execute(
        consulta
    ).scalar_one_or_none()


    return resultado


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

def buscar_ultimo_resultado_usuario(usuario_id):
    consulta = (
        select(Resultado.teste_id)
        .join(Teste, Resultado.teste_id == Teste.id)
        .where(Teste.usuario_id == usuario_id)
        .order_by(Resultado.data_geracao.desc())
        .limit(1)
    )

    return db.session.execute(consulta).scalar_one_or_none()
