from app import app
from backend.database import (
    db,
    criar_tabelas,
    sincronizar_perguntas
)
from backend.perguntas import PERGUNTAS


print("ATENÇÃO: este script apagará as tabelas atuais do banco Mentis.")
confirmacao = input(
    "Digite APAGAR para continuar: "
).strip()


if confirmacao != "APAGAR":

    print("Operação cancelada.")

    raise SystemExit


with app.app_context():

    db.drop_all()

    criar_tabelas()

    sincronizar_perguntas(
        PERGUNTAS
    )


print("")
print("Banco recriado com sucesso.")
print("Tabelas: usuarios, perguntas, testes, respostas, resultados, resultado_categorias.")
