from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
import json
import time
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


# Importar nuestros módulos
from models import get_libros_collection, get_autores_collection
from database import inicializar_datos

app = FastAPI(title="Microservicio de Catálogo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def wait_for_mongodb(max_retries=30, delay=2):
    """Espera a que MongoDB esté disponible"""
    from models import client
    
    for i in range(max_retries):
        try:
            # Intentar conectar a MongoDB
            client.admin.command('ping')
            print("✅ MongoDB está listo")
            return True
        except ServerSelectionTimeoutError:
            print(f"⏳ Esperando MongoDB... ({i+1}/{max_retries})")
            time.sleep(delay)
        except Exception as e:
            print(f"⏳ Error conectando a MongoDB... ({i+1}/{max_retries}) - {e}")
            time.sleep(delay)
    
    print("❌ No se pudo conectar a MongoDB después de varios intentos")
    return False


# Inicializar base de datos al iniciar
@app.on_event("startup")
async def startup_event():
    print("🚀 Inicializando base de datos MongoDB...")
    
    # ESPERAR A QUE MONGODB ESTÉ LISTO
    if wait_for_mongodb():
        inicializar_datos()
        print("✅ Base de datos lista")
    else:
        print("❌ No se pudo inicializar la base de datos")
# Modelos Pydantic
class LibroResponse(BaseModel):
    id: int
    titulo: str
    autor: str
    autor_id: int
    categoria: str
    isbn: str
    año_publicacion: int
    editorial: str
    ejemplares_disponibles: int
    ejemplares_totales: int
    descripcion: Optional[str] = None

class AutorResponse(BaseModel):
    id: int
    nombre: str
    nacionalidad: str

# JSON encoder para ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

# Inicializar base de datos al iniciar
@app.on_event("startup")
async def startup_event():
    print("🚀 Inicializando base de datos MongoDB...")
    inicializar_datos()
    print("✅ Base de datos lista")

@app.get("/")
async def root():
    return {"message": "Microservicio de Catálogo funcionando"}

@app.get("/libros", response_model=List[LibroResponse])
async def listar_libros(
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    autor: Optional[str] = Query(None, description="Filtrar por autor"),
    search: Optional[str] = Query(None, description="Buscar en título")
):
    collection = get_libros_collection()
    query = {}
    
    if categoria:
        query["categoria"] = categoria
    if autor:
        query["autor"] = autor
    if search:
        query["titulo"] = {"$regex": search, "$options": "i"}
    
    libros = list(collection.find(query))
    
    # Convertir _id de MongoDB a id numérico
    for libro in libros:
        libro["id"] = libro["_id"]
        del libro["_id"]
    
    return libros

@app.get("/libros/{libro_id}", response_model=LibroResponse)
async def obtener_libro(libro_id: int):
    collection = get_libros_collection()
    libro = collection.find_one({"_id": libro_id})
    
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    libro["id"] = libro["_id"]
    del libro["_id"]
    return libro

@app.get("/autores", response_model=List[AutorResponse])
async def listar_autores():
    collection = get_autores_collection()
    autores = list(collection.find())
    
    for autor in autores:
        autor["id"] = autor["_id"]
        del autor["_id"]
    
    return autores

@app.get("/autores/{autor_id}", response_model=AutorResponse)
async def obtener_autor(autor_id: int):
    collection = get_autores_collection()
    autor = collection.find_one({"_id": autor_id})
    
    if not autor:
        raise HTTPException(status_code=404, detail="Autor no encontrado")
    
    autor["id"] = autor["_id"]
    del autor["_id"]
    return autor

@app.get("/categorias")
async def listar_categorias():
    collection = get_libros_collection()
    categorias = collection.distinct("categoria")
    return {"categorias": categorias}

@app.get("/health")
async def health_check():
    collection = get_libros_collection()
    total_libros = collection.count_documents({})
    return {
        "status": "healthy", 
        "service": "catalogo", 
        "total_libros": total_libros
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)