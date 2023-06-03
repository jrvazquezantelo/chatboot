from flask import render_template, jsonify, request, redirect, session, url_for
from app import app
from auth import verificar_autenticacion
from database import db
import os
import openai
import llama_index
from langchain.chat_models import ChatOpenAI

@app.route('/')
@verificar_autenticacion
def home():
    return render_template('home.html')

@app.route('/conversation')
def conversation():
    cursor = db.cursor()
    query = "SELECT id, question, answer FROM `conversations`;"
    cursor.execute(query)
    results = cursor.fetchall() 
    cursor.close()
    success_message = session.pop('success_message', None)
    error_message = session.pop('error_message', None)
    return render_template('conversation.html', conversations=results, success_message=success_message, error_message=error_message)

@app.route('/add_conversation', methods=['POST'])
def add_conversation():
    if request.method == 'POST':
        question = request.form['question']
        answer = request.form['answer']
        cursor = db.cursor()
        
         # Verificar si la pregunta ya existe en la base de datos
        check_query = "SELECT * FROM conversations WHERE question = %s"
        cursor.execute(check_query, (question,))
        existing_conversation = cursor.fetchone()
            
        if existing_conversation:
            session['error_message'] = 'La pregunta ya existe en la base de datos.'
        else:
            query = "INSERT INTO conversations (question, answer) VALUES (%s, %s)"  # Corrección en la consulta SQL
            try:
                cursor.execute(query, (question, answer))
                db.commit()
                session['success_message'] = 'La conversación se ha guardado exitosamente.'
            except Exception as e:
                db.rollback()
                session['error_message'] = 'Ocurrió un error al guardar la conversación.'
            finally:
                cursor.close()
    return redirect('/conversation')
    
@app.route('/edit_conversation', methods=['POST'])
def edit_conversation():
    if request.method == 'POST':
        id = request.form['id']
        question = request.form['question']
        answer = request.form['answer']
        cursor = db.cursor()

        # Verificar si la pregunta ya existe en la base de datos, excluyendo la conversación actual
        check_query = "SELECT * FROM conversations WHERE question = %s AND id <> %s"
        cursor.execute(check_query, (question, id))
        existing_conversation = cursor.fetchone()

        if existing_conversation:
            session['error_message'] = 'La pregunta ya existe en la base de datos.'
        else:
            query = "UPDATE conversations SET question = %s, answer = %s WHERE id = %s"
            try:
                cursor.execute(query, (question, answer, id))
                db.commit()
                session['success_message'] = 'La conversación se ha actualizado exitosamente.'
            except Exception as e:
                db.rollback()
                session['error_message'] = 'Ocurrió un error al actualizar la conversación.'
            finally:
                cursor.close()
    return redirect('/conversation')
    
@app.route('/delete_conversation/<int:conversation_id>', methods=['GET'])
def delete_conversation(conversation_id):
    cursor = db.cursor()
    query = "DELETE FROM conversations WHERE id = %s"
    try:
        cursor.execute(query, (conversation_id,))
        db.commit()
        session['success_message'] = 'La conversación se ha eliminado exitosamente.'
    except Exception as e:
        db.rollback()
        session['error_message'] = 'Ocurrió un error al eliminar la conversación.'
    finally:
        cursor.close()
    return redirect('/conversation')

@app.route('/chatboot', methods=['POST'])
def chatboot():
    os.environ["OPENAI_API_KEY"] = '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'
    storage_context = llama_index.StorageContext.from_defaults(persist_dir='./storage')
    index = llama_index.load_index_from_storage(storage_context)
    pregunta = "¿ cuantas horas dura este curso?"  # Puedes cambiar la pregunta aquí
    respuesta = index.as_query_engine().query(pregunta)  # Realiza la consulta con la pregunta
    return str(respuesta)

@app.route('/train')
def train():
    os.environ["OPENAI_API_KEY"] = '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'
    ruta_script = os.path.abspath(__file__)
    ruta_raiz = os.path.dirname(ruta_script)
    ruta_static_data = os.path.join(ruta_raiz, 'static', 'data')
    sheets = llama_index.SimpleDirectoryReader(ruta_static_data).load_data()
    number_of_sheets = len(sheets)
    if number_of_sheets > 0:
        model = llama_index.LLMPredictor(llm=ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo'))
        service_context = llama_index.ServiceContext.from_defaults(llm_predictor=model)
        index = llama_index.GPTVectorStoreIndex.from_documents(sheets, service_context = service_context)
        index.storage_context.persist()
        return f'Enhorabuena cantidad de hojas entrenadas: {number_of_sheets}'
    else:
        return 'No hay datos disponibles para el entrenamiento'

@app.route('/pruebas', methods=['POST'])
def pruebas():
    return "prueba"

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return 'Página no encontrada', 404
