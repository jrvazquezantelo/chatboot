from flask import render_template

from app import app
from auth import verificar_autenticacion

@app.route('/')
@verificar_autenticacion
def home():
    return render_template('home.html')

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return 'Página no encontrada', 404
