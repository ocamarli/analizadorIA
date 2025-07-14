# app/api/v1/analizaSQL.py
from flask import Blueprint, request, jsonify
from datetime import timedelta
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from flask_jsonpify import jsonify
from flask_socketio import SocketIO, emit
from config import config
from langchain_community.chat_models import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
import os
import datetime
import json
import re
import tempfile
import shutil
import zipfile
import time
import random
import traceback
import threading
import uuid
from werkzeug.utils import secure_filename
from typing import Optional, Dict, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint
analizarCodigoSQL_bp = Blueprint('analizarCodigoSQL', __name__)

# Variable global para SocketIO (se inicializa desde __init__.py)
socketio = None

def init_socketio(app_socketio):
    """Inicializar SocketIO desde __init__.py"""
    global socketio
    socketio = app_socketio
    logger.info("SocketIO inicializado en analizaSQL blueprint")

# Diccionario global para rastrear progreso de análisis
analysis_progress = {}

class ProgressTracker:
    def __init__(self, session_id, total_chunks=1):
        self.session_id = session_id
        self.total_chunks = total_chunks
        self.current_chunk = 0
        self.current_phase = "Iniciando"
        self.overall_progress = 0
        self.chunks_completed = 0
        
    def update_chunk_progress(self, chunk_number, phase="Procesando"):
        self.current_chunk = chunk_number
        self.current_phase = phase
        
        # Calcular progreso con más granularidad y movimiento
        if phase == "Extrayendo archivos":
            self.overall_progress = 5
        elif phase.startswith("Procesando archivos"):
            self.overall_progress = 15
        elif phase.startswith("Archivos procesados") or phase.startswith("Iniciando análisis"):
            self.overall_progress = 25
        elif "Iniciando análisis de historias de usuario" in phase:
            self.overall_progress = 30
        elif "Procesando épicas chunk" in phase:
            # Progreso de chunks épicas: del 30% al 65% (35% total)
            if self.total_chunks > 1:
                chunk_progress = (chunk_number / self.total_chunks) * 35
                self.overall_progress = 30 + chunk_progress
            else:
                self.overall_progress = 50
        elif "Consolidando épicas finales" in phase:
            self.overall_progress = 70
        elif "Iniciando análisis DEF" in phase:
            self.overall_progress = 75
        elif "Procesando DEF chunk" in phase:
            # Progreso de chunks DEF: del 75% al 90% (15% total)
            if self.total_chunks > 1:
                chunk_progress = (chunk_number / self.total_chunks) * 15
                self.overall_progress = 75 + chunk_progress
            else:
                self.overall_progress = 85
        elif "Consolidando análisis DEF" in phase:
            self.overall_progress = 92
        elif "completado" in phase.lower() or "completadas" in phase.lower():
            self.overall_progress = 100
        else:
            # Fallback: distribución más granular para otros casos
            if self.total_chunks > 1:
                base_progress = 30 + (chunk_number / self.total_chunks) * 60
                self.overall_progress = min(base_progress, 95)
            else:
                self.overall_progress = 85
        
        # Asegurar que nunca exceda 100% y que siempre avance
        self.overall_progress = min(max(self.overall_progress, 0), 100)
        
        # Emitir progreso via WebSocket si está disponible
        if socketio:
            try:
                socketio.emit('analysis_progress', {
                    'session_id': self.session_id,
                    'total_chunks': self.total_chunks,
                    'current_chunk': chunk_number,
                    'phase': phase,
                    'progress': int(self.overall_progress)
                })
                logger.info(f"Progreso emitido via WebSocket: {int(self.overall_progress)}%")
            except Exception as e:
                logger.warning(f"Error enviando progreso via WebSocket: {e}")
        
        logger.info(f"Progreso {self.session_id}: {int(self.overall_progress)}% - {phase} chunk {chunk_number}/{self.total_chunks}")

    def set_consolidation_progress(self, consolidation_type, progress_within_consolidation=0):
        """Método específico para progreso detallado durante consolidación"""
        if consolidation_type == "epicas":
            # Consolidación de épicas: 70-74%
            self.overall_progress = 70 + (progress_within_consolidation * 4 / 100)
            phase = f"Consolidando épicas... {progress_within_consolidation}%"
        elif consolidation_type == "def":
            # Consolidación de DEF: 92-97%
            self.overall_progress = 92 + (progress_within_consolidation * 5 / 100)
            phase = f"Consolidando análisis DEF... {progress_within_consolidation}%"
        else:
            return
            
        # Emitir progreso
        if socketio:
            try:
                socketio.emit('analysis_progress', {
                    'session_id': self.session_id,
                    'total_chunks': self.total_chunks,
                    'current_chunk': self.current_chunk,
                    'phase': phase,
                    'progress': int(self.overall_progress)
                })
            except Exception as e:
                logger.warning(f"Error enviando progreso de consolidación: {e}")
                
        logger.info(f"Consolidación {self.session_id}: {int(self.overall_progress)}% - {phase}")

    def complete_analysis(self):
        """Marcar análisis como completado al 100%"""
        self.overall_progress = 100
        phase = "Análisis completado exitosamente"
        
        if socketio:
            try:
                socketio.emit('analysis_progress', {
                    'session_id': self.session_id,
                    'total_chunks': self.total_chunks,
                    'current_chunk': self.total_chunks,
                    'phase': phase,
                    'progress': 100
                })
                logger.info("Progreso completado al 100% emitido via WebSocket")
            except Exception as e:
                logger.warning(f"Error enviando progreso final: {e}")
        
        logger.info(f"Análisis completado {self.session_id}: 100% - {phase}")

# Configuración de Rate Limiting
class RateLimitConfig:
    MAX_RETRIES = 5
    BASE_DELAY = 2
    MAX_DELAY = 300.0
    EXPONENTIAL_BACKOFF = True
    JITTER_FACTOR = 0.1
    RATE_LIMIT_ERRORS = [429, 503, 502, 504, 500]
    RATE_LIMIT_KEYWORDS = [
        'rate limit', 'too many requests', 'quota exceeded',
        'service unavailable', 'timeout', 'busy', 'overloaded',
        'throttled', 'rate exceeded', 'api limit'
    ]

class RateLimitHandler:
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.retry_count = 0
        
    def is_rate_limit_error(self, error: Exception) -> bool:
        """Determina si el error es debido a rate limiting"""
        error_message = str(error).lower()
        
        # Verificar palabras clave en el mensaje de error
        for keyword in self.config.RATE_LIMIT_KEYWORDS:
            if keyword in error_message:
                logger.info(f"Rate limit detectado por palabra clave: {keyword}")
                return True
        
        # Verificar si es un error HTTP específico (si es aplicable)
        if hasattr(error, 'status_code'):
            if error.status_code in self.config.RATE_LIMIT_ERRORS:
                logger.info(f"Rate limit detectado por código HTTP: {error.status_code}")
                return True
                
        # Verificar errores específicos de OpenAI/Azure
        if 'openai' in error_message or 'azure' in error_message:
            if any(keyword in error_message for keyword in ['rate', 'quota', 'limit', 'throttle']):
                logger.info("Rate limit detectado en servicio OpenAI/Azure")
                return True
                
        return False
    
    def calculate_delay(self, retry_count: int) -> float:
        """Calcula el tiempo de espera con backoff exponencial y jitter"""
        if self.config.EXPONENTIAL_BACKOFF:
            delay = self.config.BASE_DELAY * (2 ** retry_count)
        else:
            delay = self.config.BASE_DELAY * (retry_count + 1)
        
        # Añadir jitter para evitar thundering herd
        jitter = delay * self.config.JITTER_FACTOR * random.random()
        delay += jitter
        
        # Limitar el delay máximo
        return min(delay, self.config.MAX_DELAY)
    
    def execute_with_retry(self, func, *args, **kwargs):
        """Ejecuta una función con retry automático en caso de rate limiting"""
        self.retry_count = 0
        last_error = None
        
        while self.retry_count <= self.config.MAX_RETRIES:
            try:
                logger.info(f"Intento {self.retry_count + 1}/{self.config.MAX_RETRIES + 1}")
                result = func(*args, **kwargs)
                
                # Reset contador si fue exitoso
                if self.retry_count > 0:
                    logger.info(f"Operación exitosa después de {self.retry_count} reintentos")
                self.retry_count = 0
                return result
                
            except Exception as error:
                last_error = error
                logger.error(f"Error en intento {self.retry_count + 1}: {str(error)}")
                
                # Verificar si es un error de rate limiting
                if not self.is_rate_limit_error(error):
                    logger.info("Error no relacionado con rate limiting, no reintentando")
                    raise error
                
                # Si ya excedimos los reintentos
                if self.retry_count >= self.config.MAX_RETRIES:
                    logger.error(f"Rate limit excedido después de {self.config.MAX_RETRIES} reintentos")
                    raise Exception(f"Rate limit excedido después de {self.config.MAX_RETRIES} reintentos. Último error: {str(error)}")
                
                # Calcular tiempo de espera
                delay = self.calculate_delay(self.retry_count)
                self.retry_count += 1
                
                logger.warning(f"Rate limit detectado. Esperando {delay:.2f} segundos antes del reintento {self.retry_count + 1}")
                time.sleep(delay)
        
        # Si llegamos aquí, algo salió mal
        raise last_error or Exception("Error desconocido en rate limit handler")

# Instanciar handler global
rate_limit_handler = RateLimitHandler()

# Configuración de LangChain con manejo de errores mejorado
def create_llm_instance():
    """Crea una instancia de LLM con configuración robusta"""
    try:
        return AzureChatOpenAI(
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
            temperature=0.7,
            request_timeout=120,
            max_retries=0
        )
    except Exception as e:
        logger.error(f"Error creando instancia LLM: {e}")
        raise

llm = create_llm_instance()

# Función wrapper para invocar LLM con rate limiting
def invoke_llm_with_retry(messages, context=""):
    """Invoca el LLM con manejo de rate limiting"""
    def _invoke():
        logger.info(f"Invocando LLM para: {context}")
        return llm.invoke(messages)
    
    return rate_limit_handler.execute_with_retry(_invoke)

# Configuración para subida de archivos
ALLOWED_EXTENSIONS = {'.sql', '.ddl', '.dml', '.pgsql', '.psql', '.mysql', '.plsql', '.proc', 
                     '.sp', '.fn', '.udf', '.view', '.trigger', '.idx', '.schema', '.dump',
                     '.backup', '.db', '.sqlite', '.sqlite3', '.dbf', '.mdb', '.accdb'}
MAX_FILES = 5000
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB por archivo

def allowed_file(filename):
    return os.path.splitext(filename.lower())[1] in ALLOWED_EXTENSIONS

# Función para dividir el código en chunks si es muy largo
def split_code_into_chunks(code, max_chunk_size=35000):
    """Divide el código en chunks manejables para evitar límites de tokens"""
    if len(code) <= max_chunk_size:
        logger.info("Código no requiere división en chunks")
        return [code]
    
    logger.info(f"Dividiendo código de {len(code)} caracteres en chunks de máximo {max_chunk_size}")
    
    chunks = []
    current_chunk = ""
    lines = code.split('\n')
    
    for line in lines:
        # Si agregar esta línea excede el tamaño máximo
        if len(current_chunk) + len(line) + 1 > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                logger.info(f"Chunk {len(chunks)} creado con {len(current_chunk)} caracteres")
                current_chunk = line
            else:
                # Línea muy larga, la incluimos tal como está
                chunks.append(line)
                logger.info(f"Chunk {len(chunks)} creado con línea larga de {len(line)} caracteres")
        else:
            current_chunk += '\n' + line if current_chunk else line
    
    # Agregar el último chunk si tiene contenido
    if current_chunk:
        chunks.append(current_chunk)
        logger.info(f"Chunk final {len(chunks)} creado con {len(current_chunk)} caracteres")
    
    logger.info(f"División completada: {len(chunks)} chunks creados")
    return chunks

# Función para analizar archivos de bases de datos
def analyze_database_code(content):
    """Analiza archivos de base de datos para extraer elementos SQL"""
    tables = []
    procedures = []
    functions = []
    views = []
    triggers = []
    indexes = []
    schemas = []
    
    # Convertir a minúsculas para búsqueda case-insensitive
    content_lower = content.lower()
    
    # Buscar tablas
    table_patterns = [
        r'create\s+table\s+(?:if\s+not\s+exists\s+)?(?:`?(\w+)`?\.)?`?(\w+)`?',
        r'alter\s+table\s+(?:`?(\w+)`?\.)?`?(\w+)`?',
        r'drop\s+table\s+(?:if\s+exists\s+)?(?:`?(\w+)`?\.)?`?(\w+)`?'
    ]
    
    for pattern in table_patterns:
        matches = re.findall(pattern, content_lower, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            table_name = match[1] if isinstance(match, tuple) and len(match) > 1 else match
            if table_name and table_name not in tables:
                tables.append(table_name)
    
    # Buscar procedimientos almacenados
    procedure_patterns = [
        r'create\s+(?:or\s+replace\s+)?procedure\s+(?:`?(\w+)`?\.)?`?(\w+)`?',
        r'create\s+(?:or\s+replace\s+)?proc\s+(?:`?(\w+)`?\.)?`?(\w+)`?',
        r'delimiter\s*\$\$\s*create\s+procedure\s+(?:`?(\w+)`?\.)?`?(\w+)`?'
    ]
    
    for pattern in procedure_patterns:
        matches = re.findall(pattern, content_lower, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            proc_name = match[1] if isinstance(match, tuple) and len(match) > 1 else match
            if proc_name and proc_name not in procedures:
                procedures.append(proc_name)
    
    # Buscar funciones
    function_patterns = [
        r'create\s+(?:or\s+replace\s+)?function\s+(?:`?(\w+)`?\.)?`?(\w+)`?',
        r'create\s+(?:or\s+replace\s+)?definer\s*=\s*[^\s]+\s+function\s+(?:`?(\w+)`?\.)?`?(\w+)`?'
    ]
    
    for pattern in function_patterns:
        matches = re.findall(pattern, content_lower, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            func_name = match[1] if isinstance(match, tuple) and len(match) > 1 else match
            if func_name and func_name not in functions:
                functions.append(func_name)
    
    # Buscar vistas
    view_patterns = [
        r'create\s+(?:or\s+replace\s+)?view\s+(?:`?(\w+)`?\.)?`?(\w+)`?',
        r'create\s+(?:materialized\s+)?view\s+(?:`?(\w+)`?\.)?`?(\w+)`?'
    ]
    
    for pattern in view_patterns:
        matches = re.findall(pattern, content_lower, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            view_name = match[1] if isinstance(match, tuple) and len(match) > 1 else match
            if view_name and view_name not in views:
                views.append(view_name)
    
    # Buscar triggers
    trigger_patterns = [
        r'create\s+(?:or\s+replace\s+)?trigger\s+(?:`?(\w+)`?\.)?`?(\w+)`?',
        r'create\s+definer\s*=\s*[^\s]+\s+trigger\s+(?:`?(\w+)`?\.)?`?(\w+)`?'
    ]
    
    for pattern in trigger_patterns:
        matches = re.findall(pattern, content_lower, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            trigger_name = match[1] if isinstance(match, tuple) and len(match) > 1 else match
            if trigger_name and trigger_name not in triggers:
                triggers.append(trigger_name)
    
    # Buscar índices
    index_patterns = [
        r'create\s+(?:unique\s+)?index\s+(?:`?(\w+)`?\.)?`?(\w+)`?',
        r'alter\s+table\s+\w+\s+add\s+(?:unique\s+)?index\s+`?(\w+)`?'
    ]
    
    for pattern in index_patterns:
        matches = re.findall(pattern, content_lower, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            index_name = match[1] if isinstance(match, tuple) and len(match) > 1 else match[0] if isinstance(match, tuple) else match
            if index_name and index_name not in indexes:
                indexes.append(index_name)
    
    # Buscar esquemas/bases de datos
    schema_patterns = [
        r'create\s+(?:database|schema)\s+(?:if\s+not\s+exists\s+)?`?(\w+)`?',
        r'use\s+`?(\w+)`?'
    ]
    
    for pattern in schema_patterns:
        matches = re.findall(pattern, content_lower, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            schema_name = match if isinstance(match, str) else match[0]
            if schema_name and schema_name not in schemas:
                schemas.append(schema_name)
    
    return {
        "tables": tables[:20],
        "procedures": procedures[:15], 
        "functions": functions[:15],
        "views": views[:10],
        "triggers": triggers[:10],
        "indexes": indexes[:15],
        "schemas": schemas[:5]
    }

# Función de consolidación
def consolidate_chunk_analysis(all_chunks_results, analysis_type, project_name):
    """Consolida múltiples análisis de chunks en un documento final unificado"""
    
    # Si solo hay un chunk o está vacío, devolverlo directamente SIN MODIFICACIONES
    if len(all_chunks_results) <= 1:
        result = all_chunks_results[0] if all_chunks_results else ""
        logger.info(f"Un solo chunk para {analysis_type}, devolviendo directamente: {len(result)} caracteres")
        return result
    
    # Si hay chunks vacíos, filtrarlos
    valid_chunks = [chunk for chunk in all_chunks_results if chunk and chunk.strip()]
    
    if len(valid_chunks) <= 1:
        result = valid_chunks[0] if valid_chunks else ""
        logger.info(f"Solo un chunk válido para {analysis_type}, devolviendo directamente: {len(result)} caracteres")
        return result
    
    # Solo consolidar si realmente hay múltiples chunks con contenido
    logger.info(f"Consolidando {len(valid_chunks)} chunks válidos para {analysis_type}")
    
    # Prompt específico para épicas e historias de usuario
    if "Épicas" in analysis_type or "Historias de Usuario" in analysis_type:
        consolidation_prompt = PromptTemplate(
            input_variables=["project_name", "chunks_content", "total_chunks"],
            template="""Eres un Product Owner experto en consolidación de épicas e historias de usuario para proyectos de bases de datos.

Tu tarea es consolidar múltiples secciones de épicas e historias de usuario en una estructura final unificada y bien organizada.

PROYECTO: {project_name}
SECCIONES A CONSOLIDAR: {total_chunks}

INSTRUCCIONES CRÍTICAS DE CONSOLIDACIÓN:
- JAMÁS uses "etc.", "entre otros", "y más" o términos similares
- SIEMPRE lista TODOS los elementos sin omitir información
- GENERA consolidación completa y exhaustiva
- INCLUYE todos los detalles de todas las secciones sin omitir nada

INSTRUCCIONES DE CONSOLIDACIÓN:

1. **REORGANIZAR ÉPICAS COMPLETAMENTE**: Agrupa las épicas similares de diferentes secciones bajo una sola épica principal listando TODOS los elementos
2. **RENUMERAR EXHAUSTIVAMENTE**: Asigna números consecutivos a épicas (1, 2, 3...) e historias (1.1, 1.2, 2.1, 2.2...) incluyendo TODAS las historias
3. **ELIMINAR DUPLICADOS MANTENIENDO COMPLETITUD**: Si hay historias de usuario muy similares, combínalas en una sola más completa que incluya TODOS los aspectos
4. **MANTENER ESTRUCTURA COMPLETA**: Conserva el formato de épicas con TODAS sus historias de usuario anidadas
5. **COMPLETAR ÉPICAS EXHAUSTIVAMENTE**: Si una épica está incompleta, agrégale TODAS las historias que le falten basándote en el análisis
6. **ORDEN LÓGICO COMPLETO**: Organiza las épicas en orden de importancia/dependencia para el proyecto incluyendo TODAS

SECCIONES A CONSOLIDAR:
{chunks_content}

RESULTADO ESPERADO:
Un documento unificado con épicas numeradas (1, 2, 3...) cada una con TODAS sus historias de usuario numeradas (1.1, 1.2, 2.1, 2.2...), sin duplicados y completamente organizado. TODA la información debe estar presente sin usar "etc." ni omitir detalles."""
        )
    else:
        # Prompt genérico para otros tipos de análisis
        consolidation_prompt = PromptTemplate(
            input_variables=["analysis_type", "project_name", "chunks_content", "total_chunks"],
            template="""Eres un especialista en consolidación de análisis de bases de datos. Tu tarea es unificar múltiples análisis parciales de chunks de código SQL en un documento final coherente y bien estructurado.

TIPO DE ANÁLISIS: {analysis_type}
PROYECTO: {project_name}
TOTAL DE SECCIONES ANALIZADAS: {total_chunks}

INSTRUCCIONES CRÍTICAS DE CONSOLIDACIÓN:
- JAMÁS uses "etc.", "entre otros", "y más" o términos similares
- SIEMPRE lista TODOS los elementos encontrados en todas las secciones
- GENERA consolidación completa y exhaustiva
- INCLUYE todos los detalles de todas las secciones sin omitir nada

INSTRUCCIONES DE CONSOLIDACIÓN:
1. Combina TODA la información de los {total_chunks} chunks sin duplicar contenido ni omitir detalles
2. Organiza TODA la información de manera lógica y estructurada por temas/categorías completas
3. Elimina redundancias y contradicciones, priorizando la información más completa sin omitir aspectos
4. Crea un flujo narrativo coherente que cubra COMPLETAMENTE todo el proyecto
5. Mantén el nivel técnico apropiado incluyendo TODOS los detalles técnicos encontrados
6. Si hay información conflictiva, menciona TODAS las diferencias y da recomendaciones completas
7. Asegúrate de que el documento final sea autónomo, completo y exhaustivo
8. NO agregues headers metadata adicionales, devuelve directamente el contenido consolidado COMPLETO

ANÁLISIS PARCIALES A CONSOLIDAR:
{chunks_content}

RESULTADO ESPERADO:
Genera un documento final unificado que combine TODA la información de manera coherente, eliminando redundancias y creando un análisis integral y exhaustivo del proyecto de base de datos. El documento debe incluir TODOS los detalles encontrados sin usar "etc." ni omitir información."""
        )
    
    # Preparar el contenido de todos los chunks de manera más organizada
    chunks_content = ""
    for i, chunk_result in enumerate(valid_chunks, 1):
        chunks_content += f"\n\n=== SECCIÓN {i} DE {len(valid_chunks)} ===\n"
        chunks_content += chunk_result.strip()
        chunks_content += f"\n=== FIN SECCIÓN {i} ===\n"
    
    try:
        if "Épicas" in analysis_type or "Historias de Usuario" in analysis_type:
            formatted_prompt = consolidation_prompt.format(
                project_name=project_name,
                chunks_content=chunks_content,
                total_chunks=len(valid_chunks)
            )
        else:
            formatted_prompt = consolidation_prompt.format(
                analysis_type=analysis_type,
                project_name=project_name,
                chunks_content=chunks_content,
                total_chunks=len(valid_chunks)
            )
        
        messages = [
            SystemMessage(content=f"Eres un especialista en consolidación de análisis de bases de datos, enfocado en crear documentos finales unificados, coherentes y COMPLETOS. NUNCA uses 'etc.' o términos similares. SIEMPRE incluye TODA la información disponible."),
            HumanMessage(content=formatted_prompt)
        ]
        
        response = invoke_llm_with_retry(messages, f"consolidación {analysis_type}")
        
        logger.info(f"Consolidación completada exitosamente para {analysis_type}")
        
        return response.content
        
    except Exception as e:
        logger.error(f"Error consolidando {analysis_type}: {e}")
        
        # Fallback: simplemente concatenar los chunks con separadores mínimos
        logger.warning(f"Usando fallback para {analysis_type}")
        fallback_result = ""
        
        for i, chunk_result in enumerate(valid_chunks, 1):
            if i > 1:
                fallback_result += "\n\n"
            fallback_result += chunk_result.strip()
        
        return fallback_result

# Función para generar historias de usuario con progress tracking mejorado
def generate_user_stories_with_retry(project_name, project_stats, all_code, progress_tracker=None):
    """Genera épicas y historias de usuario con tracking de progreso mejorado"""
    
    # Dividir código en chunks si es necesario
    code_chunks = split_code_into_chunks(all_code, max_chunk_size=35000)
    
    if progress_tracker:
        progress_tracker.total_chunks = len(code_chunks)
        progress_tracker.update_chunk_progress(0, "Iniciando análisis de historias de usuario")
    
    logger.info(f"Procesando épicas y historias de usuario en {len(code_chunks)} chunk(s)")
    
    # Si solo hay un chunk, procesarlo normalmente SIN consolidación
    if len(code_chunks) == 1:
        logger.info("Solo un chunk, procesando épicas y HUs directamente sin consolidación")
        
        if progress_tracker:
            progress_tracker.update_chunk_progress(1, "Generando épicas e historias de usuario")
        
        user_stories_prompt = PromptTemplate(
            input_variables=["project_name", "project_stats", "code_chunk"],
            template="""Eres un especialista en análisis de bases de datos y Product Owner experimentado en metodologías ágiles.
            Tu tarea es analizar scripts SQL, procedimientos almacenados, funciones y estructuras de bases de datos para generar una estructura completa de ÉPICAS y HISTORIAS DE USUARIO detalladas y desglosadas.

            PROYECTO DE BASE DE DATOS: {project_name}

            INSTRUCCIONES CRÍTICAS - INFORMACIÓN COMPLETA:
            - JAMÁS uses "etc.", "entre otros", "y más" o términos similares
            - SIEMPRE lista TODOS los elementos encontrados en el código
            - GENERA información completa y exhaustiva para cada sección
            - INCLUYE todos los detalles disponibles sin omitir nada

            FORMATO DE SALIDA REQUERIDO (SIN OMITIR INFORMACIÓN):

            # ÉPICA 1: [Nombre Completo de la Épica]
            **Descripción:** [Descripción completa y detallada del dominio funcional sin omitir aspectos]
            **Valor de Negocio:** [Explicación completa de por qué es importante esta épica]
            **Criterios de Aceptación de la Épica:**
            - [Criterio épico detallado 1]
            - [Criterio épico detallado 2]
            - [Todos los criterios necesarios sin usar "etc."]

            ## Historia de Usuario 1.1: [Título Específico y Completo]
            **Como** [rol específico y detallado],
            **Quiero** [funcionalidad específica, detallada y completa],
            **Para** [beneficio de negocio concreto y explicado completamente].

            **Criterios de Aceptación:**
            - [Criterio técnico específico y detallado 1]
            - [Criterio técnico específico y detallado 2]
            - [Todos los criterios necesarios listados completamente]

            **Definición de Terminado:**
            - [Requisito técnico de BD específico y completo]
            - [Pruebas requeridas detalladas]
            - [Todos los requisitos de terminado sin omitir]

            CONTEXTO DEL PROYECTO:
            {project_stats}

            CÓDIGO DE BASE DE DATOS A ANALIZAR:
            {code_chunk}

            OBJETIVO CRÍTICO: Generar entre 15-30 historias de usuario exhaustivamente detalladas, agrupadas en 5-10 épicas funcionales. TODA la información debe estar completa sin usar "etc." ni omitir detalles."""
        )
        
        try:
            formatted_prompt = user_stories_prompt.format(
                project_name=project_name,
                project_stats=project_stats,
                code_chunk=code_chunks[0]
            )
            
            messages = [
                SystemMessage(content="Eres un Product Owner experto en análisis de bases de datos y metodologías ágiles. Tu especialidad es crear épicas y historias de usuario detalladas y COMPLETAS para proyectos de bases de datos. NUNCA uses 'etc.' o términos similares. SIEMPRE proporciona información completa y exhaustiva."),
                HumanMessage(content=formatted_prompt)
            ]
            
            response = invoke_llm_with_retry(messages, f"épicas y historias de usuario")
            
            if progress_tracker:
                progress_tracker.update_chunk_progress(1, "Épicas e historias completadas")
            
            logger.info("Épicas y historias de usuario generadas exitosamente (chunk único)")
            return response.content
            
        except Exception as e:
            logger.error(f"Error generando épicas y historias de usuario (chunk único): {e}")
            return f"Error al generar épicas y historias de usuario: {str(e)}"
    
    # SOLO si hay múltiples chunks, usar la lógica de consolidación
    logger.info(f"Múltiples chunks ({len(code_chunks)}), procesando épicas y HUs con consolidación")
    
    user_stories_prompt = PromptTemplate(
        input_variables=["project_name", "project_stats", "code_chunk", "chunk_info"],
        template="""Eres un especialista en análisis de bases de datos y Product Owner experimentado en metodologías ágiles.
        Tu tarea es analizar scripts SQL, procedimientos almacenados, funciones y estructuras de bases de datos para generar ÉPICAS y HISTORIAS DE USUARIO detalladas y desglosadas para esta sección específica del proyecto.

        PROYECTO DE BASE DE DATOS: {project_name}

        {chunk_info}

        CONTEXTO DEL PROYECTO:
        {project_stats}

        CÓDIGO DE BASE DE DATOS DE ESTA SECCIÓN:
        {code_chunk}

        OBJETIVO: Generar épicas y historias de usuario exhaustivamente detalladas para esta sección específica. TODA la información debe estar completa sin usar "etc." La consolidación se hará después."""
    )
    
    all_user_stories = []
    
    # Procesar cada chunk individualmente con progreso detallado
    for i, chunk in enumerate(code_chunks):
        if progress_tracker:
            progress_tracker.update_chunk_progress(i + 1, f"Procesando épicas chunk {i+1}")
        
        chunk_info = f"NOTA: Analizando parte {i+1} de {len(code_chunks)} del código total. Enfócate en las épicas e historias de usuario específicas de esta sección. PROPORCIONA información COMPLETA sin usar 'etc.'."
        
        try:
            logger.info(f"Generando épicas y historias de usuario para chunk {i+1}/{len(code_chunks)}")
            
            formatted_prompt = user_stories_prompt.format(
                project_name=project_name,
                project_stats=project_stats,
                code_chunk=chunk,
                chunk_info=chunk_info
            )
            
            messages = [
                SystemMessage(content="Eres un Product Owner experto en análisis de bases de datos y metodologías ágiles. Enfócate en crear épicas e historias de usuario COMPLETAS y detalladas para la sección específica que estás analizando. NUNCA uses 'etc.' o términos similares."),
                HumanMessage(content=formatted_prompt)
            ]
            
            response = invoke_llm_with_retry(messages, f"épicas y historias de usuario chunk {i+1}")
            all_user_stories.append(response.content)
            
            logger.info(f"Épicas e historias de usuario generadas para chunk {i+1}/{len(code_chunks)}")
            
            # Pequeña pausa entre chunks
            if i < len(code_chunks) - 1:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error generando épicas e historias de usuario para chunk {i+1}: {e}")
            error_message = f"[ERROR] No se pudieron generar épicas e historias de usuario para la sección {i+1} del código: {str(e)}"
            all_user_stories.append(error_message)
    
    # Consolidación final con progreso detallado
    if len(all_user_stories) > 1:
        if progress_tracker:
            progress_tracker.update_chunk_progress(len(code_chunks), "Consolidando épicas finales")
            # Simular progreso dentro de la consolidación
            progress_tracker.set_consolidation_progress("epicas", 25)
            time.sleep(0.5)
            progress_tracker.set_consolidation_progress("epicas", 50)
            time.sleep(0.5)
            progress_tracker.set_consolidation_progress("epicas", 75)
            time.sleep(0.5)
            progress_tracker.set_consolidation_progress("epicas", 100)
        
        logger.info("Iniciando consolidación de épicas e historias de usuario de múltiples chunks...")
        try:
            consolidated = consolidate_chunk_analysis(all_user_stories, "Épicas e Historias de Usuario", project_name)
            logger.info("Consolidación de épicas e historias de usuario completada exitosamente")
            return consolidated
        except Exception as e:
            logger.error(f"Error en consolidación de épicas e historias de usuario: {e}")
            return "\n\n".join(all_user_stories)
    else:
        return all_user_stories[0] if all_user_stories else ""

# Función para generar análisis DEF con progress tracking mejorado
def generate_def_analysis_with_retry(project_name, project_stats, all_code, progress_tracker=None):
    """Genera análisis DEF con tracking de progreso mejorado"""
    
    # Dividir código en chunks si es necesario
    code_chunks = split_code_into_chunks(all_code, max_chunk_size=35000)
    
    if progress_tracker:
        progress_tracker.update_chunk_progress(0, "Iniciando análisis DEF")
    
    logger.info(f"Procesando análisis DEF en {len(code_chunks)} chunk(s)")
    
    # Si solo hay un chunk, procesarlo normalmente
    if len(code_chunks) == 1:
        if progress_tracker:
            progress_tracker.update_chunk_progress(1, "Generando análisis DEF")
        
        def_analysis_prompt = PromptTemplate(
            input_variables=["project_name", "project_stats", "code_chunk"],
            template="""Eres un especialista en análisis de bases de datos y arquitecto de software experimentado.
            Tu tarea es analizar scripts SQL, procedimientos almacenados, funciones y estructuras de bases de datos para generar un análisis DEF (Definición de Requerimientos Funcionales) completo y detallado.

            PROYECTO DE BASE DE DATOS: {project_name}

            ESTRUCTURA DEL ANÁLISIS DEF (SIN OMITIR INFORMACIÓN):

            # ANÁLISIS DEF - {project_name}

            ## 1. RESUMEN EJECUTIVO
            [Descripción completa y detallada del sistema de base de datos y su propósito]

            ## 2. ANÁLISIS DE DOMINIO
            ### 2.1 Entidades Principales
            [Lista exhaustiva de TODAS las entidades/tablas principales]

            ### 2.2 Relaciones y Dependencias
            [Mapa completo de TODAS las relaciones entre entidades]

            ### 2.3 Procesos de Negocio Identificados
            [Lista completa de TODOS los procesos que soporta la base de datos]

            ## 3. REQUERIMIENTOS FUNCIONALES
            [TODAS las funcionalidades identificadas]

            ## 4. ESPECIFICACIONES TÉCNICAS
            [TODOS los detalles técnicos encontrados]

            ## 5. CASOS DE USO
            [TODOS los escenarios de uso identificados]

            ## 6. RESTRICCIONES Y VALIDACIONES
            [TODAS las reglas de negocio encontradas]

            ## 7. REQUERIMIENTOS NO FUNCIONALES
            [TODOS los aspectos de rendimiento, seguridad, disponibilidad]

            ## 8. RECOMENDACIONES
            [TODAS las mejoras y optimizaciones sugeridas]

            CONTEXTO DEL PROYECTO:
            {project_stats}

            CÓDIGO DE BASE DE DATOS A ANALIZAR:
            {code_chunk}"""
        )
        
        try:
            formatted_prompt = def_analysis_prompt.format(
                project_name=project_name,
                project_stats=project_stats,
                code_chunk=code_chunks[0]
            )
            
            messages = [
                SystemMessage(content="Eres un especialista en análisis de bases de datos y arquitecto de software. Tu especialidad es crear análisis DEF exhaustivamente detallados y completos para sistemas de bases de datos. NUNCA uses 'etc.' o términos similares."),
                HumanMessage(content=formatted_prompt)
            ]
            
            response = invoke_llm_with_retry(messages, f"análisis DEF")
            
            if progress_tracker:
                progress_tracker.update_chunk_progress(1, "Análisis DEF completado")
            
            logger.info("Análisis DEF generado exitosamente (chunk único)")
            return response.content
            
        except Exception as e:
            logger.error(f"Error generando análisis DEF (chunk único): {e}")
            return f"Error al generar análisis DEF: {str(e)}"
    
    # Múltiples chunks con progreso detallado
    def_analysis_prompt = PromptTemplate(
        input_variables=["project_name", "project_stats", "code_chunk", "chunk_info"],
        template="""Eres un especialista en análisis de bases de datos y arquitecto de software experimentado.
        Tu tarea es analizar scripts SQL, procedimientos almacenados, funciones y estructuras de bases de datos para generar un análisis DEF (Definición de Requerimientos Funcionales) para esta sección específica del proyecto.

        PROYECTO DE BASE DE DATOS: {project_name}

        {chunk_info}

        CONTEXTO DEL PROYECTO:
        {project_stats}

        CÓDIGO DE BASE DE DATOS DE ESTA SECCIÓN:
        {code_chunk}"""
    )
    
    all_def_analyses = []
    
    # Procesar cada chunk individualmente
    for i, chunk in enumerate(code_chunks):
        if progress_tracker:
            progress_tracker.update_chunk_progress(i + 1, f"Procesando DEF chunk {i+1}")
        
        chunk_info = f"NOTA: Analizando parte {i+1} de {len(code_chunks)} del código total. Enfócate en el análisis DEF específico de esta sección."
        
        try:
            logger.info(f"Generando análisis DEF para chunk {i+1}/{len(code_chunks)}")
            
            formatted_prompt = def_analysis_prompt.format(
                project_name=project_name,
                project_stats=project_stats,
                code_chunk=chunk,
                chunk_info=chunk_info
            )
            
            messages = [
                SystemMessage(content="Eres un especialista en análisis de bases de datos y arquitecto de software. Enfócate en crear análisis DEF exhaustivamente detallados para la sección específica que estás analizando."),
                HumanMessage(content=formatted_prompt)
            ]
            
            response = invoke_llm_with_retry(messages, f"análisis DEF chunk {i+1}")
            all_def_analyses.append(response.content)
            
            logger.info(f"Análisis DEF generado para chunk {i+1}/{len(code_chunks)}")
            
            time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error generando análisis DEF para chunk {i+1}: {e}")
            error_message = f"[ERROR] No se pudo generar análisis DEF para la sección {i+1} del código: {str(e)}"
            all_def_analyses.append(error_message)
    
    # Consolidación final con progreso detallado
    if len(all_def_analyses) > 1:
        if progress_tracker:
            progress_tracker.update_chunk_progress(len(code_chunks), "Consolidando análisis DEF")
            # Simular progreso dentro de la consolidación DEF
            progress_tracker.set_consolidation_progress("def", 20)
            time.sleep(0.5)
            progress_tracker.set_consolidation_progress("def", 40)
            time.sleep(0.5)
            progress_tracker.set_consolidation_progress("def", 70)
            time.sleep(0.5)
            progress_tracker.set_consolidation_progress("def", 100)
        
        logger.info("Iniciando consolidación de análisis DEF de múltiples chunks...")
        try:
            consolidated = consolidate_chunk_analysis(all_def_analyses, "Análisis DEF", project_name)
            logger.info("Consolidación de análisis DEF completada exitosamente")
            return consolidated
        except Exception as e:
            logger.error(f"Error en consolidación de análisis DEF: {e}")
            return "\n\n".join(all_def_analyses)
    else:
        return all_def_analyses[0] if all_def_analyses else ""

# Endpoint principal con progress tracking mejorado
@analizarCodigoSQL_bp.route('/analizarCodigoSQL/zip', methods=['POST'])
def analyze_zip_file():
    # Generar session_id único para tracking
    session_id = str(uuid.uuid4())
    
    if 'zip_file' not in request.files:
        return jsonify({"error": "No se envió archivo ZIP"}), 400
    
    zip_file = request.files['zip_file']
    project_name = request.form.get('project_name', 'Proyecto de Base de Datos desde ZIP')
    
    if zip_file.filename == '' or not zip_file.filename.lower().endswith('.zip'):
        return jsonify({"error": "Debe ser un archivo ZIP válido"}), 400
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        logger.info(f"Iniciando análisis de proyecto de base de datos: {project_name}")
        
        # Crear tracker de progreso
        progress_tracker = ProgressTracker(session_id)
        progress_tracker.update_chunk_progress(0, "Extrayendo archivos")
        
        # Guardar archivo ZIP
        zip_path = os.path.join(temp_dir, 'project.zip')
        zip_file.save(zip_path)
        
        # Extraer ZIP
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Buscar archivos de base de datos
        uploaded_files = []
        total_size = 0
        
        progress_tracker.update_chunk_progress(0, "Procesando archivos de base de datos")
        
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                
                if ext.lower() in ALLOWED_EXTENSIONS:
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size <= MAX_FILE_SIZE:
                            rel_path = os.path.relpath(file_path, extract_dir)
                            uploaded_files.append({
                                'original_name': rel_path,
                                'temp_path': file_path,
                                'size': file_size
                            })
                            total_size += file_size
                            
                            if len(uploaded_files) >= MAX_FILES:
                                break
                    except Exception as e:
                        logger.error(f"Error procesando archivo {file}: {e}")
                        continue
            
            if len(uploaded_files) >= MAX_FILES:
                break
        
        if not uploaded_files:
            return jsonify({"error": "No se encontraron archivos de base de datos válidos en el ZIP"}), 400
        
        logger.info(f"Procesando {len(uploaded_files)} archivos de base de datos extraídos del ZIP")
        
        # Analizar archivos extraídos
        project_stats = {
            "total_files": len(uploaded_files),
            "analyzed_files": len(uploaded_files),
            "extensions": {},
            "total_lines": 0,
            "sql_files": 0,
            "ddl_files": 0,
            "procedure_files": 0,
            "total_tables": 0,
            "total_procedures": 0,
            "total_functions": 0,
            "total_views": 0,
            "total_triggers": 0,
            "total_indexes": 0,
            "database_engines": [],
            "schemas_found": []
        }
        
        all_code = ""
        analyzed_files = []
        
        for file_info in uploaded_files:
            try:
                with open(file_info['temp_path'], 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.count('\n') + 1
                    
                    # Analizar código de base de datos
                    analysis = analyze_database_code(content)
                    
                    # Obtener extensión
                    _, ext = os.path.splitext(file_info['original_name'])
                    ext = ext.lower()
                    
                    # Estadísticas por extensión
                    if ext in project_stats["extensions"]:
                        project_stats["extensions"][ext] += 1
                    else:
                        project_stats["extensions"][ext] = 1
                    
                    # Clasificar archivos de base de datos
                    if ext in ['.sql', '.pgsql', '.psql', '.mysql']:
                        project_stats["sql_files"] += 1
                    elif ext in ['.ddl', '.schema']:
                        project_stats["ddl_files"] += 1
                    elif ext in ['.proc', '.sp']:
                        project_stats["procedure_files"] += 1
                    
                    # Detectar motor de base de datos por contenido
                    content_lower = content.lower()
                    if 'mysql' in content_lower or 'auto_increment' in content_lower:
                        if 'MySQL' not in project_stats["database_engines"]:
                            project_stats["database_engines"].append('MySQL')
                    if 'postgresql' in content_lower or 'serial' in content_lower or 'bigserial' in content_lower:
                        if 'PostgreSQL' not in project_stats["database_engines"]:
                            project_stats["database_engines"].append('PostgreSQL')
                    if 'sql server' in content_lower or 'identity' in content_lower:
                        if 'SQL Server' not in project_stats["database_engines"]:
                            project_stats["database_engines"].append('SQL Server')
                    if 'oracle' in content_lower or 'number(' in content_lower:
                        if 'Oracle' not in project_stats["database_engines"]:
                            project_stats["database_engines"].append('Oracle')
                    
                    # Agregar a archivos analizados
                    analyzed_files.append({
                        "name": os.path.basename(file_info['original_name']),
                        "path": file_info['original_name'],
                        "extension": ext,
                        "size": file_info['size'],
                        "lines": lines,
                        "tables_count": len(analysis["tables"]),
                        "procedures_count": len(analysis["procedures"]),
                        "functions_count": len(analysis["functions"]),
                        "views_count": len(analysis["views"]),
                        "triggers_count": len(analysis["triggers"]),
                        "indexes_count": len(analysis["indexes"])
                    })
                    
                    # Acumular estadísticas
                    project_stats["total_lines"] += lines
                    project_stats["total_tables"] += len(analysis["tables"])
                    project_stats["total_procedures"] += len(analysis["procedures"])
                    project_stats["total_functions"] += len(analysis["functions"])
                    project_stats["total_views"] += len(analysis["views"])
                    project_stats["total_triggers"] += len(analysis["triggers"])
                    project_stats["total_indexes"] += len(analysis["indexes"])
                    project_stats["schemas_found"].extend(analysis["schemas"])
                    
                    # Agregar al código completo
                    all_code += f"\n\n--- Archivo: {file_info['original_name']} ({lines} líneas) ---\n"
                    all_code += f"Tablas encontradas: {len(analysis['tables'])}\n"
                    all_code += f"Procedimientos encontrados: {len(analysis['procedures'])}\n"
                    all_code += f"Funciones encontradas: {len(analysis['functions'])}\n"
                    all_code += f"Vistas encontradas: {len(analysis['views'])}\n"
                    all_code += f"Triggers encontrados: {len(analysis['triggers'])}\n"
                    all_code += f"Índices encontrados: {len(analysis['indexes'])}\n\n"
                    all_code += content
                    
            except Exception as e:
                logger.error(f"Error al leer archivo {file_info['original_name']}: {e}")
        
        # Preparar datos para los prompts
        stats_text = f"""- Total de archivos: {project_stats["total_files"]}
- Archivos analizados: {project_stats["analyzed_files"]}
- Total de líneas de código: {project_stats["total_lines"]}
- Archivos SQL: {project_stats["sql_files"]}
- Archivos DDL: {project_stats["ddl_files"]}
- Archivos de procedimientos: {project_stats["procedure_files"]}
- Total de tablas encontradas: {project_stats["total_tables"]}
- Total de procedimientos encontrados: {project_stats["total_procedures"]}
- Total de funciones encontradas: {project_stats["total_functions"]}
- Total de vistas encontradas: {project_stats["total_views"]}
- Total de triggers encontrados: {project_stats["total_triggers"]}
- Total de índices encontrados: {project_stats["total_indexes"]}
- Motores de BD detectados: {project_stats["database_engines"]}
- Esquemas encontrados: {list(set(project_stats["schemas_found"]))[:5]}"""
        
        # Actualizar progreso antes de iniciar análisis
        progress_tracker.update_chunk_progress(0, "Archivos procesados, iniciando análisis")
        
        # Generar análisis con progress tracking mejorado
        logger.info("Generando historias de usuario con tracking de progreso...")
        user_stories = generate_user_stories_with_retry(project_name, stats_text, all_code, progress_tracker)
        
        logger.info("Generando análisis DEF con tracking de progreso...")
        def_analysis = generate_def_analysis_with_retry(project_name, stats_text, all_code, progress_tracker)
        
        # Progreso final - IMPORTANTE: Marcar como completado
        progress_tracker.complete_analysis()
        
        # Generar timestamp para referencia
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Construir árbol de archivos desde los archivos extraídos
        def build_tree_from_files(files):
            tree = {
                "name": project_name,
                "type": "folder",
                "children": []
            }
            
            for file_info in files:
                file_path = file_info.get('path', file_info.get('name', ''))
                if not file_path:
                    continue
                    
                path_parts = file_path.replace('\\', '/').split('/')
                current_node = tree
                
                for i, part in enumerate(path_parts[:-1]):
                    if not part:
                        continue
                        
                    folder = next((child for child in current_node["children"] 
                                 if child["name"] == part and child["type"] == "folder"), None)
                    
                    if not folder:
                        folder = {
                            "name": part,
                            "type": "folder",
                            "children": []
                        }
                        current_node["children"].append(folder)
                    
                    current_node = folder
                
                filename = path_parts[-1] if path_parts else file_info.get('name', 'unknown')
                _, ext = os.path.splitext(filename)
                current_node["children"].append({
                    "name": filename,
                    "type": "file",
                    "extension": ext.lower(),
                    "path": file_path
                })
            
            return tree
        
        directory_tree = build_tree_from_files(analyzed_files)
        
        logger.info(f"Análisis completado exitosamente para proyecto de base de datos: {project_name}")
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "timestamp": timestamp,
            "user_stories": user_stories,
            "def_analysis": def_analysis,
            "analyzed_files": analyzed_files,
            "directory_tree": directory_tree,
            "project_stats": project_stats,
            "documentation_found": False,
            "analyzed_documents": [],
            "code_analysis": {
                "language": "SQL/Database",
                "total_tables": project_stats["total_tables"],
                "total_procedures": project_stats["total_procedures"],
                "total_functions": project_stats["total_functions"],
                "total_views": project_stats["total_views"],
                "total_triggers": project_stats["total_triggers"],
                "total_indexes": project_stats["total_indexes"],
                "database_engines": project_stats["database_engines"],
                "schemas_found": list(set(project_stats["schemas_found"]))[:5]
            },
            "summary": {
                "files_analyzed": len(analyzed_files),
                "total_lines_analyzed": project_stats["total_lines"],
                "documentation_files_found": 0,
                "analysis_completed": True,
                "upload_method": "zip_upload",
                "consolidation_applied": True,
                "retry_info": {
                    "total_retries_used": rate_limit_handler.retry_count,
                    "rate_limiting_encountered": rate_limit_handler.retry_count > 0
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error al analizar ZIP de base de datos: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": f"Error procesando ZIP de base de datos: {str(e)}",
            "success": False,
            "session_id": session_id,
            "retry_info": {
                "retries_attempted": rate_limit_handler.retry_count,
                "rate_limiting_encountered": rate_limit_handler.retry_count > 0
            }
        }), 500
    
    finally:
        # Limpiar tracker de progreso
        if session_id in analysis_progress:
            del analysis_progress[session_id]
        
        try:
            shutil.rmtree(temp_dir)
        except Exception as cleanup_error:
            logger.error(f"Error al limpiar archivos temporales: {cleanup_error}")

# Endpoint para obtener estado del servicio
@analizarCodigoSQL_bp.route('/analizarCodigoSQL/status', methods=['GET'])
def get_analysis_status():
    """Endpoint para verificar el estado del servicio"""
    return jsonify({
        "status": "running",
        "service_type": "database_analyzer",
        "features": [
            "chunk_processing",
            "rate_limiting",
            "document_consolidation",
            "multi_database_support",
            "websocket_progress_tracking"
        ],
        "supported_extensions": list(ALLOWED_EXTENSIONS),
        "supported_databases": ["MySQL", "PostgreSQL", "SQL Server", "Oracle", "SQLite"],
        "websocket_enabled": socketio is not None,
        "timestamp": datetime.datetime.now().isoformat()
    })

# Endpoint para consolidación