from flask import render_template, request, redirect, session
import bcrypt
import mysql.connector

from app import app

db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='b11'
)

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

        error_message = 'Credenciales inválidas. Inténtalo nuevamente.'
        return render_template('login.html', error_message=error_message)

    if 'username' in session:
        return redirect('/')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')
