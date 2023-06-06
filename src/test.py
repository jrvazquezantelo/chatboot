from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '¡Hola, mundo!'

if __name__ == '__main__':   
    port = 8080
    # Ejecuta la aplicación en el puerto especificado
    app.run(host='0.0.0.0', port=port)