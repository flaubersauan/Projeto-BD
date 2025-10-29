from flask import Flask
from database import Session
from sqlalchemy import text
app = Flask(__name__)

db = Session()

query = "SELECT Nome_usuario, Email FROM usuarios WHERE ID_usuario = 1;"
resultado = db.execute(text(query))

for linha in resultado:
    print(f"Nome: {linha.Nome_usuario}, E-mail: {linha.Email}")