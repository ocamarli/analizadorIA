# app/__init__.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager

from flask_jsonpify import jsonify
from config import config
# Importar tus blueprints
from app.modulos.chatOpenAi import chat_bp
from app.modulos.shearchDocument import search_bp
from app.api.v1.generahistoriasusuio import histories_bp
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
analizarstories_bp = Blueprint('analizarstories', __name__)

@analizarstories_bp.route('/analyze-user-stories', methods=['POST'])
def analyze_user_stories():
    # Verificar si hay archivos en la solicitud
    if 'files' not in request.files:
        return jsonify({"error": "No se encontraron archivos"}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({"error": "No se seleccionaron archivos"}), 400
    
    # Crear directorio temporal para guardar archivos
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Procesar cada archivo PDF
        all_text = ""
        file_info = []
        
        for file in files:
            if file and file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)
                
                # Extraer texto del PDF
                with open(filepath, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    num_pages = len(pdf_reader.pages)
                    
                    text = ""
                    for page_num in range(num_pages):
                        page = pdf_reader.pages[page_num]
                        text += page.extract_text()
                
                all_text += f"\n--- Documento: {filename} ---\n{text}\n"
                file_info.append({
                    "filename": filename,
                    "pages": num_pages,
                    "text_length": len(text)
                })
        
        # Si no hay texto extraído, devolver error
        if not all_text.strip():
            return jsonify({"error": "No se pudo extraer texto de los archivos PDF"}), 400
        
        # Analizar directamente con OpenAI
        analysis_result = analyze_with_openai_direct(all_text, len(file_info))
        
        # Guardar resultados en un directorio
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("analysis_results", timestamp)
        os.makedirs(output_dir, exist_ok=True)
        
        # Guardar los archivos generados
        for file in analysis_result.get("generatedFiles", []):
            file_path = os.path.join(output_dir, file["name"])
            
            # Crear directorios intermedios si es necesario
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file["content"])
        
        # Devolver resultados al frontend
        return jsonify(analysis_result)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        # Limpiar archivos temporales
        for filename in os.listdir(temp_dir):
            os.unlink(os.path.join(temp_dir, filename))
        os.rmdir(temp_dir)

def analyze_with_openai_direct(document_text, num_files):
    """
    Analiza el texto extraído directamente con Azure OpenAI
    sin procesamiento intermedio
    """
    # Crear el mensaje del sistema para el modelo
    system_message = """Eres un experto en análisis de historias de usuario y requisitos de software.
    Tu tarea es analizar documentos que contienen historias de usuario, identificar y extraer estas historias,
    analizar problemas, generar recomendaciones técnicas, funcionales y no funcionales, y detectar información faltante.
    
    Debes responder en formato JSON con la siguiente estructura:
    {
        "filesAnalyzed": número de archivos analizados,
        "totalUserStories": número total de historias de usuario encontradas,
        "totalRecommendations": número total de recomendaciones,
        "userStories": [
            {
                "title": "Título representativo de la historia",
                "content": "Contenido original de la historia",
                "analysis": "Análisis detallado de la historia",
                "issues": [
                    {
                        "title": "Título del problema",
                        "description": "Descripción del problema",
                        "severity": "high/medium/low"
                    }
                ]
            }
        ],
        "recommendations": [
            {
                "title": "Título de la recomendación",
                "description": "Descripción detallada",
                "category": "functional/technical/non-functional",
                "severity": "high/medium/low",
                "tags": ["tag1", "tag2"]
            }
        ],
        "missingInformation": [
            {
                "story": "Referencia a la historia",
                "type": "Tipo de información faltante",
                "description": "Descripción de lo que falta"
            }
        ],
        "generatedFiles": [
            {
                "name": "nombre_del_archivo.extension",
                "content": "contenido del archivo"
            }
        ]
    }
    
    En generatedFiles, incluye archivos que ayuden a implementar o mejorar las historias de usuario,
    como prototipos de código, ejemplos, estructuras de archivos recomendadas, o documentación adicional.
    """
    
    # Crear mensaje para el usuario
    user_message = f"""
    Analiza el siguiente texto extraído de {num_files} documentos PDF que contienen historias de usuario 
    para un proyecto de software:
    
    {document_text}
    
    En tu análisis:
    1. Identifica todas las historias de usuario presentes
    2. Detecta problemas en las historias (ambigüedad, falta de detalle, etc.)
    3. Genera recomendaciones técnicas, funcionales y no funcionales
    4. Identifica información faltante en cada historia
    5. Sugiere mejoras y refinamientos
    6. Genera archivos de ejemplo que podrían ayudar a implementar estas historias (incluye al menos 3 archivos)
    
    Asegúrate de que tu respuesta esté en el formato JSON solicitado.
    """
    
    try:
        # Llamada a Azure OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Asegúrate de que este modelo esté disponible en tu despliegue
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        # Acceder a la respuesta
        result_json = response.choices[0].message.content
        
        # Convertir la respuesta JSON en un objeto Python
        result_data = json.loads(result_json)
        
        return result_data
        
    except Exception as e:
        print(f"Error en la llamada a OpenAI: {e}")
        raise        
