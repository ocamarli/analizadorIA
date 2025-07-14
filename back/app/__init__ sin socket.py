# app/__init__.py
from flask import Flask, request, jsonify
from datetime import timedelta
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from flask_jsonpify import jsonify
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
COGNITIVE_SEARCH_ENDPOINT = "https://azuresearhdemobside.search.windows.net"
COGNITIVE_SEARCH_INDEX = "azureblob-index"
COGNITIVE_SEARCH_API_KEY = "YdBHzUf4al4bPNDgDOLLc9XDnPaxucfrBU47RQbXtRAzSeCujuVS"
search_client = SearchClient(COGNITIVE_SEARCH_ENDPOINT, COGNITIVE_SEARCH_INDEX, AzureKeyCredential(COGNITIVE_SEARCH_API_KEY))
# Importa lo que necesites: openai_client, etc.
# O podrías importarlos desde un archivo de configuración/servicios.
AZURE_OPENAI_ENDPOINT = "https://openaidemobside.openai.azure.com"
AZURE_OPENAI_API_KEY = "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"
AZURE_OPENAI_DEPLOYMENT = "2024-08-01-preview"  # Nombre del deployment en Azure
openai_client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_DEPLOYMENT
)
# Configuración de LangChain
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-14"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKZ9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.7
)

def create_app(env_name='docker'):
    """Crea la aplicación Flask usando un Application Factory."""
    # 1) Instancia Flask
    env = config[env_name]  # config['docker'] en tu caso
    app = Flask(__name__)
    app.config['DEBUG'] = env.DEBUG
    
    # 2) Inicializa extensiones
    CORS(app)
    jwt.init_app(app)

    # 3) Registra los Blueprints
    #    Puedes asignar un url_prefix para cada uno, p.ej. "/api"
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(histories_bp, url_prefix='/api')
    app.register_blueprint(analizarstories_bp,url_prefix='/api')
    app.register_blueprint(chatglobal_bp, url_prefix='/api')
    app.register_blueprint(generarcodigo_bp,url_prefix='/api')
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


    # Ruta raíz (opcional)
    for rule in app.url_map.iter_rules():
     print(rule, rule.methods)
    @app.route("/")
    def root():
        return "Works!!"

    return app