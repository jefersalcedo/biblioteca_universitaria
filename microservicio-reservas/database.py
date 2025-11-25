from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from datetime import datetime, timedelta

# Configuración de MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
DB_NAME = "biblioteca_reservas"

def get_database():
    """Obtiene la conexión a la base de datos MongoDB"""
    try:
        client = MongoClient(MONGO_URL)
        # Verificar conexión
        client.admin.command('ping')
        print("✅ Conectado a MongoDB exitosamente")
        return client[DB_NAME]
    except ConnectionFailure as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        raise

def initialize_database():
    """Inicializa la base de datos con colecciones e índices"""
    db = get_database()
    
    # Crear colecciones si no existen
    collections = db.list_collection_names()
    
    # Colección de reservas
    if "reservas" not in collections:
        db.create_collection("reservas")
        print("✅ Colección 'reservas' creada")
    
    # Colección de notificaciones
    if "notificaciones" not in collections:
        db.create_collection("notificaciones")
        print("✅ Colección 'notificaciones' creada")
    
    # Crear índices para mejor performance
    db.reservas.create_index([("usuario_id", 1)])
    db.reservas.create_index([("libro_id", 1)])
    db.reservas.create_index([("estado", 1)])
    db.reservas.create_index([("fecha_vencimiento", 1)])
    
    db.notificaciones.create_index([("usuario_id", 1)])
    db.notificaciones.create_index([("fecha_creacion", 1)])
    
    print("✅ Índices creados correctamente")
    return db

def calcular_fecha_vencimiento(dias_reserva=7):
    """Calcula la fecha de vencimiento de la reserva"""
    return datetime.utcnow() + timedelta(days=dias_reserva)

def verificar_reserva_activa(db, usuario_id, libro_id):
    """Verifica si el usuario ya tiene una reserva activa para el mismo libro"""
    reserva = db.reservas.find_one({
        "usuario_id": usuario_id,
        "libro_id": libro_id,
        "estado": "activa"
    })
    return reserva is not None

def crear_notificacion(db, usuario_id, tipo, mensaje, reserva_id=None):
    """Crea una notificación para el usuario"""
    notificacion = {
        "usuario_id": usuario_id,
        "tipo": tipo,  # "vencimiento", "disponible", "recordatorio"
        "mensaje": mensaje,
        "reserva_id": reserva_id,
        "leida": False,
        "fecha_creacion": datetime.utcnow()
    }
    
    db.notificaciones.insert_one(notificacion)
    return notificacion