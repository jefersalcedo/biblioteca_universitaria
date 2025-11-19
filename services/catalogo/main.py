from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from pymongo import MongoClient
from bson import ObjectId
from typing import List, Optional
import httpx
import os

# ==================== CONFIGURACIÓN ====================

class Settings(BaseSettings):
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://admin:admin123@mongodb_catalogos:27017/catalogos_db?authSource=admin")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://authentication:8001")
    
    class Config:
        env_file = ".env"

settings = Settings()

# ==================== BASE DE DATOS ====================

client = MongoClient(settings.MONGODB_URL)
db = client.catalogos_db

# ==================== ESQUEMAS ====================

class LibroCreate(BaseModel):
    titulo: str
    isbn: str
    autor: str
    editorial: str
    anio: int  # ← CAMBIADO de 'año' a 'anio'
    categoria: str
    cantidad_disponible: int = 0

class LibroResponse(BaseModel):
    id: str
    titulo: str
    isbn: str
    autor: str
    editorial: str
    anio: int  # ← CAMBIADO de 'año' a 'anio'
    categoria: str
    cantidad_disponible: int

# ==================== APP FASTAPI ====================

app = FastAPI(title="Catálogos Service")

# ==================== DEPENDENCIAS ====================

async def verify_token(authorization: Optional[str] = Header(None)):
    """Verifica el token con el servicio de autenticación"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    try:
        token = authorization.replace("Bearer ", "")
        async with httpx.AsyncClient() as client_http:
            response = await client_http.post(
                f"{settings.AUTH_SERVICE_URL}/verify",
                params={"token": token}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

# ==================== ENDPOINTS ====================

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Catalogos Service"}

@app.post("/libros", response_model=LibroResponse, status_code=201)
async def crear_libro(libro: LibroCreate, user=Depends(verify_token)):
    libro_dict = libro.dict()
    result = db.libros.insert_one(libro_dict)
    libro_dict["id"] = str(result.inserted_id)
    return libro_dict

@app.get("/libros", response_model=List[LibroResponse])
def listar_libros(skip: int = 0, limit: int = 100):
    libros = []
    for libro in db.libros.find().skip(skip).limit(limit):
        libro["id"] = str(libro.pop("_id"))
        libros.append(libro)
    return libros

@app.get("/libros/{libro_id}", response_model=LibroResponse)
def obtener_libro(libro_id: str):
    libro = db.libros.find_one({"_id": ObjectId(libro_id)})
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    libro["id"] = str(libro.pop("_id"))
    return libro

@app.put("/libros/{libro_id}", response_model=LibroResponse)
async def actualizar_libro(libro_id: str, libro: LibroCreate, user=Depends(verify_token)):
    result = db.libros.update_one(
        {"_id": ObjectId(libro_id)},
        {"$set": libro.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return obtener_libro(libro_id)

@app.delete("/libros/{libro_id}")
async def eliminar_libro(libro_id: str, user=Depends(verify_token)):
    result = db.libros.delete_one({"_id": ObjectId(libro_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return {"message": "Libro eliminado"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)