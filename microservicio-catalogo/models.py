from pymongo import MongoClient
from pymongo.collection import Collection
import os
from typing import List, Dict, Any

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:admin123@mongodb:27017/")
print(f"🔗 Conectando a MongoDB: {MONGO_URI}")  # Para debug
client = MongoClient(MONGO_URI,serverSelectionTimeoutMS=5000)
db = client.biblioteca

# Colecciones
libros_collection: Collection = db.libros
autores_collection: Collection = db.autores
categorias_collection: Collection = db.categorias

def get_libros_collection():
    return libros_collection

def get_autores_collection():
    return autores_collection