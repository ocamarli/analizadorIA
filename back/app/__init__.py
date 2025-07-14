# app/__init__.py
from flask import Flask, request, jsonify
from datetime import timedelta
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from flask_jsonpify import jsonify
from flask_socketio import SocketIO
from config import config
from langchain_community.chat_models import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import glob
import os
import datetime
import json

# Importar tus blueprints
from app.modulos.chatOpenAi import chat_bp
from app.modulos.shearchDocument import search_bp
from app.api.v1.generahistoriasusuio import histories_bp
from app.api.v1.analizarhistorias import analizarstories_bp
from app.api.v1.generarcodigo import generarcodigo_bp

from app.api.v1.scrap import scrap_bp
from app.api.v1.apicatalogs import catalogos_bp
from app.api.v1.generaHistoriasTecnicas import genera_historias_tecnicas_bp
from app.api.v1.generaDEF import def_bp
from app.api.v1.analizarLegadoCloud import analizarLegadoCloud_bp
from app.api.v1.analizaCodigoo import analizarCodigoo_bp
from app.api.v1.analizarGO import analizarGo_bp
from app.api.v1.generarUMLSecuencia import diagramaSecuencia_bp
from app.api.v1.chatglobal import chatglobal_bp
from app.api.v1.generarUMLClases import diagramaClases_bp
from app.api.v1.generarUMLSecuenciaMermaid import diagramaSecuenciaMermaid_bp
from app.api.v1.generarUMLFlujoMermaid import diagramaFlujoMermaid_bp
from app.api.v1.generarUMLClasesMermaid import diagramaClasesMermaid_bp
from app.api.v1.analizaCodigoRepomix import analizarCodigoRepomix_bp
from app.api.v1.analizaSQL import analizarCodigoSQL_bp
from app.api.v1.adm import adm_bp
from app.api.v1.analizarArquitectura import analizar_arquitectura_bp
from app.api.v1.generarUMLArquiMermaid import diagramaArquitecturaMermaid_bp
from app.api.v1.generarArquitecturaToBe import generar_arquitectura_tobe_bp
from app.api.v1.generaModeladoDatos import generar_modelado_bp
from app.api.v1.generaUMLMatrizImpacto import diagramaMatrizImpacto_bp
from app.api.v1.generarUMLArquitecturaMermaid import diagramaArquitectura_bp
from app.api.v1.generarDocArquitecturaGeneral import documentoArquitectura_bp
from app.api.v1.generarDocServicios import documentoServicios_bp
from app.api.v1.generarux import generaUx_bp
from app.api.v1.generarUMLArquiteturaTecnologiaMermaid import diagramaTecnologia_bp

import glob
import os
import requests
import datetime
import tempfile
from openai import AzureOpenAI
from werkzeug.utils import secure_filename
import PyPDF2
import json
import re
from flask import Flask, request, jsonify
jwt = JWTManager()
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Configuraciones globales
COGNITIVE_SEARCH_ENDPOINT = "https://azuresearhdemobside.search.windows.net"
COGNITIVE_SEARCH_INDEX = "azureblob-index"
COGNITIVE_SEARCH_API_KEY = "YdBHzUf4al4bPNDgDOLLc9XDnPaxucfrBU47RQbXtRAzSeCujuVS"
search_client = SearchClient(COGNITIVE_SEARCH_ENDPOINT, COGNITIVE_SEARCH_INDEX, AzureKeyCredential(COGNITIVE_SEARCH_API_KEY))

AZURE_OPENAI_ENDPOINT = "https://openaidemobside.openai.azure.com"
AZURE_OPENAI_API_KEY = "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"
AZURE_OPENAI_DEPLOYMENT = "2024-08-01-preview"

openai_client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_DEPLOYMENT
)

# Configuración de LangChain
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-14"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.7
)

# Variable global para SocketIO
socketio = None

def create_app(env_name='docker'):
    """Crea la aplicación Flask usando un Application Factory."""
    global socketio
    
    # 1) Instancia Flask
    env = config[env_name]  # config['docker'] en tu caso
    app = Flask(__name__)
    app.config['DEBUG'] = env.DEBUG
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
    
    # 2) Inicializa extensiones
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    jwt.init_app(app)
    
    # 3) Inicializar SocketIO
    socketio = SocketIO(
        app,
        cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        async_mode='threading',
        logger=True,
        engineio_logger=True
    )
    
    # 4) Configurar eventos de SocketIO
    @socketio.on('connect')
    def handle_connect():
        print('Cliente conectado via WebSocket')
        
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Cliente desconectado via WebSocket')

    @socketio.on('join_session')
    def handle_join_session(data):
        session_id = data.get('session_id')
        if session_id:
            print(f'Cliente unido a sesión: {session_id}')

    # 5) Registra los Blueprints
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(histories_bp, url_prefix='/api')
    app.register_blueprint(analizarstories_bp, url_prefix='/api')
    app.register_blueprint(chatglobal_bp, url_prefix='/api')
    app.register_blueprint(generarcodigo_bp, url_prefix='/api')
    app.register_blueprint(scrap_bp, url_prefix='/api')
    app.register_blueprint(search_bp, url_prefix='/api')
    app.register_blueprint(catalogos_bp, url_prefix='/api')
    app.register_blueprint(adm_bp, url_prefix='/api')
    app.register_blueprint(genera_historias_tecnicas_bp, url_prefix='/api')
    app.register_blueprint(def_bp, url_prefix='/api')
    app.register_blueprint(analizarCodigoo_bp, url_prefix='/api')
    app.register_blueprint(analizarGo_bp, url_prefix='/api')
    app.register_blueprint(analizarLegadoCloud_bp, url_prefix='/api')
    app.register_blueprint(diagramaSecuencia_bp, url_prefix='/api')
    app.register_blueprint(diagramaClases_bp, url_prefix='/api')
    app.register_blueprint(diagramaSecuenciaMermaid_bp, url_prefix='/api')
    app.register_blueprint(diagramaFlujoMermaid_bp, url_prefix='/api')    
    app.register_blueprint(diagramaClasesMermaid_bp, url_prefix='/api')
    app.register_blueprint(analizarCodigoRepomix_bp, url_prefix='/api')
    app.register_blueprint(analizarCodigoSQL_bp, url_prefix='/api')
    app.register_blueprint(analizar_arquitectura_bp, url_prefix='/api')
    app.register_blueprint(generar_arquitectura_tobe_bp, url_prefix='/api')
    app.register_blueprint(generar_modelado_bp, url_prefix='/api')
    app.register_blueprint(diagramaMatrizImpacto_bp,url_prefix='/api')
    app.register_blueprint(diagramaArquitectura_bp,url_prefix='/api')
    app.register_blueprint(documentoArquitectura_bp,url_prefix='/api')
    app.register_blueprint(documentoServicios_bp,url_prefix='/api')
    app.register_blueprint(generaUx_bp,url_prefix='/api')
    app.register_blueprint(diagramaTecnologia_bp,url_prefix='/api')
    

    # 6) Inicializar SocketIO en el blueprint de SQL
    from app.api.v1.analizaSQL import init_socketio
    init_socketio(socketio)

    # 7) Rutas adicionales
    @app.route("/")
    def root():
        return jsonify({
            "message": "API de Análisis de Código y Bases de Datos",
            "version": "2.0.0",
            "features": [
                "Análisis de código",
                "Generación de historias de usuario",
                "Análisis DEF",
                "Progreso en tiempo real via WebSocket",
                "Chunking automático",
                "Rate limiting con reintentos"
            ],
            "websocket": "enabled"
        })
    
    @app.route("/health")
    def health():
        return jsonify({"status": "healthy", "websocket": "enabled"})

    # Imprimir rutas registradas (para debug)
    for rule in app.url_map.iter_rules():
        print(rule, rule.methods)

    return app, socketio

def get_socketio():
    """Función helper para obtener la instancia de SocketIO"""
    global socketio
    return socketio