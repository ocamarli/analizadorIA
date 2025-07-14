# catalog_api_simple.py
from flask import Blueprint, jsonify, request
import redis
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Blueprint para catálogo
catalogos_bp = Blueprint('catalog', __name__)

# Configuración básica de Redis
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'rcreskofpoccace01.redis.cache.windows.net'),
    'port': int(os.getenv('REDIS_PORT', 6380)),
    'password': os.getenv('REDIS_PASSWORD','2h9cvxkMjv9RsUYZZqcPce3vzGzxHimvcAzCaGED3ns='),
    'decode_responses': True,
    'ssl': True
}

# Variable global para la conexión
redis_client = None

def connect_to_redis():
    """Establece conexión con Redis"""
    global redis_client
    try:
        redis_client = redis.Redis(**REDIS_CONFIG)
        redis_client.ping()
        print("✅ Conexión con Redis establecida correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al conectar con Redis: {str(e)}")
        redis_client = None
        return False

# Intenta conectar al iniciar
connect_to_redis()

@catalogos_bp.route('/test-connection')
def test_connection():
    """Endpoint para probar la conexión con Redis"""
    if redis_client and redis_client.ping():
        return jsonify({
            'status': 'success',
            'message': 'Conectado a Redis correctamente',
            'redis_info': {
                'host': REDIS_CONFIG['host'],
                'port': REDIS_CONFIG['port']
            }
        })
    else:
        # Intentar reconectar
        if connect_to_redis():
            return jsonify({
                'status': 'success',
                'message': 'Reconexión exitosa con Redis'
            })
        return jsonify({
            'status': 'error',
            'message': 'No se pudo conectar a Redis',
            'config': REDIS_CONFIG
        }), 500

@catalogos_bp.route('/products', methods=['POST'])
def add_product():
    """Añadir un nuevo producto"""
    if not redis_client:
        return jsonify({'error': 'Redis no disponible'}), 500
    
    try:
        data = request.get_json()
        
        # Validación básica
        if not data or 'name' not in data or 'price' not in data:
            return jsonify({'error': 'Se requieren name y price'}), 400
        
        # Crear ID único
        product_id = str(uuid.uuid4())
        product = {
            'id': product_id,
            'name': data['name'],
            'price': float(data['price']),
            'created_at': datetime.now().isoformat()
        }
        
        # Guardar en Redis
        redis_client.set(f'product:{product_id}', json.dumps(product))
        
        return jsonify({
            'message': 'Producto añadido correctamente',
            'product': product
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@catalogos_bp.route('/products')
def get_all_products():
    """Obtener todos los productos"""
    if not redis_client:
        return jsonify({'error': 'Redis no disponible'}), 500
    
    try:
        # Obtener todas las claves de productos
        product_keys = redis_client.keys('product:*')
        products = []
        
        for key in product_keys:
            product_data = redis_client.get(key)
            if product_data:
                products.append(json.loads(product_data))
        
        return jsonify({
            'count': len(products),
            'products': products
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@catalogos_bp.route('/products/<product_id>')
def get_product(product_id):
    """Obtener un producto específico"""
    if not redis_client:
        return jsonify({'error': 'Redis no disponible'}), 500
    
    try:
        product_data = redis_client.get(f'product:{product_id}')
        if not product_data:
            return jsonify({'error': 'Producto no encontrado'}), 404
            
        return jsonify(json.loads(product_data))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500