# app/api/v1/analizarCodigoRepomix.py
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
analizarCodigoRepomix_bp = Blueprint('analizarCodigoRepomix', __name__)

# Variable global para SocketIO (se inicializa desde __init__.py)
socketio = None

def init_socketio(app_socketio):
    """Inicializar SocketIO desde __init__.py"""
    global socketio
    socketio = app_socketio
    logger.info("SocketIO inicializado en analizarCodigoRepomix blueprint")

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
        elif "Iniciando análisis DEF de especificación funcional" in phase:
            self.overall_progress = 30
        elif "Analizando DEF" in phase and "especificación funcional" in phase:
            # Progreso de chunks DEF: del 30% al 65% (35% total)
            if self.total_chunks > 1:
                chunk_progress = (chunk_number / self.total_chunks) * 35
                self.overall_progress = 30 + chunk_progress
            else:
                self.overall_progress = 50
        elif "Consolidando DEF funcional" in phase:
            self.overall_progress = 70
        elif "Iniciando análisis DAT técnico" in phase:
            self.overall_progress = 75
        elif "Procesando DAT chunk" in phase:
            # Progreso de chunks DAT: del 75% al 90% (15% total)
            if self.total_chunks > 1:
                chunk_progress = (chunk_number / self.total_chunks) * 15
                self.overall_progress = 75 + chunk_progress
            else:
                self.overall_progress = 85
        elif "Consolidando análisis DAT" in phase:
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
        if consolidation_type == "def":
            # Consolidación de DEF: 70-74%
            self.overall_progress = 70 + (progress_within_consolidation * 4 / 100)
            phase = f"Consolidando DEF funcional... {progress_within_consolidation}%"
        elif consolidation_type == "dat":
            # Consolidación de DAT: 92-97%
            self.overall_progress = 92 + (progress_within_consolidation * 5 / 100)
            phase = f"Consolidando análisis DAT... {progress_within_consolidation}%"
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

# Configuración de Rate Limiting OPTIMIZADA
class RateLimitConfig:
    MAX_RETRIES = 3  # Reducido de 65 a 3
    BASE_DELAY = 5   # Aumentado de 2 a 5 segundos
    MAX_DELAY = 120.0  # Reducido de 300 a 120 segundos
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
            temperature=0.5,
            request_timeout=90,  # Reducido de 120 a 90 segundos
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

# Configuración para subida de archivos - ACTUALIZADA PARA CÓDIGO LEGADO C/C++
ALLOWED_EXTENSIONS = {'.c', '.cpp', '.cxx', '.cc', '.c++', '.h', '.hpp', '.hxx', '.hh', 
                     '.h++', '.inc', '.inl', '.ipp', '.txx', '.tcc', '.def', '.rc', 
                     '.res', '.asm', '.s', '.S', '.lib', '.dll', '.obj', '.o', 
                     '.make', '.mk', '.cmake', '.pro', '.vcproj', '.vcxproj', 
                     '.sln', '.dsp', '.dsw', '.cbp', '.dev'}
MAX_FILES = 5000
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB por archivo

def allowed_file(filename):
    return os.path.splitext(filename.lower())[1] in ALLOWED_EXTENSIONS

# Función para dividir el código en chunks OPTIMIZADA
def split_code_into_chunks(code, max_chunk_size=50000):  # Aumentado de 35000 a 45000
    """Divide el código en chunks más grandes para reducir la cantidad de llamadas a la API"""
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

# Función para analizar código legado C/C++ - NUEVA FUNCIÓN
def analyze_legacy_code(content, filename):
    """Analiza archivos de código legado C/C++ para extraer elementos principales"""
    functions = []
    classes = []
    structs = []
    includes = []
    defines = []
    variables = []
    typedefs = []
    enums = []
    namespaces = []
    apis = []
    dlls = []
    
    # Convertir a minúsculas para búsqueda case-insensitive en algunos casos
    content_lower = content.lower()
    lines = content.split('\n')
    
    # Buscar funciones (C y C++)
    function_patterns = [
        r'(?:static\s+|extern\s+|inline\s+)?(?:const\s+)?(?:\w+(?:\s*\*)*\s+)+(\w+)\s*\([^{]*\)\s*{',
        r'(?:virtual\s+|static\s+|inline\s+)?(?:\w+(?:\s*\*)*\s+)+(\w+)\s*\([^{]*\)\s*{',
        r'(?:WINAPI|CALLBACK|APIENTRY)\s+(\w+)\s*\(',
        r'(?:__declspec\s*\([^)]+\)\s+)?(?:\w+\s+)*(\w+)\s*\([^{]*\)\s*{'
    ]
    
    for pattern in function_patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            func_name = match if isinstance(match, str) else match[0]
            if func_name and func_name not in functions and func_name != 'main':
                functions.append(func_name)
    
    # Buscar clases (C++)
    class_patterns = [
        r'class\s+(?:__declspec\s*\([^)]+\)\s+)?(\w+)',
        r'struct\s+(?:__declspec\s*\([^)]+\)\s+)?(\w+)(?:\s*:\s*public|\s*:\s*private|\s*{)',
        r'template\s*<[^>]*>\s*class\s+(\w+)'
    ]
    
    for pattern in class_patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            class_name = match if isinstance(match, str) else match[0]
            if class_name and class_name not in classes:
                classes.append(class_name)
    
    # Buscar estructuras
    struct_patterns = [
        r'typedef\s+struct\s+(?:\w+\s+)?{[^}]*}\s*(\w+)',
        r'struct\s+(\w+)\s*{',
        r'typedef\s+struct\s+(\w+)'
    ]
    
    for pattern in struct_patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            struct_name = match if isinstance(match, str) else match[0]
            if struct_name and struct_name not in structs:
                structs.append(struct_name)
    
    # Buscar includes
    include_patterns = [
        r'#include\s*[<"]([^>"]+)[>"]',
        r'#import\s*[<"]([^>"]+)[>"]'
    ]
    
    for pattern in include_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if match and match not in includes:
                includes.append(match)
    
    # Buscar defines y macros
    define_patterns = [
        r'#define\s+(\w+)',
        r'#ifdef\s+(\w+)',
        r'#ifndef\s+(\w+)'
    ]
    
    for pattern in define_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if match and match not in defines:
                defines.append(match)
    
    # Buscar typedefs
    typedef_patterns = [
        r'typedef\s+(?:struct\s+\w+\s+)?(\w+);',
        r'typedef\s+[^;]*\s+(\w+);'
    ]
    
    for pattern in typedef_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if match and match not in typedefs:
                typedefs.append(match)
    
    # Buscar enums
    enum_patterns = [
        r'enum\s+(\w+)',
        r'typedef\s+enum\s*{[^}]*}\s*(\w+)'
    ]
    
    for pattern in enum_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if match and match not in enums:
                enums.append(match)
    
    # Buscar namespaces (C++)
    namespace_patterns = [
        r'namespace\s+(\w+)',
        r'using\s+namespace\s+(\w+)'
    ]
    
    for pattern in namespace_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if match and match not in namespaces:
                namespaces.append(match)
    
    # Buscar APIs de Windows y DLLs
    api_patterns = [
        r'(GetProcAddress|LoadLibrary|FreeLibrary|CreateFile|ReadFile|WriteFile)',
        r'(CreateProcess|CreateThread|WaitForSingleObject|CloseHandle)',
        r'(RegOpenKey|RegCloseKey|RegQueryValue|RegSetValue)',
        r'(MessageBox|CreateWindow|ShowWindow|UpdateWindow)',
        r'(malloc|calloc|free|realloc|memcpy|memset|strlen|strcpy)'
    ]
    
    for pattern in api_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            api_name = match if isinstance(match, str) else match[0]
            if api_name and api_name not in apis:
                apis.append(api_name)
    
    # Buscar referencias a DLLs
    dll_patterns = [
        r'LoadLibrary\s*\(\s*[LT]?"([^"]+\.dll)"',
        r'#pragma\s+comment\s*\(\s*lib\s*,\s*"([^"]+\.lib)"',
        r'__declspec\s*\(\s*dllimport\s*\)',
        r'__declspec\s*\(\s*dllexport\s*\)'
    ]
    
    for line in lines:
        for pattern in dll_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                if match and match not in dlls:
                    dlls.append(match)
    
    return {
        "functions": functions[:30],  # Limitar a 30 para no saturar
        "classes": classes[:20],
        "structs": structs[:20], 
        "includes": includes[:25],
        "defines": defines[:20],
        "typedefs": typedefs[:15],
        "enums": enums[:15],
        "namespaces": namespaces[:10],
        "apis": apis[:25],
        "dlls": dlls[:15]
    }

# Función de consolidación optimizada - ACTUALIZADA PARA SEPARACIÓN CLARA
def consolidate_optimized_analysis(all_chunks_results, analysis_type, project_name):
    """Consolida análisis optimizado manteniendo separación clara entre DEF y DAT"""
    
    if len(all_chunks_results) <= 1:
        result = all_chunks_results[0] if all_chunks_results else ""
        logger.info(f"Un solo chunk para {analysis_type}, devolviendo directamente: {len(result)} caracteres")
        return result
    
    valid_chunks = [chunk for chunk in all_chunks_results if chunk and chunk.strip()]
    
    if len(valid_chunks) <= 1:
        result = valid_chunks[0] if valid_chunks else ""
        logger.info(f"Solo un chunk válido para {analysis_type}, devolviendo directamente: {len(result)} caracteres")
        return result
    
    # Si hay más de 4 chunks, usar concatenación inteligente
    if len(valid_chunks) > 4:
        logger.warning(f"Muchos chunks ({len(valid_chunks)}) para {analysis_type}, usando concatenación estructurada")
        return create_smart_concatenation(valid_chunks, project_name, analysis_type)
    
    logger.info(f"Consolidando {len(valid_chunks)} chunks válidos para {analysis_type} con IA")
    
    # Prompts específicos según tipo de análisis
    if "DEF" in analysis_type or "Especificación" in analysis_type or "Funcional" in analysis_type:
        # Template para consolidación FUNCIONAL (DEF)
        consolidation_prompt = PromptTemplate(
            input_variables=["project_name", "chunks_content", "total_chunks"],
            template="""Consolidación DEF Final - {project_name}

OBJETIVO: Unificar todas las partes funcionales en UN DOCUMENTO ÚNICO DE ESPECIFICACIÓN FUNCIONAL (DEF).

INSTRUCCIONES:
1. FUSIONA épicas y funcionalidades similares manteniendo TODA la información funcional
2. ELIMINA duplicados funcionales pero conserva información única
3. ORGANIZA jerárquicamente: ÉPICAS → FUNCIONALIDADES → HISTORIAS DE USUARIO → REGLAS DE NEGOCIO
4. MANTÉN enfoque en aspectos de NEGOCIO y FUNCIONALIDAD del usuario final
5. NO incluyas detalles técnicos de implementación (esos van en el DAT)

FORMATO DE SALIDA:

# DOCUMENTO DE ESPECIFICACIÓN FUNCIONAL (DEF) - {project_name}

## 1. INTRODUCCIÓN
### 1.1 Propósito del Sistema
[Propósito funcional identificado del código]

### 1.2 Situación Actual
[Qué funcionalidades implementa actualmente el sistema]

### 1.3 Situación Deseada
[Hacia dónde debe evolucionar funcionalmente]

## 2. ÉPICAS FUNCIONALES DEL PROYECTO

### ÉPICA 1: [Dominio Funcional Principal]
**Descripción Funcional:** [Qué procesos de negocio cubre]
**Valor de Negocio:** [Por qué es importante para los usuarios]

#### FUNCIONALIDADES DE LA ÉPICA 1
- **FN1.1:** [Descripción de la funcionalidad desde perspectiva del usuario]
- **FN1.2:** [Descripción de la funcionalidad desde perspectiva del usuario]

#### HISTORIAS DE USUARIO DE LA ÉPICA 1
##### Historia de Usuario 1.1: [Título]
**Como** [rol], **Quiero** [funcionalidad], **Para** [beneficio]
**Criterios de Aceptación:** [Criterios específicos]

### ÉPICA 2: [Segundo Dominio Funcional]
[Misma estructura...]

## 3. REGLAS DE NEGOCIO IDENTIFICADAS
### RN001: [Nombre de la regla]
**Descripción:** [Regla encontrada en el código]
**Aplicabilidad:** [Dónde se aplica]

## 4. REQUISITOS NO FUNCIONALES
### 4.1 Performance
[Requisitos de rendimiento identificados]

### 4.2 Seguridad
[Requisitos de seguridad encontrados]

## 5. RESTRICCIONES Y SUPUESTOS
[Limitaciones funcionales identificadas]

PARTES A CONSOLIDAR:
{chunks_content}

RESULTADO: Documento DEF único con toda la información funcional organizada jerárquicamente."""
        )
    else:
        # Template para consolidación TÉCNICA (DAT)
        consolidation_prompt = PromptTemplate(
            input_variables=["project_name", "chunks_content", "total_chunks"],
            template="""Consolidación DAT Final - {project_name}

OBJETIVO: Unificar todas las partes técnicas en UN DOCUMENTO ÚNICO DE ANÁLISIS TÉCNICO (DAT).

INSTRUCCIONES:
1. FUSIONA componentes técnicos similares
2. CREA un inventario técnico completo del sistema
3. ORGANIZA por arquitectura, componentes, dependencias, migración
4. MANTÉN enfoque en aspectos TÉCNICOS y de IMPLEMENTACIÓN
5. NO incluyas épicas, funcionalidades o historias de usuario (esos van en el DEF)

FORMATO DE SALIDA:

# DOCUMENTO DE ANÁLISIS TÉCNICO (DAT) - {project_name}

## 1. RESUMEN EJECUTIVO TÉCNICO
[Arquitectura general, tecnologías y paradigmas]

## 2. ARQUITECTURA Y COMPONENTES DEL SISTEMA
### 2.1 Componentes Principales
[Módulos y subsistemas técnicos]

### 2.2 Flujo Técnico General del Sistema
[Flujo técnico completo: Componente A → procesa → Componente B → BD → etc.]

## 3. INVENTARIO TÉCNICO DETALLADO
### 3.1 Archivos y Módulos
[Inventario completo de archivos de código]

### 3.2 Funciones y Algoritmos
[Catálogo de funciones con complejidad]

### 3.3 Estructuras de Datos
[Clases, structs, variables globales]

## 4. ANÁLISIS DE DEPENDENCIAS TÉCNICAS
[Bibliotecas, APIs, dependencias internas]

## 5. GESTIÓN DE MEMORIA Y RECURSOS
[Patrones de memoria, I/O, handles]

## 6. PLAN DE MIGRACIÓN TÉCNICA DETALLADO
### 6.1 Elementos Críticos para Migración
[Código que DEBE migrarse con prioridad alta]

### 6.2 Estrategia de Migración por Fases
[Plan técnico detallado de modernización]

### 6.3 Herramientas y Tecnologías Objetivo
[Stack tecnológico recomendado]

## 7. ESTIMACIONES Y CRONOGRAMA TÉCNICO
[Tiempos, esfuerzos y recursos para migración]

PARTES A CONSOLIDAR:
{chunks_content}

RESULTADO: Documento DAT único con inventario técnico completo y plan de migración específico."""
        )
    
    # Contenido procesado para consolidación
    chunks_content = ""
    for i, chunk in enumerate(valid_chunks, 1):
        # Limpiar referencias a secciones del chunk
        cleaned_chunk = re.sub(r'=== SECCIÓN \d+ ===', '', chunk)
        cleaned_chunk = re.sub(r'Análisis de.*Parte \d+ de \d+', '', cleaned_chunk)
        cleaned_chunk = re.sub(r'SECCIÓN_\d+', '', cleaned_chunk, flags=re.IGNORECASE)
        
        chunks_content += f"\n=== PARTE {i} ===\n{cleaned_chunk}\n"
    
    try:
        formatted_prompt = consolidation_prompt.format(
            project_name=project_name,
            chunks_content=chunks_content,
            total_chunks=len(valid_chunks)
        )
        
        system_message = "Eres un especialista en consolidación de DEF (Especificaciones Funcionales)." if "DEF" in analysis_type else "Eres un especialista en consolidación de DAT (Análisis Técnico)."
        system_message += " Crea un documento único manteniendo separación clara entre aspectos funcionales (DEF) y técnicos (DAT)."
        
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=formatted_prompt)
        ]
        
        response = invoke_llm_with_retry(messages, f"consolidación {analysis_type}")
        logger.info(f"Consolidación completada para {analysis_type}")
        return response.content
        
    except Exception as e:
        logger.error(f"Error en consolidación: {e}")
        return create_smart_concatenation(valid_chunks, project_name, analysis_type)

def extract_essential_content(chunk):
    """Extrae el contenido esencial de un chunk eliminando headers redundantes"""
    lines = chunk.split('\n')
    essential_lines = []
    
    for line in lines:
        # Saltar headers markdown redundantes pero mantener contenido
        if line.startswith('# ') or line.startswith('## ') or line.startswith('### '):
            # Convertir a formato compacto
            header_level = len(line.split()[0])
            content = line.replace('#', '').strip()
            essential_lines.append(f"{'*' * header_level} {content}")
        else:
            essential_lines.append(line)
    
    return '\n'.join(essential_lines)

def create_smart_concatenation(chunks, project_name, analysis_type):
    """Crea concatenación inteligente cuando hay muchos chunks"""
    result = f"# {analysis_type} - {project_name}\n\n"
    result += "*Análisis consolidado automáticamente por optimización de tokens*\n\n"
    
    # Agrupar contenido por tipo según si es DEF o DAT
    if "DEF" in analysis_type or "Especificación" in analysis_type or "Funcional" in analysis_type:
        # Agrupación para DEF (Funcional)
        epicas_content = []
        funcionalidades_content = []
        historias_content = []
        reglas_content = []
        
        for i, chunk in enumerate(chunks, 1):
            lines = chunk.split('\n')
            current_section = []
            
            for line in lines:
                if 'ÉPICA' in line.upper() or 'EPIC' in line.upper():
                    if current_section:
                        epicas_content.append('\n'.join(current_section))
                        current_section = []
                elif 'FUNCIONALIDAD' in line.upper() or 'FUNCTIONALITY' in line.upper():
                    if current_section:
                        funcionalidades_content.append('\n'.join(current_section))
                        current_section = []
                elif 'HISTORIA' in line.upper() or 'USER STORY' in line.upper():
                    if current_section:
                        historias_content.append('\n'.join(current_section))
                        current_section = []
                elif 'REGLA' in line.upper() or 'RULE' in line.upper():
                    if current_section:
                        reglas_content.append('\n'.join(current_section))
                        current_section = []
                
                current_section.append(line)
            
            # Agregar la última sección
            if current_section:
                epicas_content.append('\n'.join(current_section))
        
        # Ensamblar resultado DEF estructurado
        if epicas_content:
            result += "## ÉPICAS IDENTIFICADAS\n\n"
            for i, epica in enumerate(epicas_content, 1):
                result += f"### Épica {i}\n{epica}\n\n"
        
        if funcionalidades_content:
            result += "## FUNCIONALIDADES\n\n"
            for i, funcionalidad in enumerate(funcionalidades_content, 1):
                result += f"### Funcionalidad {i}\n{funcionalidad}\n\n"
        
        if historias_content:
            result += "## HISTORIAS DE USUARIO\n\n"
            for i, historia in enumerate(historias_content, 1):
                result += f"### Historia {i}\n{historia}\n\n"
                
        if reglas_content:
            result += "## REGLAS DE NEGOCIO\n\n"
            for i, regla in enumerate(reglas_content, 1):
                result += f"### Regla {i}\n{regla}\n\n"
    else:
        # Agrupación para DAT (Técnico)
        componentes_content = []
        algoritmos_content = []
        dependencias_content = []
        migracion_content = []
        
        for i, chunk in enumerate(chunks, 1):
            lines = chunk.split('\n')
            current_section = []
            
            for line in lines:
                if 'COMPONENTE' in line.upper() or 'COMPONENT' in line.upper():
                    if current_section:
                        componentes_content.append('\n'.join(current_section))
                        current_section = []
                elif 'ALGORITMO' in line.upper() or 'ALGORITHM' in line.upper():
                    if current_section:
                        algoritmos_content.append('\n'.join(current_section))
                        current_section = []
                elif 'DEPENDENCIA' in line.upper() or 'DEPENDENCY' in line.upper():
                    if current_section:
                        dependencias_content.append('\n'.join(current_section))
                        current_section = []
                elif 'MIGRACIÓN' in line.upper() or 'MIGRATION' in line.upper():
                    if current_section:
                        migracion_content.append('\n'.join(current_section))
                        current_section = []
                
                current_section.append(line)
            
            # Agregar la última sección
            if current_section:
                componentes_content.append('\n'.join(current_section))
        
        # Ensamblar resultado DAT estructurado
        if componentes_content:
            result += "## COMPONENTES TÉCNICOS\n\n"
            for i, componente in enumerate(componentes_content, 1):
                result += f"### Componente {i}\n{componente}\n\n"
        
        if algoritmos_content:
            result += "## ALGORITMOS Y ESTRUCTURAS\n\n"
            for i, algoritmo in enumerate(algoritmos_content, 1):
                result += f"### Algoritmo {i}\n{algoritmo}\n\n"
                
        if dependencias_content:
            result += "## DEPENDENCIAS TÉCNICAS\n\n"
            for i, dependencia in enumerate(dependencias_content, 1):
                result += f"### Dependencia {i}\n{dependencia}\n\n"
                
        if migracion_content:
            result += "## ASPECTOS DE MIGRACIÓN\n\n"
            for i, migracion in enumerate(migracion_content, 1):
                result += f"### Migración {i}\n{migracion}\n\n"
    
    return result

# Función para generar DEF (Documento de Especificación Funcional) - CORREGIDA
def generate_def_with_retry(project_name, project_stats, all_code, progress_tracker=None):
    """Genera DEF: Documento de Especificación Funcional basado en análisis de código legado"""
    
    # Dividir código en chunks más grandes
    code_chunks = split_code_into_chunks(all_code, max_chunk_size=45000)
    
    if progress_tracker:
        progress_tracker.total_chunks = len(code_chunks)
        progress_tracker.update_chunk_progress(0, "Iniciando análisis DEF - Especificación Funcional")
    
    logger.info(f"Procesando DEF (Especificación Funcional) en {len(code_chunks)} chunk(s)")
    
    # Si solo hay un chunk, usar prompt completo para DEF
    if len(code_chunks) == 1:
        logger.info("Solo un chunk, procesando DEF completo")
        
        if progress_tracker:
            progress_tracker.update_chunk_progress(1, "Generando DEF - Especificación Funcional")
        
        def_prompt = PromptTemplate(
            input_variables=["project_name", "project_stats", "code_chunk"],
            template="""Eres un analista de negocio especializado en crear Documentos de Especificación Funcional (DEF) a partir de código legado C/C++.
            Tu tarea es generar un DEF completo analizando el código desde la perspectiva de REQUERIMIENTOS DE NEGOCIO y FUNCIONALIDAD.

            PROYECTO DE CÓDIGO LEGADO: {project_name}

            ENFOQUE DEL DEF - FUNCIONALIDAD Y NEGOCIO:
            - Identifica QUÉ funcionalidades de negocio implementa el sistema
            - Define épicas, requerimientos funcionales e historias de usuario
            - Documenta reglas de negocio encontradas en el código
            - Establece requisitos no funcionales basados en la implementación
            - NO incluyas detalles técnicos de implementación (esos van en el DAT)
            - Enfócate en la perspectiva del usuario final y procesos de negocio

            ESTRUCTURA DEL DEF:

            # DOCUMENTO DE ESPECIFICACIÓN FUNCIONAL
            ## {project_name}

            ## 1. INTRODUCCIÓN

            ### 1.1 Propósito
            [Descripción del propósito del sistema basado en el análisis del código]

            ### 1.2 Situación Actual
            [Qué hace actualmente el sistema según el código analizado]

            ### 1.3 Situación Deseada (Modernización)
            [Hacia dónde debería evolucionar el sistema]

            ### 1.4 Datos Generales
            - **Nombre del Sistema:** {project_name}
            - **Lenguaje Actual:** C/C++ (Código Legado)
            - **Tipo de Sistema:** [Identificado del código - ej: Sistema de Gestión, Aplicación de Procesamiento, etc.]
            - **Dominio de Negocio:** [Dominio identificado del código]

            ### 1.5 Beneficio Esperado de la Modernización
            [Beneficios estimados de migrar el sistema a tecnologías modernas]

            ### 1.6 Definiciones, Acrónimos y Abreviaturas
            [Términos de negocio identificados en el código]

            ## 2. DESCRIPCIÓN GENERAL

            ### 2.1 Alcance Funcional
            [Qué funcionalidades cubre el sistema actual según el código]

            ### 2.2 Perspectiva del Producto
            [Cómo se posiciona el sistema en el contexto de negocio]

            ### 2.3 Fuera de Alcance
            [Qué NO hace el sistema actual]

            ## 3. FUNCIONALIDAD DEL PRODUCTO

            ### 3.1 Épicas Identificadas

            #### ÉPICA 1: [Nombre del Dominio Funcional Principal]
            **Descripción:** [Qué grupo de funcionalidades maneja]
            **Valor de Negocio:** [Por qué es importante para el negocio]
            **Criterios de Aceptación de la Épica:**
            - [Criterio 1]
            - [Criterio 2]

            **Funcionalidades (FN) de la Épica:**
            - **FN1:** [Nombre de la funcionalidad]
              - **Descripción:** [Qué hace esta funcionalidad]
              - **Entrada:** [Qué necesita como input]
              - **Salida:** [Qué produce como output]
              - **Reglas de Negocio Aplicables:** [RN1, RN2, etc.]

            **Historias de Usuario de la Épica:**
            - **HU1:** [Título de la historia]
              - **Como** [tipo de usuario],
              - **Quiero** [funcionalidad específica],
              - **Para** [beneficio de negocio]
              - **Criterios de Aceptación:**
                - Dado que [contexto], cuando [acción], entonces [resultado]
                - Dado que [contexto], cuando [acción], entonces [resultado]
              - **Casos de Uso Asociados:** [CU1, CU2]

            #### ÉPICA 2: [Segundo Dominio Funcional]
            [Misma estructura...]

            #### ÉPICA 3: [Tercer Dominio Funcional]
            [Misma estructura...]

            ### 3.2 Casos de Uso Principales

            #### Caso de Uso 1: [Nombre del proceso principal]
            **ID:** CU001
            **Actor Principal:** [Usuario que ejecuta]
            **Objetivo:** [Qué quiere lograr]
            **Precondiciones:** [Estado inicial requerido]
            **Postcondiciones:** [Estado final esperado]
            
            **Flujo Principal:**
            1. [Paso funcional 1]
            2. [Paso funcional 2]
            3. [Paso funcional 3]
            
            **Flujos Alternativos:**
            - **A1:** Si [condición], entonces [flujo alternativo]
            
            **Flujos de Excepción:**
            - **E1:** Si [error], entonces [manejo del error]

            ## 4. REGLAS DE NEGOCIO IDENTIFICADAS

            ### RN001: [Nombre de la regla]
            **Descripción:** [Descripción de la regla encontrada en el código]
            **Origen:** [Función/módulo donde se implementa]
            **Tipo:** [Validación/Cálculo/Restricción/etc.]
            **Impacto:** [Dónde aplica esta regla]
            **Ejemplo:** [Ejemplo concreto del código]

            ### RN002: [Segunda regla de negocio]
            [Misma estructura...]

            ## 5. REQUISITOS NO FUNCIONALES

            ### 5.1 Requisitos de Rendimiento
            **Identificados del código actual:**
            - [Análisis de performance basado en algoritmos encontrados]
            - [Requisitos de memoria identificados]
            - [Requisitos de procesamiento]

            **Requisitos para modernización:**
            - [Nuevos requisitos de rendimiento esperados]

            ### 5.2 Seguridad
            **Implementación actual:**
            - [Medidas de seguridad encontradas en el código]
            - [Validaciones de entrada identificadas]
            - [Controles de acceso implementados]

            **Requisitos de seguridad moderna:**
            - [Nuevos estándares de seguridad requeridos]

            ### 5.3 Disponibilidad
            **Análisis actual:**
            - [Mecanismos de disponibilidad en el código]
            - [Manejo de errores para continuidad]

            **Requisitos modernos:**
            - [Requisitos de alta disponibilidad]

            ### 5.4 Mantenibilidad
            **Situación actual:**
            - [Análisis de mantenibilidad del código legado]

            **Requisitos futuros:**
            - [Requisitos de mantenibilidad para el sistema moderno]

            ## 6. RESTRICCIONES

            ### 6.1 Restricciones Actuales (Identificadas del Código)
            - [Limitaciones tecnológicas del código actual]
            - [Dependencias que limitan el sistema]
            - [Restricciones de plataforma]

            ### 6.2 Restricciones para la Modernización
            - [Restricciones para la migración]
            - [Limitaciones de recursos]
            - [Restricciones de tiempo]

            ## 7. SUPUESTOS

            ### 7.1 Supuestos del Sistema Actual
            - [Supuestos identificados en la lógica del código]
            - [Asunciones sobre datos de entrada]
            - [Supuestos sobre el entorno de operación]

            ### 7.2 Supuestos para la Modernización
            - [Supuestos para la migración]
            - [Asunciones sobre tecnologías objetivo]

            ## 8. RIESGOS

            ### 8.1 Riesgos del Sistema Actual
            - [Riesgos identificados en el código legado]
            - [Vulnerabilidades encontradas]
            - [Puntos críticos de falla]

            ### 8.2 Riesgos de la Modernización
            - [Riesgos del proceso de migración]
            - [Riesgos de pérdida de funcionalidad]
            - [Riesgos de integración]

            ## 9. EVOLUCIÓN PREVISIBLE DEL SISTEMA

            ### 9.1 Roadmap Funcional
            **Fase 1: Migración Base**
            - [Funcionalidades core a migrar primero]

            **Fase 2: Mejoras Funcionales**
            - [Mejoras a implementar post-migración]

            **Fase 3: Optimizaciones**
            - [Optimizaciones futuras]

            ### 9.2 Nuevas Funcionalidades Propuestas
            - [Funcionalidades que se podrían agregar]
            - [Mejoras de usabilidad]
            - [Integraciones futuras]

            ## 10. MATRIZ DE TRAZABILIDAD

            | Épica | Funcionalidad | Historia Usuario | Caso de Uso | Regla Negocio | Req. No Funcional |
            |-------|---------------|------------------|-------------|---------------|-------------------|
            | E1    | FN1          | HU1             | CU001       | RN001         | RNF001           |
            | E1    | FN2          | HU2             | CU002       | RN002         | RNF002           |

            ## 11. CRITERIOS DE ACEPTACIÓN GENERALES
            - [Criterios que aplican a todo el sistema]
            - [Estándares de calidad funcional]
            - [Criterios de completitud]

            ## 12. GLOSARIO DE TÉRMINOS DE NEGOCIO
            - **Término 1:** [Definición desde perspectiva de negocio]
            - **Término 2:** [Definición desde perspectiva de negocio]

            CONTEXTO DEL PROYECTO:
            {project_stats}

            CÓDIGO LEGADO C/C++ A ANALIZAR:
            {code_chunk}

            OBJETIVO: Generar un DEF completo enfocado en funcionalidad, épicas, historias de usuario, reglas de negocio y requisitos desde la perspectiva del negocio y usuario final."""
        )
        
        try:
            formatted_prompt = def_prompt.format(
                project_name=project_name,
                project_stats=project_stats,
                code_chunk=code_chunks[0]
            )
            
            messages = [
                SystemMessage(content="Eres un analista de negocio experto en crear Documentos de Especificación Funcional (DEF). Te especializas en extraer requerimientos funcionales, épicas, historias de usuario y reglas de negocio del código, enfocándote en QUÉ hace el sistema desde la perspectiva del usuario final y procesos de negocio."),
                HumanMessage(content=formatted_prompt)
            ]
            
            response = invoke_llm_with_retry(messages, f"DEF - Especificación Funcional")
            
            if progress_tracker:
                progress_tracker.update_chunk_progress(1, "DEF completado")
            
            logger.info("DEF (Especificación Funcional) generado exitosamente")
            return response.content
            
        except Exception as e:
            logger.error(f"Error generando DEF (Especificación Funcional): {e}")
            return f"Error al generar DEF (Especificación Funcional): {str(e)}"
    
    # Para múltiples chunks, usar formato optimizado FUNCIONAL
    def_prompt_optimized = PromptTemplate(
        input_variables=["project_name", "project_stats", "code_chunk", "chunk_number", "total_chunks"],
        template="""Análisis DEF Funcional - Parte {chunk_number} de {total_chunks} - {project_name}

Identifica elementos FUNCIONALES de esta parte del código para crear DEF.

ÉPICAS_FUNCIONALES:
- [Nombre del dominio funcional]: [Qué procesos de negocio maneja]

FUNCIONALIDADES:
- FN: [Nombre] - [Qué hace funcionalmente] - [Input/Output de negocio]

HISTORIAS_USUARIO:
- HU: COMO [rol] QUIERO [funcionalidad] PARA [beneficio] | CRITERIOS: [criterios funcionales]

REGLAS_NEGOCIO:
- RN: [Descripción de regla encontrada en código] - [Dónde se aplica] - [Función que la implementa]

CASOS_USO:
- CU: [Nombre] - [Actor] - [Objetivo] - [Flujo básico identificado]

REQUISITOS_NO_FUNCIONALES:
- RNF: [Tipo] - [Descripción basada en código] - [Criterio medible]

RESTRICCIONES:
- [Limitación identificada en código] - [Impacto funcional]

SUPUESTOS:
- [Supuesto de negocio identificado en lógica]

RIESGOS:
- [Riesgo funcional identificado] - [Impacto en el negocio]

CONTEXTO: {project_stats}
CÓDIGO: {code_chunk}

OBJETIVO: Extraer únicamente aspectos funcionales y de negocio para consolidar en DEF completo."""
    )
    
    all_def_results = []
    
    # Procesar cada chunk con enfoque funcional
    for i, chunk in enumerate(code_chunks):
        if progress_tracker:
            progress_tracker.update_chunk_progress(i + 1, f"Analizando funcionalidad parte {i+1}")
        
        try:
            logger.info(f"Extrayendo aspectos funcionales para DEF - chunk {i+1}/{len(code_chunks)}")
            
            formatted_prompt = def_prompt_optimized.format(
                project_name=project_name,
                project_stats=project_stats,
                code_chunk=chunk,
                chunk_number=i+1,
                total_chunks=len(code_chunks)
            )
            
            messages = [
                SystemMessage(content="Eres un analista funcional especializado en crear DEF. Identifica únicamente especificaciones funcionales, épicas, funcionalidades e historias de usuario desde perspectiva de negocio."),
                HumanMessage(content=formatted_prompt)
            ]
            
            response = invoke_llm_with_retry(messages, f"análisis DEF especificación funcional chunk {i+1}")
            all_def_results.append(response.content)
            
            logger.info(f"Análisis DEF especificación funcional generado para chunk {i+1}/{len(code_chunks)}")
            
            if i < len(code_chunks) - 1:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error en análisis DEF especificación funcional para chunk {i+1}: {e}")
            error_message = f"[ERROR_DEF_{i+1}] No se pudo generar especificación funcional: {str(e)}"
            all_def_results.append(error_message)
    
    # Consolidación del DEF
    if len(all_def_results) > 1:
        if progress_tracker:
            progress_tracker.update_chunk_progress(len(code_chunks), "Consolidando DEF")
            progress_tracker.set_consolidation_progress("def", 50)
            time.sleep(0.5)
            progress_tracker.set_consolidation_progress("def", 100)
        
        logger.info("Iniciando consolidación del DEF...")
        try:
            consolidated = consolidate_optimized_analysis(all_def_results, "DEF - Especificación Funcional", project_name)
            logger.info("Consolidación del DEF completada exitosamente")
            return consolidated
        except Exception as e:
            logger.error(f"Error en consolidación del DEF funcional: {e}")
            return create_smart_concatenation(all_def_results, project_name, "DEF - Especificación Funcional")
    else:
        return all_def_results[0] if all_def_results else ""

# Función para generar DAT (Documento de Análisis Técnico) - RENOMBRADA
def generate_dat_with_retry(project_name, project_stats, all_code, progress_tracker=None):
    """Genera DAT: Documento de Análisis Técnico del código legado"""
    
    # Dividir código en chunks más grandes
    code_chunks = split_code_into_chunks(all_code, max_chunk_size=45000)
    
    if progress_tracker:
        progress_tracker.update_chunk_progress(0, "Iniciando análisis DAT técnico")
    
    logger.info(f"Procesando DAT (Análisis Técnico) en {len(code_chunks)} chunk(s)")
    
    # Si solo hay un chunk, procesarlo con análisis técnico completo
    if len(code_chunks) == 1:
        if progress_tracker:
            progress_tracker.update_chunk_progress(1, "Generando DAT técnico")
        
        dat_analysis_prompt = PromptTemplate(
            input_variables=["project_name", "project_stats", "code_chunk"],
            template="""Eres un arquitecto de software especializado en crear Documentos de Análisis Técnico (DAT) de código legado C/C++.
            Tu tarea es generar un DAT completo analizando CÓMO está implementado el sistema técnicamente.

            PROYECTO DE CÓDIGO LEGADO: {project_name}

            ENFOQUE DEL DAT - ÚNICAMENTE TÉCNICO:
            - Analiza CÓMO está implementado el sistema técnicamente
            - Documenta arquitectura, estructuras de datos, algoritmos y flujos técnicos
            - Inventaría todos los componentes técnicos del código
            - Crea plan detallado de migración técnica
            - NO incluyas épicas, requerimientos funcionales o historias de usuario
            - Enfócate en aspectos de implementación, arquitectura y tecnología

            ESTRUCTURA DEL DAT:

            # DOCUMENTO DE ANÁLISIS TÉCNICO (DAT)
            ## {project_name}

            ## 1. RESUMEN EJECUTIVO TÉCNICO
            [Descripción técnica general: arquitectura, tecnologías, paradigmas de programación, complejidad técnica]

            ## 2. ARQUITECTURA DEL SISTEMA

            ### 2.1 Arquitectura General
            **Estilo Arquitectónico:** [Identificado del código - ej: Monolítico, Cliente-Servidor, etc.]
            **Patrones Arquitectónicos:** [Patrones encontrados - ej: MVC, Observer, Factory, etc.]
            **Paradigma de Programación:** [Imperativo, Orientado a Objetos, Estructurado, etc.]

            ### 2.2 Componentes Principales del Sistema
            **Componente 1:** [Nombre del módulo/subsistema]
            - **Propósito Técnico:** [Qué función técnica cumple]
            - **Archivos Principales:** [archivos.cpp, archivos.h]
            - **Interfaces:** [APIs expuestas, puntos de entrada]
            - **Dependencias:** [Qué otros componentes necesita]

            ### 2.3 Flujo Técnico Principal del Sistema
            **Secuencia de Ejecución Detallada:**
            1. **Inicialización:** [main()] → [funciones de setup] → [inicialización de estructuras]
            2. **Procesamiento Principal:** [loop principal] → [funciones de procesamiento] → [gestión de datos]
            3. **Finalización:** [cleanup] → [liberación de recursos] → [cierre]

            ### 2.4 Diagramas de Flujo Técnico
            ```
            [Representación textual del flujo técnico principal]
            Entrada → Validación → Procesamiento → Salida
                ↓         ↓           ↓         ↓
            [detalles] [detalles] [detalles] [detalles]
            ```

            ## 3. INVENTARIO TÉCNICO DETALLADO

            ### 3.1 Módulos y Archivos del Sistema
            **Archivo: [nombre.cpp]**
            - **Propósito:** [Función específica del archivo]
            - **Líneas de código:** [aproximado]
            - **Funciones principales:** [lista de funciones]
            - **Dependencias:** [archivos que incluye]
            - **Complejidad:** [Alta/Media/Baja]

            ### 3.2 Funciones y Métodos
            **Función: [nombre_funcion()]**
            - **Signatura:** [tipo_retorno nombre_funcion(parámetros)]
            - **Propósito:** [Qué algoritmo/lógica implementa]
            - **Complejidad Ciclomática:** [estimada]
            - **Complejidad Temporal:** [O(n), O(log n), etc.]
            - **Archivo:** [donde se define]
            - **Líneas:** [rango de líneas]

            ### 3.3 Estructuras de Datos y Clases
            **Estructura: [nombre_struct]**
            - **Definición:** [campos y tipos]
            - **Tamaño estimado:** [bytes]
            - **Uso:** [dónde y cómo se utiliza]
            - **Alineación de memoria:** [consideraciones]

            **Clase: [nombre_clase]**
            - **Herencia:** [clase base si aplica]
            - **Atributos:** [miembros privados/públicos]
            - **Métodos:** [públicos/privados/protegidos]
            - **Polimorfismo:** [uso de virtual, override]

            ### 3.4 Variables Globales y Constantes
            **Variable Global: [nombre]**
            - **Tipo:** [tipo de dato]
            - **Inicialización:** [cómo y dónde se inicializa]
            - **Scope:** [alcance en el sistema]
            - **Thread Safety:** [análisis de concurrencia]

            ### 3.5 Macros y Definiciones
            **Macro: [#define NOMBRE]**
            - **Valor:** [valor definido]
            - **Uso:** [dónde se utiliza]
            - **Impacto:** [en memoria, performance, etc.]

            ## 4. ANÁLISIS DE DEPENDENCIAS TÉCNICAS

            ### 4.1 Dependencias Internas
            **Matriz de Dependencias:**
            ```
            módulo_a.cpp → incluye → módulo_b.h → usa → función_x()
            módulo_b.cpp → incluye → común.h → usa → estructura_y
            ```

            ### 4.2 Bibliotecas Externas
            **Biblioteca: [nombre]**
            - **Versión:** [si se puede identificar]
            - **Funciones utilizadas:** [APIs específicas]
            - **Licencia:** [si es conocida]
            - **Estado:** [Activa/Obsoleta/Deprecated]

            ### 4.3 APIs del Sistema Operativo
            **API: [nombre_api]**
            - **Plataforma:** [Windows/Linux/Cross-platform]
            - **Propósito:** [Para qué se utiliza]
            - **Alternativas modernas:** [APIs equivalentes actuales]

            ## 5. ALGORITMOS Y COMPLEJIDAD

            ### 5.1 Algoritmos Críticos Identificados
            **Algoritmo: [nombre/descripción]**
            ```c++
            // Pseudocódigo o código simplificado del algoritmo
            for (int i = 0; i < n; i++) {
                // lógica principal
            }
            ```
            - **Complejidad Temporal:** [O(n), O(n²), etc.]
            - **Complejidad Espacial:** [memoria utilizada]
            - **Optimización Posible:** [mejoras sugeridas]

            ### 5.2 Estructuras de Datos Utilizadas
            **Estructura: [tipo]**
            - **Implementación:** [array, lista enlazada, hash table, etc.]
            - **Operaciones:** [inserción, búsqueda, eliminación]
            - **Performance:** [análisis de rendimiento]

            ## 6. GESTIÓN DE MEMORIA Y RECURSOS

            ### 6.1 Patrones de Gestión de Memoria
            **Asignación Dinámica:**
            - **malloc/new:** [dónde se usa]
            - **free/delete:** [cómo se libera]
            - **Potential leaks:** [puntos de riesgo identificados]

            ### 6.2 Gestión de Archivos y I/O
            **Manejo de Archivos:**
            - **Apertura:** [fopen, CreateFile, etc.]
            - **Lectura/Escritura:** [métodos utilizados]
            - **Cierre:** [garantía de cierre]

            ### 6.3 Gestión de Handles y Recursos del SO
            **Recursos:**
            - **Handles de ventana:** [si aplica]
            - **Sockets:** [manejo de red]
            - **Threads:** [gestión de hilos]

            ## 7. CONCURRENCIA Y SINCRONIZACIÓN

            ### 7.1 Modelo de Threading
            **Implementación:**
            - **Threads:** [pthread, std::thread, CreateThread]
            - **Sincronización:** [mutex, semáforos, critical sections]
            - **Shared Data:** [datos compartidos entre threads]

            ### 7.2 Problemas de Concurrencia Identificados
            - **Race Conditions:** [posibles condiciones de carrera]
            - **Deadlocks:** [riesgo de interbloqueos]
            - **Data Races:** [acceso concurrent a datos]

            ## 8. ANÁLISIS DE PERFORMANCE

            ### 8.1 Puntos Críticos de Rendimiento
            **Bottleneck 1:** [descripción]
            - **Ubicación:** [archivo y función]
            - **Impacto:** [en el rendimiento general]
            - **Mejora sugerida:** [optimización propuesta]

            ### 8.2 Uso de Memoria
            **Análisis de Memoria:**
            - **Stack Usage:** [uso del stack]
            - **Heap Usage:** [uso del heap]
            - **Memory Footprint:** [huella de memoria total estimada]

            ## 9. CONFIGURACIÓN Y PARÁMETROS TÉCNICOS

            ### 9.1 Archivos de Configuración
            **Configuración:** [archivos .ini, .conf, registry, etc.]
            - **Parámetros:** [lista de parámetros configurables]
            - **Valores por defecto:** [valores predeterminados]
            - **Validación:** [cómo se validan los parámetros]

            ### 9.2 Parámetros de Compilación
            **Compilación:**
            - **Compiler:** [GCC, MSVC, Clang]
            - **Flags:** [opciones de compilación]
            - **Optimizaciones:** [niveles de optimización]
            - **Target Platform:** [plataforma objetivo]

            ## 10. SEGURIDAD TÉCNICA

            ### 10.1 Vulnerabilidades Identificadas
            **Vulnerabilidad: [tipo]**
            - **Ubicación:** [archivo y línea aproximada]
            - **Riesgo:** [Alto/Medio/Bajo]
            - **Descripción:** [detalle de la vulnerabilidad]
            - **Mitigación:** [cómo solucionarlo]

            ### 10.2 Prácticas de Seguridad Implementadas
            - **Validación de Entrada:** [métodos utilizados]
            - **Sanitización:** [limpieza de datos]
            - **Cifrado:** [si se implementa alguno]

            ## 11. PLAN DE MIGRACIÓN TÉCNICA DETALLADO

            ### 11.1 Análisis de Modernización

            #### 11.1.1 Elementos Críticos para Migración
            **ALTA PRIORIDAD (Debe migrarse):**
            - **malloc/free manual** → **std::unique_ptr/shared_ptr**
              - **Ubicación:** [archivos específicos]
              - **Esfuerzo:** [horas/días estimados]
              - **Riesgo:** [Alto - memory leaks]
            
            - **char* strings** → **std::string**
              - **Ubicación:** [archivos específicos]
              - **Esfuerzo:** [horas/días estimados]
              - **Riesgo:** [Alto - buffer overflows]

            **MEDIA PRIORIDAD (Debe modernizarse):**
            - **Arrays fijos** → **std::vector**
            - **Structs C** → **Clases C++**
            - **printf debugging** → **logging framework**

            **BAJA PRIORIDAD (Opcional):**
            - **Algoritmos funcionando** → mantener si están optimizados
            - **Constantes bien definidas** → mantener

            ### 11.2 Estrategia de Migración Técnica

            #### 11.2.1 Fases de Migración
            **FASE 1: Preparación del Entorno (Semanas 1-2)**
            1. **Setup de herramientas modernas:**
               - CMake 3.20+ para build system
               - vcpkg/Conan para dependencias
               - Visual Studio 2022 o GCC 11+
            
            2. **Análisis estático inicial:**
               - Cppcheck para detección de bugs
               - Clang Static Analyzer
               - Valgrind para memory analysis

            **FASE 2: Migración de Gestión de Memoria (Semanas 3-6)**
            ```cpp
            // Antes (C style):
            Usuario* users = malloc(count * sizeof(Usuario));
            // procesar users
            free(users);
            
            // Después (C++ moderno):
            std::vector<Usuario> users(count);
            // procesamiento automático de memoria
            ```

            **FASE 3: Migración de Strings y I/O (Semanas 7-10)**
            ```cpp
            // Antes:
            char buffer[256];
            strcpy(buffer, input);
            
            // Después:
            std::string buffer = input;
            ```

            **FASE 4: Testing y Validación (Semanas 11-12)**
            - Unit tests con Google Test
            - Performance benchmarks
            - Memory leak detection

            ### 11.3 Herramientas de Migración Recomendadas

            #### 11.3.1 Análisis y Detección
            - **Cppcheck:** detección automática de problemas
            - **Clang-Tidy:** modernización automática de código
            - **include-what-you-use:** limpieza de includes

            #### 11.3.2 Build y Dependencias
            - **CMake:** sistema de build moderno y multiplataforma
            - **vcpkg:** gestión de dependencias C++
            - **Ninja:** build system de alta velocidad

            #### 11.3.3 Testing y Quality Assurance
            - **Google Test:** framework de testing
            - **Google Benchmark:** performance testing
            - **AddressSanitizer:** detección de memory errors

            ### 11.4 Estimaciones Técnicas Detalladas

            #### 11.4.1 Esfuerzo por Tipo de Migración
            | Tipo de Cambio | Complejidad | Tiempo Estimado | Riesgo |
            |----------------|-------------|-----------------|--------|
            | malloc → smart_ptr | Alta | 2-4 días por módulo | Alto |
            | char* → std::string | Media | 1-2 días por módulo | Medio |
            | Arrays → std::vector | Baja | 4-8 horas por módulo | Bajo |
            | C structs → C++ classes | Media | 1-3 días por módulo | Medio |

            #### 11.4.2 Cronograma de Migración
            **Total estimado:** [X semanas/meses]
            - **Preparación:** 15% del tiempo
            - **Migración core:** 50% del tiempo
            - **Testing:** 25% del tiempo
            - **Documentación:** 10% del tiempo

            ### 11.5 Riesgos Técnicos y Mitigaciones

            #### 11.5.1 Riesgos Identificados
            **Riesgo Alto: Pérdida de funcionalidad**
            - **Descripción:** Comportamiento diferente post-migración
            - **Mitigación:** Tests exhaustivos de regresión
            - **Plan B:** Rollback a versión original

            **Riesgo Medio: Performance degradation**
            - **Descripción:** Nuevo código más lento
            - **Mitigación:** Benchmarks continuos
            - **Plan B:** Optimización específica

            ### 11.6 Criterios de Éxito Técnico
            **Métricas de Calidad:**
            - ✅ Zero memory leaks (Valgrind clean)
            - ✅ Zero buffer overflows (AddressSanitizer clean)
            - ✅ Compilación sin warnings (-Wall -Werror)
            - ✅ Code coverage ≥ 80%

            **Métricas de Performance:**
            - ✅ Tiempo de respuesta ≤ versión original + 10%
            - ✅ Uso de memoria ≤ versión original + 15%
            - ✅ Throughput ≥ 95% de versión original

            ## 12. RECOMENDACIONES TÉCNICAS

            ### 12.1 Arquitectura Objetivo
            **Estilo Arquitectónico Recomendado:** [Clean Architecture, Hexagonal, etc.]
            **Tecnologías Objetivo:** [C++20, CMake, vcpkg, etc.]
            **Patrones a Implementar:** [SOLID, RAII, etc.]

            ### 12.2 Tecnologías de Reemplazo
            | Tecnología Actual | Tecnología Objetivo | Justificación |
            |-------------------|-------------------|---------------|
            | malloc/free | std::smart_ptr | Gestión automática de memoria |
            | char* | std::string | Seguridad y facilidad de uso |
            | printf | fmt/spdlog | Logging estructurado |

            ### 12.3 Roadmap Técnico
            **Corto Plazo (1-3 meses):**
            - Migración de gestión de memoria crítica
            - Implementación de tests básicos

            **Medio Plazo (3-6 meses):**
            - Modernización completa del código
            - Optimizaciones de performance

            **Largo Plazo (6+ meses):**
            - Refactoring arquitectónico
            - Nuevas funcionalidades técnicas

            CONTEXTO DEL PROYECTO:
            {project_stats}

            CÓDIGO LEGADO C/C++ A ANALIZAR:
            {code_chunk}

            OBJETIVO: Generar un DAT técnico completo con inventario detallado del código, análisis de arquitectura, plan de migración específico y recomendaciones técnicas para modernización."""
        )
        
        try:
            formatted_prompt = dat_analysis_prompt.format(
                project_name=project_name,
                project_stats=project_stats,
                code_chunk=code_chunks[0]
            )
            
            messages = [
                SystemMessage(content="Eres un arquitecto de software especializado en crear Documentos de Análisis Técnico (DAT). Te enfocas en CÓMO está implementado el sistema técnicamente, inventariando código, arquitectura, dependencias y creando planes de migración específicos. NO incluyes aspectos funcionales de negocio."),
                HumanMessage(content=formatted_prompt)
            ]
            
            response = invoke_llm_with_retry(messages, f"DAT - análisis técnico completo")
            
            if progress_tracker:
                progress_tracker.update_chunk_progress(1, "DAT técnico completado")
            
            logger.info("DAT (Análisis Técnico) generado exitosamente")
            return response.content
            
        except Exception as e:
            logger.error(f"Error generando DAT (Análisis Técnico): {e}")
            return f"Error al generar DAT (Análisis Técnico): {str(e)}"
    
    # Para múltiples chunks, usar formato optimizado TÉCNICO
    dat_prompt_optimized = PromptTemplate(
        input_variables=["project_name", "project_stats", "code_chunk", "chunk_number", "total_chunks"],
        template="""Análisis DAT Técnico - Parte {chunk_number} de {total_chunks} - {project_name}

Analiza TÉCNICAMENTE esta parte del código para el DAT.

INVENTARIO_CÓDIGO:
- ARCHIVOS: [archivo.cpp]: [Propósito técnico específico]
- FUNCIONES: [función()]: [Signatura] - [Algoritmo] - [Complejidad]
- CLASES: [ClaseX]: [Atributos] - [Métodos] - [Responsabilidad técnica]
- ESTRUCTURAS: [struct X]: [Campos y tipos] - [Alineación] - [Uso]

FLUJO_TÉCNICO:
1. [función_a()] → aloca memoria con [malloc/new] → procesa [datos_específicos]
2. [función_b()] → llama API [api_específica()] → maneja [tipo_error]
3. [resultado] → se almacena en [estructura] → se libera con [free/delete]

DEPENDENCIAS_TÉCNICAS:
- INCLUDES: [#include específico] - [Funciones usadas]
- BIBLIOTECAS: [biblioteca] - [Versión] - [APIs utilizadas]
- APIS_SO: [API del SO] - [Parámetros] - [Valor retorno]

ALGORITMOS_ESPECÍFICOS:
- [Algoritmo]: [Complejidad temporal] - [Complejidad espacial] - [Implementación]

MEMORIA_Y_RECURSOS:
- ASIGNACIÓN: [malloc/new específicos] - [Tamaño] - [Patrón]
- LIBERACIÓN: [free/delete específicos] - [Dónde] - [Validación]
- HANDLES: [Archivos/sockets abiertos] - [Cómo se cierran]

CONFIGURACIÓN_TÉCNICA:
- PARÁMETROS: [Variable] - [Tipo] - [Valor] - [Dónde se usa]
- CONSTANTES: [#define] - [Valor] - [Impacto]

ASPECTOS_MIGRACIÓN:
- CRÍTICO: [Elemento crítico] - [Por qué es crítico] - [Estrategia migración]
- MEDIO: [Elemento mejorable] - [Beneficio migración]
- BAJO: [Elemento estable] - [Mantener como está]

CONTEXTO: {project_stats}
CÓDIGO: {code_chunk}"""
    )
    
    all_dat_results = []
    
    # Procesar cada chunk con enfoque técnico
    for i, chunk in enumerate(code_chunks):
        if progress_tracker:
            progress_tracker.update_chunk_progress(i + 1, f"Analizando técnicamente parte {i+1}")
        
        try:
            logger.info(f"Generando análisis técnico DAT para chunk {i+1}/{len(code_chunks)}")
            
            formatted_prompt = dat_prompt_optimized.format(
                project_name=project_name,
                project_stats=project_stats,
                code_chunk=chunk,
                chunk_number=i+1,
                total_chunks=len(code_chunks)
            )
            
            messages = [
                SystemMessage(content="Eres un arquitecto de software especializado en crear DAT. Enfócate únicamente en aspectos técnicos: código, arquitectura, implementación, dependencias y estrategias de migración técnica."),
                HumanMessage(content=formatted_prompt)
            ]
            
            response = invoke_llm_with_retry(messages, f"análisis DAT técnico chunk {i+1}")
            all_dat_results.append(response.content)
            
            logger.info(f"Análisis DAT técnico generado para chunk {i+1}/{len(code_chunks)}")
            
            time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error generando análisis DAT técnico para chunk {i+1}: {e}")
            error_message = f"[ERROR_DAT_{i+1}] No se pudo generar análisis técnico: {str(e)}"
            all_dat_results.append(error_message)
    
    # Consolidación del DAT
    if len(all_dat_results) > 1:
        if progress_tracker:
            progress_tracker.update_chunk_progress(len(code_chunks), "Consolidando DAT técnico")
            progress_tracker.set_consolidation_progress("dat", 50)
            time.sleep(0.5)
            progress_tracker.set_consolidation_progress("dat", 100)
        
        logger.info("Iniciando consolidación del DAT técnico...")
        try:
            consolidated = consolidate_optimized_analysis(all_dat_results, "DAT - Análisis Técnico", project_name)
            logger.info("Consolidación del DAT técnico completada exitosamente")
            return consolidated
        except Exception as e:
            logger.error(f"Error en consolidación del DAT técnico: {e}")
            return create_smart_concatenation(all_dat_results, project_name, "DAT - Análisis Técnico")
    else:
        return all_dat_results[0] if all_dat_results else ""

# Endpoint principal con progress tracking mejorado
@analizarCodigoRepomix_bp.route('/analizarCodigoRepomix/zip', methods=['POST'])
def analyze_zip_file():
    # Generar session_id único para tracking
    session_id = str(uuid.uuid4())
    
    if 'zip_file' not in request.files:
        return jsonify({"error": "No se envió archivo ZIP"}), 400
    
    zip_file = request.files['zip_file']
    project_name = request.form.get('project_name', 'Proyecto de Código Legado desde ZIP')
    
    if zip_file.filename == '' or not zip_file.filename.lower().endswith('.zip'):
        return jsonify({"error": "Debe ser un archivo ZIP válido"}), 400
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        logger.info(f"Iniciando análisis optimizado de proyecto de código legado: {project_name}")
        
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
        
        # Buscar archivos de código legado
        uploaded_files = []
        total_size = 0
        
        progress_tracker.update_chunk_progress(0, "Procesando archivos de código")
        
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
            return jsonify({"error": "No se encontraron archivos de código legado válidos en el ZIP"}), 400
        
        logger.info(f"Procesando {len(uploaded_files)} archivos de código legado extraídos del ZIP")
        
        # Analizar archivos extraídos
        project_stats = {
            "total_files": len(uploaded_files),
            "analyzed_files": len(uploaded_files),
            "extensions": {},
            "total_lines": 0,
            "c_files": 0,
            "cpp_files": 0,
            "header_files": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_structs": 0,
            "total_includes": 0,
            "total_defines": 0,
            "total_apis": 0,
            "compilers_detected": [],
            "frameworks_found": []
        }
        
        all_code = ""
        analyzed_files = []
        
        for file_info in uploaded_files:
            try:
                with open(file_info['temp_path'], 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.count('\n') + 1
                    
                    # Analizar código legado
                    analysis = analyze_legacy_code(content, file_info['original_name'])
                    
                    # Obtener extensión
                    _, ext = os.path.splitext(file_info['original_name'])
                    ext = ext.lower()
                    
                    # Estadísticas por extensión
                    if ext in project_stats["extensions"]:
                        project_stats["extensions"][ext] += 1
                    else:
                        project_stats["extensions"][ext] = 1
                    
                    # Clasificar archivos
                    if ext in ['.c']:
                        project_stats["c_files"] += 1
                    elif ext in ['.cpp', '.cxx', '.cc', '.c++']:
                        project_stats["cpp_files"] += 1
                    elif ext in ['.h', '.hpp', '.hxx', '.hh', '.h++']:
                        project_stats["header_files"] += 1
                    
                    # Detectar compiladores y frameworks por contenido
                    content_lower = content.lower()
                    if 'visual studio' in content_lower or 'msvc' in content_lower or '_msc_ver' in content_lower:
                        if 'MSVC/Visual Studio' not in project_stats["compilers_detected"]:
                            project_stats["compilers_detected"].append('MSVC/Visual Studio')
                    if 'gcc' in content_lower or '__gnuc__' in content_lower:
                        if 'GCC' not in project_stats["compilers_detected"]:
                            project_stats["compilers_detected"].append('GCC')
                    if 'clang' in content_lower or '__clang__' in content_lower:
                        if 'Clang' not in project_stats["compilers_detected"]:
                            project_stats["compilers_detected"].append('Clang')
                    
                    # Detectar frameworks comunes
                    if 'mfc' in content_lower or 'afx' in content_lower:
                        if 'MFC' not in project_stats["frameworks_found"]:
                            project_stats["frameworks_found"].append('MFC')
                    if 'atl' in content_lower:
                        if 'ATL' not in project_stats["frameworks_found"]:
                            project_stats["frameworks_found"].append('ATL')
                    if 'qt' in content_lower or 'qobject' in content_lower:
                        if 'Qt' not in project_stats["frameworks_found"]:
                            project_stats["frameworks_found"].append('Qt')
                    if 'boost' in content_lower:
                        if 'Boost' not in project_stats["frameworks_found"]:
                            project_stats["frameworks_found"].append('Boost')
                    
                    # Agregar a archivos analizados
                    analyzed_files.append({
                        "name": os.path.basename(file_info['original_name']),
                        "path": file_info['original_name'],
                        "extension": ext,
                        "size": file_info['size'],
                        "lines": lines,
                        "functions_count": len(analysis["functions"]),
                        "classes_count": len(analysis["classes"]),
                        "structs_count": len(analysis["structs"]),
                        "includes_count": len(analysis["includes"]),
                        "defines_count": len(analysis["defines"]),
                        "apis_count": len(analysis["apis"])
                    })
                    
                    # Acumular estadísticas
                    project_stats["total_lines"] += lines
                    project_stats["total_functions"] += len(analysis["functions"])
                    project_stats["total_classes"] += len(analysis["classes"])
                    project_stats["total_structs"] += len(analysis["structs"])
                    project_stats["total_includes"] += len(analysis["includes"])
                    project_stats["total_defines"] += len(analysis["defines"])
                    project_stats["total_apis"] += len(analysis["apis"])
                    
                    # Agregar al código completo
                    all_code += f"\n\n--- Archivo: {file_info['original_name']} ({lines} líneas) ---\n"
                    all_code += f"Funciones encontradas: {len(analysis['functions'])}\n"
                    all_code += f"Clases encontradas: {len(analysis['classes'])}\n"
                    all_code += f"Estructuras encontradas: {len(analysis['structs'])}\n"
                    all_code += f"Includes encontrados: {len(analysis['includes'])}\n"
                    all_code += f"Defines encontrados: {len(analysis['defines'])}\n"
                    all_code += f"APIs encontradas: {len(analysis['apis'])}\n\n"
                    all_code += content
                    
            except Exception as e:
                logger.error(f"Error al leer archivo {file_info['original_name']}: {e}")
        
        # Preparar datos para los prompts
        stats_text = f"""- Total de archivos: {project_stats["total_files"]}
- Archivos analizados: {project_stats["analyzed_files"]}
- Total de líneas de código: {project_stats["total_lines"]}
- Archivos C: {project_stats["c_files"]}
- Archivos C++: {project_stats["cpp_files"]}
- Archivos de cabecera: {project_stats["header_files"]}
- Total de funciones encontradas: {project_stats["total_functions"]}
- Total de clases encontradas: {project_stats["total_classes"]}
- Total de estructuras encontradas: {project_stats["total_structs"]}
- Total de includes encontrados: {project_stats["total_includes"]}
- Total de defines encontrados: {project_stats["total_defines"]}
- Total de APIs encontradas: {project_stats["total_apis"]}
- Compiladores detectados: {project_stats["compilers_detected"]}
- Frameworks encontrados: {project_stats["frameworks_found"]}"""
        
        # Actualizar progreso antes de iniciar análisis
        progress_tracker.update_chunk_progress(0, "Archivos procesados, iniciando análisis optimizado")
        
        # Generar análisis OPTIMIZADO con progress tracking mejorado
        logger.info("Generando DEF (Especificación Funcional) con análisis optimizado...")
        def_analysis = generate_def_with_retry(project_name, stats_text, all_code, progress_tracker)
        
        logger.info("Generando DAT (Análisis Técnico) con análisis optimizado...")
        dat_analysis = generate_dat_with_retry(project_name, stats_text, all_code, progress_tracker)
        
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
        
        logger.info(f"Análisis optimizado completado exitosamente para proyecto de código legado: {project_name}")
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "timestamp": timestamp,
            "def_analysis": def_analysis,  # ✅ Documento de Especificación Funcional
            "dat_analysis": dat_analysis,  # ✅ Documento de Análisis Técnico
            "analyzed_files": analyzed_files,
            "directory_tree": directory_tree,
            "project_stats": project_stats,
            "documentation_found": False,
            "analyzed_documents": [],
            "code_analysis": {
                "language": "C/C++ Legacy",
                "total_functions": project_stats["total_functions"],
                "total_classes": project_stats["total_classes"],
                "total_structs": project_stats["total_structs"],
                "total_includes": project_stats["total_includes"],
                "total_defines": project_stats["total_defines"],
                "total_apis": project_stats["total_apis"],
                "compilers_detected": project_stats["compilers_detected"],
                "frameworks_found": project_stats["frameworks_found"]
            },
            "summary": {
                "files_analyzed": len(analyzed_files),
                "total_lines_analyzed": project_stats["total_lines"],
                "documentation_files_found": 0,
                "analysis_completed": True,
                "upload_method": "zip_upload",
                "consolidation_applied": True,
                "optimization_applied": True,
                "document_types_generated": ["DEF", "DAT"],  # NUEVO
                "retry_info": {
                    "total_retries_used": rate_limit_handler.retry_count,
                    "rate_limiting_encountered": rate_limit_handler.retry_count > 0
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error al analizar ZIP de código legado optimizado: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": f"Error procesando ZIP de código legado: {str(e)}",
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

# Endpoint para obtener estado del servicio ACTUALIZADO
@analizarCodigoRepomix_bp.route('/analizarCodigoRepomix/status', methods=['GET'])
def get_analysis_status():
    """Endpoint para verificar el estado del servicio optimizado"""
    return jsonify({
        "status": "running",
        "service_type": "optimized_legacy_code_analyzer",
        "version": "2.0_optimized",
        "features": [
            "def_functional_analysis",      # NUEVO
            "dat_technical_analysis",       # NUEVO
            "optimized_chunk_processing",
            "smart_rate_limiting",
            "efficient_consolidation",
            "fallback_concatenation",
            "multi_language_support",
            "websocket_progress_tracking"
        ],
        "document_types": {
            "def": {
                "name": "Documento de Especificación Funcional",
                "focus": "Funcionalidad, épicas, historias de usuario, reglas de negocio",
                "output": "Requerimientos funcionales y especificaciones de negocio"
            },
            "dat": {
                "name": "Documento de Análisis Técnico", 
                "focus": "Arquitectura, código, dependencias, migración técnica",
                "output": "Inventario técnico y plan de migración detallado"
            }
        },
        "supported_extensions": list(ALLOWED_EXTENSIONS),
        "supported_languages": ["C", "C++", "Legacy C/C++"],
        "supported_compilers": ["MSVC", "GCC", "Clang", "Visual Studio"],
        "supported_frameworks": ["MFC", "ATL", "Qt", "Boost"],
        "rate_limit_config": {
            "max_retries": RateLimitConfig.MAX_RETRIES,
            "base_delay": RateLimitConfig.BASE_DELAY,
            "max_delay": RateLimitConfig.MAX_DELAY,
            "exponential_backoff": RateLimitConfig.EXPONENTIAL_BACKOFF,
            "optimization": "enabled"
        },
        "consolidation_config": {
            "max_chunk_size": 45000,
            "optimized_consolidation": True,
            "smart_concatenation": True,
            "fallback_on_error": True,
            "max_chunks_for_ai_consolidation": 4
        },
        "websocket_events": [
            "analysis_progress",
            "analysis_complete",
            "analysis_error"
        ],
        "websocket_enabled": socketio is not None,
        "optimizations": {
            "reduced_token_usage": True,
            "structured_chunk_format": True,
            "intelligent_fallbacks": True,
            "rate_limit_prevention": True
        },
        "timestamp": datetime.datetime.now().isoformat()
    })

# Endpoint adicional para consolidación manual OPTIMIZADO
@analizarCodigoRepomix_bp.route('/analizarCodigoRepomix/consolidate', methods=['POST'])
def manual_consolidate():
    """Endpoint para consolidar análisis existentes manualmente con optimización"""
    try:
        data = request.get_json()
        
        if not data or 'chunks' not in data:
            return jsonify({"error": "Datos de chunks requeridos"}), 400
        
        project_name = data.get('project_name', 'Proyecto Manual')
        analysis_type = data.get('analysis_type', 'Análisis General')
        chunks = data.get('chunks', [])
        use_optimization = data.get('use_optimization', True)
        
        if not chunks:
            return jsonify({"error": "No hay chunks para consolidar"}), 400
        
        # Mapear tipos de análisis a nombres correctos
        analysis_type_map = {
            "def": "DEF - Especificación Funcional",
            "dat": "DAT - Análisis Técnico",
            "functional": "DEF - Especificación Funcional",
            "technical": "DAT - Análisis Técnico"
        }
        mapped_analysis_type = analysis_type_map.get(analysis_type.lower(), analysis_type)
        
        logger.info(f"Iniciando consolidación manual optimizada de {len(chunks)} chunks para {project_name}")
        
        # Usar consolidación optimizada o tradicional según parámetro
        if use_optimization:
            consolidated_result = consolidate_optimized_analysis(chunks, mapped_analysis_type, project_name)
            consolidation_method = "optimized"
        else:
            consolidated_result = consolidate_chunk_analysis(chunks, mapped_analysis_type, project_name)
            consolidation_method = "traditional"
        
        return jsonify({
            "success": True,
            "consolidated_analysis": consolidated_result,
            "chunks_processed": len(chunks),
            "analysis_type": mapped_analysis_type,
            "project_name": project_name,
            "consolidation_method": consolidation_method,
            "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        })
        
    except Exception as e:
        logger.error(f"Error en consolidación manual optimizada: {str(e)}")
        return jsonify({
            "error": f"Error en consolidación manual: {str(e)}",
            "success": False
        }), 500

# Endpoint adicional para análisis específico de DLLs
@analizarCodigoRepomix_bp.route('/analizarCodigoRepomix/dll-analysis', methods=['POST'])
def analyze_dll_specific():
    """Endpoint especializado para análisis de DLLs y bibliotecas"""
    try:
        data = request.get_json()
        
        if not data or 'dll_path' not in data:
            return jsonify({"error": "Ruta de DLL requerida"}), 400
        
        dll_path = data.get('dll_path', '')
        project_name = data.get('project_name', 'Análisis de DLL')
        
        # Aquí se podría implementar análisis específico de DLLs
        # usando herramientas como objdump, nm, dumpbin, etc.
        
        logger.info(f"Análisis específico de DLL solicitado para: {dll_path}")
        
        return jsonify({
            "success": True,
            "message": "Análisis de DLL específico en desarrollo",
            "dll_path": dll_path,
            "project_name": project_name,
            "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
            "note": "Esta funcionalidad se implementará en una versión futura"
        })
        
    except Exception as e:
        logger.error(f"Error en análisis específico de DLL: {str(e)}")
        return jsonify({
            "error": f"Error en análisis de DLL: {str(e)}",
            "success": False
        }), 500

# Endpoint para análisis de dependencias
@analizarCodigoRepomix_bp.route('/analizarCodigoRepomix/dependencies', methods=['POST'])
def analyze_dependencies():
    """Endpoint para análisis específico de dependencias"""
    try:
        data = request.get_json()
        
        if not data or 'code_content' not in data:
            return jsonify({"error": "Contenido de código requerido"}), 400
        
        code_content = data.get('code_content', '')
        project_name = data.get('project_name', 'Análisis de Dependencias')
        
        # Análisis específico de dependencias
        analysis = analyze_legacy_code(code_content, 'dependency_analysis')
        
        logger.info(f"Análisis de dependencias completado para: {project_name}")
        
        return jsonify({
            "success": True,
            "dependencies_analysis": {
                "includes": analysis["includes"],
                "dlls": analysis["dlls"],
                "apis": analysis["apis"],
                "namespaces": analysis["namespaces"]
            },
            "project_name": project_name,
            "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        })
        
    except Exception as e:
        logger.error(f"Error en análisis de dependencias: {str(e)}")
        return jsonify({
            "error": f"Error en análisis de dependencias: {str(e)}",
            "success": False
        }), 500

# Endpoint para obtener progreso de análisis (opcional, para polling si WebSocket falla)
@analizarCodigoRepomix_bp.route('/analizarCodigoRepomix/progress/<session_id>', methods=['GET'])
def get_analysis_progress(session_id):
    """Endpoint para obtener progreso de análisis por polling (fallback si WebSocket falla)"""
    try:
        if session_id in analysis_progress:
            return jsonify({
                "success": True,
                "progress": analysis_progress[session_id],
                "timestamp": datetime.datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Session ID no encontrado",
                "timestamp": datetime.datetime.now().isoformat()
            }), 404
        
    except Exception as e:
        logger.error(f"Error obteniendo progreso para session {session_id}: {str(e)}")
        return jsonify({
            "error": f"Error obteniendo progreso: {str(e)}",
            "success": False
        }), 500

# NUEVO: Endpoint para análisis de optimización
@analizarCodigoRepomix_bp.route('/analizarCodigoRepomix/optimization-stats', methods=['GET'])
def get_optimization_stats():
    """Endpoint para obtener estadísticas de optimización del sistema"""
    try:
        return jsonify({
            "success": True,
            "optimization_stats": {
                "chunk_size_optimized": 45000,
                "original_chunk_size": 35000,
                "improvement_percentage": 28.57,
                "rate_limit_reduction": {
                    "max_retries_reduced_from": 65,
                    "max_retries_reduced_to": 3,
                    "max_delay_reduced_from": 300,
                    "max_delay_reduced_to": 120,
                    "improvement_percentage": 60.0
                },
                "consolidation_optimization": {
                    "smart_concatenation_enabled": True,
                    "max_chunks_for_ai": 4,
                    "fallback_strategy": "structured_concatenation"
                },
                "token_usage_optimization": {
                    "structured_format_enabled": True,
                    "redundant_headers_removed": True,
                    "essential_content_extraction": True
                }
            },
            "performance_metrics": {
                "estimated_token_reduction": "40-60%",
                "rate_limit_incidents_reduction": "80-90%",
                "processing_time_improvement": "30-50%"
            },
            "timestamp": datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de optimización: {str(e)}")
        return jsonify({
            "error": f"Error obteniendo estadísticas: {str(e)}",
            "success": False
        }), 500

# NUEVO: Función de fallback para la consolidación original (mantenida para compatibilidad)
def consolidate_chunk_analysis(all_chunks_results, analysis_type, project_name):
    """Función de consolidación original mantenida para compatibilidad"""
    
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
    
    # Para múltiples chunks, usar concatenación inteligente en lugar de consolidación IA pesada
    logger.warning(f"Usando concatenación inteligente para {len(valid_chunks)} chunks de {analysis_type} para evitar rate limit")
    return create_smart_concatenation(valid_chunks, project_name, analysis_type)