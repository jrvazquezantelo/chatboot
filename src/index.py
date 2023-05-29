from flask import Flask, render_template, request, redirect
import bcrypt
import mysql.connector

db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='b11'
)

app = Flask(__name__)

def verificar_autenticacion(func):
    def wrapper(*args, **kwargs):
        usuario_autenticado = False
        if usuario_autenticado:
            return func(*args, **kwargs)
        else:
            return redirect('/login')
    return wrapper

@app.route('/')
@verificar_autenticacion
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Obtener el hash almacenado de la base de datos
        cursor = db.cursor()
        query = "SELECT password FROM users WHERE username = %s"
        values = (username,)
        cursor.execute(query, values)
        result = cursor.fetchone()

        if result is not None:
            stored_hash = result[0].encode('utf-8')

            # Verificar la contraseña utilizando bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                # Credenciales válidas, redireccionar a la página de inicio
                return redirect('/inicio')

        # Credenciales inválidas, mostrar mensaje de error
        error_message = 'Credenciales inválidas. Inténtalo nuevamente.'
        return render_template('login.html', error_message=error_message)

    # Si la solicitud es GET, mostrar la página de inicio de sesión
    return render_template('login.html')

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return 'Página no encontrada', 404

if __name__ == '__main__':
    app.run(debug=True)
