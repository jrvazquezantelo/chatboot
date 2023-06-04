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
                session['error_message'] = 'Ocurrió un error al guardar la conversación'.format(str(e))
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
                session['error_message'] = 'Ocurrió un error al actualizar la conversación'.format(str(e))
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
        session['error_message'] = 'Ocurrió un error al eliminar la conversación'.format(str(e))
    finally:
        cursor.close()
    return redirect('/conversation')

@app.route('/train')
def train():
    pdf_query = "SELECT * FROM `pdf`;"
    train_query = "SELECT * FROM `train`;"

    pdf_results = execute_query(pdf_query)
    total_pdf = len(pdf_results)
    train_results = execute_query(train_query)

    success_message = session.pop('success_message', None)
    error_message = session.pop('error_message', None)

    return render_template('train.html', pdfs=pdf_results, success_message=success_message, error_message=error_message, total_pdf=total_pdf, train_results=train_results[0], percent=100)

@app.route('/add_file', methods=['POST'])
def add_file():
    if 'file' not in request.files:
        return 'No se seleccionó ningún archivo.'

    file = request.files['file']

    if file.filename == '':
        return 'No se seleccionó ningún archivo.'

    file_name = file.filename
    file_size = file.content_length

    file_ext = file_name.rsplit('.', 1)[1].lower()

    # Verificar si la extensión del archivo es PDF
    if file_ext != 'pdf':
        return 'El archivo seleccionado no es un archivo PDF válido.'
    
    # Verificar si el nombre de archivo ya existe en la base de datos
    cursor = db.cursor()
    check_query = "SELECT * FROM pdf WHERE filename = %s"
    cursor.execute(check_query, (file_name,))
    existing_file = cursor.fetchone()
    if existing_file:
        cursor.close()
        return 'El nombre de archivo ya existe.'

    ruta_script = os.path.abspath(__file__)
    ruta_raiz = os.path.dirname(ruta_script)
    ruta_static_data = os.path.join(ruta_raiz, 'static', 'data/')
    file.save(ruta_static_data + file_name)

    cursor = db.cursor()
    insert_query = "INSERT INTO pdf (filename, size) VALUES (%s, %s)"
    try:
        cursor.execute(insert_query, (file_name, file_size))
        db.commit()
        session['success_message'] = 'El documento se ha registrado exitosamente.'
    except Exception as e:
        db.rollback()
        session['error_message'] = 'Ocurrió un error al registrar el documento'.format(str(e))
    finally:
        cursor.close()

    return redirect('/train')

@app.route('/delete_file/<int:file_id>', methods=['GET'])
def delete_file(file_id):
    cursor = db.cursor()

    # Obtener el nombre del archivo y eliminarlo del sistema de archivos
    query = "SELECT filename FROM pdf WHERE id = %s"
    cursor.execute(query, (file_id,))
    result = cursor.fetchone()

    if not result:
        cursor.close()
        return 'El archivo no existe.'

    file_name = result[0]
    ruta_script = os.path.abspath(__file__)
    ruta_raiz = os.path.dirname(ruta_script)
    ruta_static_data = os.path.join(ruta_raiz, 'static', 'data/')
    file_path = os.path.join(ruta_static_data, file_name)

    try:
        os.remove(file_path)
    except OSError as e:
        cursor.close()
        return 'Ocurrió un error al eliminar el archivo.'

    # Eliminar el registro del archivo de la base de datos
    delete_query = "DELETE FROM pdf WHERE id = %s"
    try:
        cursor.execute(delete_query, (file_id,))
        db.commit()
        session['success_message'] = 'El archivo se ha eliminado exitosamente.'
    except Exception as e:
        db.rollback()
        session['error_message'] = 'Ocurrió un error al eliminar el documento'.format(str(e))
    finally:
        cursor.close()

    return redirect('/train')

def execute_query(query):
    cursor = db.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    return results

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/edit_train')
def edit_train():
    cursor = db.cursor()
    check_query = "SELECT api_key FROM token"
    cursor.execute(check_query)
    existing_token = cursor.fetchone()
    cursor.close()
    if existing_token:        
        try:
            os.environ["OPENAI_API_KEY"] = existing_token[0]
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
                session['success_message'] = f'Enhorabuena cantidad de hojas entrenadas: {number_of_sheets}'
            else:
                session['error_message'] = 'No hay datos disponibles para el entrenamiento'
        except Exception as e:         
            session['error_message'] = 'Ocurrió un error en el entrenamiento'.format(str(e))
        finally:
            # Ejecutar consulta UPDATE
            cursor = db.cursor()
            update_query = "UPDATE train SET pages = %s WHERE id = 1"
            cursor.execute(update_query, (number_of_sheets,))
            db.commit()
            return redirect('/train')
        
@app.route('/chatboot', methods=['POST'])
def chatboot():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            question = data.get('question')
        else:
            question = request.form.get('question')

        if not question:
            error_message = {
                'error': 'Bad Request',
                'message': 'El parámetro "question" es obligatorio. Por favor, proporcione una pregunta válida.'
            }
            return jsonify(error_message), 400

        cursor = db.cursor()
        check_query = "SELECT answer FROM conversations WHERE question = %s"
        cursor.execute(check_query, (question,))
        existing_conversation = cursor.fetchone()

        if existing_conversation:
            answer = existing_conversation[0]
        else:
            cursor = db.cursor()
            check_query = "SELECT api_key FROM token"
            cursor.execute(check_query)
            existing_token = cursor.fetchone()
            if existing_token:
                os.environ["OPENAI_API_KEY"] = existing_token[0]
                storage_context = llama_index.StorageContext.from_defaults(persist_dir='./storage')
                index = llama_index.load_index_from_storage(storage_context)
                processed_question = "¿" + question + "? responde en español y no diga los nombres de los archivos"
                respuesta = index.as_query_engine().query(processed_question)  # Realiza la consulta con la pregunta
                answer = str(respuesta)
                # Guardar la pregunta y respuesta en la base de datos
                insert_query = "INSERT INTO conversations (question, answer) VALUES (%s, %s)"
                cursor.execute(insert_query, (question, answer))
                db.commit()
            else:
                answer = 'No se encontró una respuesta para la pregunta proporcionada.'

        return jsonify({'answer': answer})

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return 'Página no encontrada', 404
