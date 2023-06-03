from flask import render_template, jsonify
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

@app.route('/question')
def question():
    cursor = db.cursor()
    query = "SELECT id, question, answer, valoration FROM `conversations`;"
    cursor.execute(query)
    results = cursor.fetchall() 
    cursor.close()
    return render_template('question.html', conversations=results)

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
    pdf = llama_index.SimpleDirectoryReader("C:\\Users\\jrvaz\\OneDrive\\Desktop\\chatbot-api\\datos").load_data()
    modelo = llama_index.LLMPredictor(llm=ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo'))
    service_context = llama_index.ServiceContext.from_defaults(llm_predictor=modelo)
    index = llama_index.GPTVectorStoreIndex.from_documents(pdf, service_context = service_context)
    index.storage_context.persist()
    return "ok" 

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return 'Página no encontrada', 404
