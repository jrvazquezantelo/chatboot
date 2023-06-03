from flask import Flask
app = Flask(__name__)
app.secret_key = 'DAWDA*"·23'  # Clave secreta para las sesiones

if __name__ == '__main__':
    app.run(debug=True)