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

chatglobal_bp = Blueprint('chatglobal', __name__)

@chatglobal_bp.route('/chatGlobal', methods=['POST'])
def chat():
    print("data")
  
    data = request.json
    print("data", data)
  
    message = data.get('message', '')
    chat_history = data.get('history', [])
    
    if not message:
        return jsonify({"error": "Por favor, proporciona un mensaje"}), 400
    
    try:
        # Detectar si la pregunta es sobre código o estándares
        is_code_request = detect_code_request(message)
        
        # Buscar información relevante en Azure Search
        search_results = []
        if not is_code_request:
            search_results = search_relevant_documents(message)
        
        # Preparar el historial de chat para el contexto
        formatted_history = format_chat_history(chat_history)
        
        # Generar la respuesta con Azure OpenAI
        system_message = get_system_prompt(is_code_request, search_results)
        print(system_message)
      
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                *formatted_history,
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Obtener información sobre tokens
        token_usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        print(f"Uso de tokens en esta llamada:")
        print(f"  - Tokens del prompt: {token_usage['prompt_tokens']}")
        print(f"  - Tokens de la respuesta: {token_usage['completion_tokens']}")
        print(f"  - Total de tokens: {token_usage['total_tokens']}")
        
        assistant_response = response.choices[0].message.content
        print(assistant_response)
        
        # Extraer código si existe en la respuesta
        code_blocks = extract_code_blocks(assistant_response)
        
        return jsonify({
            "response": assistant_response,
            "code_blocks": code_blocks,
            "is_code_request": is_code_request,
            "token_usage": token_usage  # Añadir información de tokens a la respuesta
        })
    
    except Exception as e:
        print(f"Error en solicitud de chat: {e}")
        return jsonify({"error": str(e)}), 500

def detect_code_request(message):
    """Detecta si el mensaje es una solicitud de código"""
    code_patterns = [
        r'escrib[ea]\s+(?:un|el|)\s*código',
        r'gener[ea]\s+(?:un|el|)\s*código',
        r'(?:puedes|podrías)\s+program[ar]',
        r'(?:ejemplo|muestra)\s+(?:de|en)\s+(?:código|python|java|javascript|react|c#|html|css)',
        r'cómo\s+(?:programar|codificar|implementar)',
        r'función\s+(?:para|que)',
        r'dame\s+(?:un|el|)\s*código',
        r'snippet',
        r'código\s+fuente',
        r'class[e]?'
    ]
    
    for pattern in code_patterns:
        if re.search(pattern, message.lower()):
            return True
    
    # Verificar si menciona lenguajes de programación específicos
    languages = ['python', 'javascript', 'java', 'c#', 'react', 'node', 'html', 'css', 'sql', 'php']
    for lang in languages:
        if lang in message.lower():
            return True
    
    return False

def search_relevant_documents(query, top=3):
    """Busca documentos relevantes en Azure Search"""
    try:
        search_results = search_client.search(
            search_text=query,
            top=top,
            search_fields=["content", "title"],
            select=["id", "title", "content", "category"]
        )
        
        results = []
        for result in search_results:
            results.append({
                "id": result["id"],
                "title": result["title"],
                "content": result["content"],
                "category": result.get("category", "General")
            })
        
        return results
    except Exception as e:
        print(f"Error al buscar documentos: {e}")
        return []

def format_chat_history(history):
    """Formatea el historial del chat para Azure OpenAI"""
    formatted = []
    for entry in history:
        if entry.get('role') and entry.get('content'):
            formatted.append({
                "role": entry['role'],
                "content": entry['content']
            })
    return formatted

def get_system_prompt(is_code_request, search_results):
    """Genera el prompt del sistema basado en el tipo de solicitud"""
    if is_code_request:
        return """Eres un asistente de programación experto que ayuda a los desarrolladores.
        Tu tarea es proporcionar código claro, bien comentado y que siga las mejores prácticas de desarrollo.
        Usa ejemplos prácticos y relevantes para el contexto de desarrollo de aplicaciones comerciales.
        El código debe seguir los estándares  y estar optimizado para rendimiento y mantenibilidad.
        Cuando proporciones código, colócalo siempre entre bloques de triple backtick con el lenguaje especificado.
        Ejemplo: ```python\ncódigo aquí\n```
        """
    else:
        context = ""
        if search_results:
            context = "Basándote en los siguientes documentos :\n\n"
            for i, doc in enumerate(search_results):
                context += f"Documento {i+1}: {doc['title']}\n"
                context += f"{doc['content']}\n\n"
        
        return f"""Eres un asistente virtual especializado en los estándares y procesos .
        Tu tarea es proporcionar información precisa y útil sobre las políticas, estándares y procedimientos de la empresa.
        
        {context}
        
        Si no estás seguro de alguna información, indícalo claramente. No inventes información que no esté respaldada por los documentos proporcionados.
        Si te preguntan sobre código, ofrece ejemplos prácticos y bien comentados, siguiendo los estándares de desarrollo .
        Mantén tus respuestas concisas y enfocadas en resolver las consultas del usuario.
        """

def extract_code_blocks(text):
    """Extrae bloques de código de un texto markdown"""
    pattern = r'```(\w*)\n([\s\S]*?)\n```'
    matches = re.findall(pattern, text)
    
    code_blocks = []
    for language, code in matches:
        code_blocks.append({
            "language": language if language else "plaintext",
            "code": code
        })
    
    return code_blocks