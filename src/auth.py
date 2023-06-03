from flask import render_template, request, redirect, session
import bcrypt
from database import db

from app import app

def verificar_autenticacion(func):
    def wrapper(*args, **kwargs):
        if 'username' in session:
            return func(*args, **kwargs)
        else:
            return redirect('/login')
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = db.cursor()
        query = "SELECT password FROM users WHERE username = %s"
        values = (username,)
        cursor.execute(query, values)
        result = cursor.fetchone()

        if result is not None:
            stored_hash = result[0].encode('utf-8')

            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                # Autenticación exitosa, establecer la sesión del usuario
                session['username'] = username
                return redirect('/')

            # La contraseña no coincide, mostrar mensaje de error
            error_message = 'Clave incorrecta. Inténtalo nuevamente.'
        else:
            # El usuario no existe, mostrar mensaje de error
            error_message = 'El usuario no existe.'

        return render_template('login.html', error_message=error_message)

    if 'username' in session:
        return redirect('/')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')
