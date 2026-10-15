from app import app, db
from sqlalchemy import text

with app.app_context():
    resultado = db.session.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = :schema ORDER BY tablename"),
        {"schema": "public"}
    ).all()
    print("Tabelas encontradas:", [linha[0] for linha in resultado])
