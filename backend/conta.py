from datetime import datetime, timezone

from sqlalchemy import select, delete

from backend.database import (
    db,
    Usuario,
    Teste,
    Resposta,
    Pergunta,
    EmotionalCheckIn
)


def _data_iso(data):
    """
    Converte uma data do banco para texto (ou None se estiver vazia).
    """

    if data is None:
        return None

    return data.isoformat()


def exportar_dados_usuario(usuario_id):
    """
    Reúne os dados da conta em um dicionário, para o usuário baixar.

    A senha (mesmo em hash) nunca é incluída.
    """

    usuario = db.session.get(
        Usuario,
        usuario_id
    )

    if usuario is None:
        return None

    testes_db = db.session.execute(
        select(Teste)
        .where(
            Teste.usuario_id == usuario_id
        )
        .order_by(
            Teste.data_teste.asc(),
            Teste.id.asc()
        )
    ).scalars().all()

    testes = []

    for teste in testes_db:

        respostas_db = db.session.execute(
            select(
                Pergunta.texto,
                Pergunta.categoria,
                Resposta.resposta
            )
            .join(
                Pergunta,
                Resposta.pergunta_id == Pergunta.id
            )
            .where(
                Resposta.teste_id == teste.id
            )
            .order_by(
                Pergunta.ordem
            )
        ).all()

        respostas = [

            {
                "pergunta": linha[0],
                "categoria": linha[1],
                "resposta": linha[2]
            }

            for linha in respostas_db

        ]

        resultado = None

        if teste.resultado is not None:

            resultado = {

                "percentual_geral": float(
                    teste.resultado.percentual_geral
                ),

                "classificacao_geral": (
                    teste.resultado.classificacao_geral
                ),

                "categorias": [

                    {
                        "categoria": categoria.categoria,
                        "percentual": float(categoria.percentual),
                        "classificacao": categoria.classificacao
                    }

                    for categoria in teste.resultado.categorias

                ]

            }

        testes.append({

            "teste_id": teste.id,

            "data": _data_iso(teste.data_teste),

            "respostas": respostas,

            "resultado": resultado

        })

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
            "data": _data_iso(checkin.data_registro)
        }

        for checkin in checkins_db

    ]

    return {

        "gerado_em": datetime.now(timezone.utc).isoformat(),

        "conta": {
            "email": usuario.email
        },

        "testes": testes,

        "checkins_humor": checkins

    }


def excluir_usuario(usuario_id):
    """
    Apaga a conta e tudo que pertence a ela:
    check-ins, testes, respostas e resultados.

    Devolve True se deu certo e False se algo falhou.
    """

    try:

        # Os check-ins não têm relação no modelo Usuario,
        # então são apagados de forma explícita.
        db.session.execute(
            delete(EmotionalCheckIn)
            .where(
                EmotionalCheckIn.usuario_id == usuario_id
            )
        )

        usuario = db.session.get(
            Usuario,
            usuario_id
        )

        if usuario is None:

            db.session.rollback()

            return False

        # Os testes, as respostas e os resultados são apagados
        # em cascata pelo próprio modelo (cascade="all, delete-orphan").
        db.session.delete(usuario)

        db.session.commit()

        return True

    except Exception:

        db.session.rollback()

        return False