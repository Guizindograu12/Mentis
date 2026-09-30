from app import app
from backend.database import db, Resposta


with app.app_context():

    total = db.session.execute(
        db.select(db.func.count(Resposta.id))
    ).scalar_one()

    print("TOTAL:", total)

    dados = db.session.execute(
        db.select(
            Resposta.id,
            Resposta.teste_id,
            Resposta.pergunta_id,
            Resposta.resposta
        ).order_by(
            Resposta.id
        )
    ).all()

    for linha in dados:

        print(tuple(linha))
