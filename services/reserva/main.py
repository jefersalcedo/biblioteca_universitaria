from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Optional, List
import redis
import json
import httpx
import os
from datetime import datetime, timedelta

# ==================== CONFIGURACIÓN ====================

class Settings(BaseSettings):
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://:redis123@redis_reservas:6379/0")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth:8001")
    CATALOGOS_SERVICE_URL: str = os.getenv("CATALOGOS_SERVICE_URL", "http://catalogos:8002")
    
    class Config:
        env_file = ".env"

settings = Settings()

# ==================== CONEXIÓN REDIS ====================

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# ==================== ESQUEMAS ====================

class ReservaCreate(BaseModel):
    libro_id: str

class ReservaResponse(BaseModel):
    id: str
    user_id: int
    libro_id: str
    fecha_reserva: str
    fecha_expiracion: str
    activa: bool

# ==================== APP FASTAPI ====================

app = FastAPI(title="Reservas Service")

# ==================== DEPENDENCIAS ====================

async def verify_token(authorization: Optional[str] = Header(None)):
    """Verifica el token con el servicio de autenticación"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    try:
        token = authorization.replace("Bearer ", "")
        async with httpx.AsyncClient() as client:
            response = await client.post(
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
    return {"status": "healthy", "service": "Reservas Service"}

@app.post("/reservas", response_model=ReservaResponse, status_code=201)
async def crear_reserva(
    reserva: ReservaCreate,
    user=Depends(verify_token)
):
    # Verificar que el libro existe
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.CATALOGOS_SERVICE_URL}/libros/{reserva.libro_id}")
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Libro no encontrado")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Servicio de catálogos no disponible")
    
    # Crear ID único para la reserva
    reserva_id = f"reserva:{user['user_id']}:{reserva.libro_id}:{datetime.utcnow().timestamp()}"
    
    # Datos de la reserva
    fecha_reserva = datetime.utcnow()
    fecha_expiracion = fecha_reserva + timedelta(days=3)  # 3 días de validez
    
    reserva_data = {
        "id": reserva_id,
        "user_id": user["user_id"],
        "libro_id": reserva.libro_id,
        "fecha_reserva": fecha_reserva.isoformat(),
        "fecha_expiracion": fecha_expiracion.isoformat(),
        "activa": True
    }
    
    # Guardar en Redis con expiración
    redis_client.setex(
        reserva_id,
        timedelta(days=3),
        json.dumps(reserva_data)
    )
    
    return reserva_data

@app.get("/reservas", response_model=List[ReservaResponse])
async def listar_reservas(user=Depends(verify_token)):
    reservas = []
    
    # Buscar todas las reservas del usuario
    pattern = f"reserva:{user['user_id']}:*"
    keys = redis_client.keys(pattern)
    
    for key in keys:
        data = redis_client.get(key)
        if data:
            reserva = json.loads(data)
            # Verificar si está activa (no expirada)
            fecha_exp = datetime.fromisoformat(reserva["fecha_expiracion"])
            reserva["activa"] = datetime.utcnow() < fecha_exp
            reservas.append(reserva)
    
    return reservas

@app.get("/reservas/{reserva_id}", response_model=ReservaResponse)
async def obtener_reserva(
    reserva_id: str,
    user=Depends(verify_token)
):
    data = redis_client.get(reserva_id)
    
    if not data:
        raise HTTPException(status_code=404, detail="Reserva no encontrada o expirada")
    
    reserva = json.loads(data)
    
    # Verificar permisos
    if reserva["user_id"] != user["user_id"] and "administrador" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="No tiene permisos")
    
    # Verificar si está activa
    fecha_exp = datetime.fromisoformat(reserva["fecha_expiracion"])
    reserva["activa"] = datetime.utcnow() < fecha_exp
    
    return reserva

@app.delete("/reservas/{reserva_id}")
async def cancelar_reserva(
    reserva_id: str,
    user=Depends(verify_token)
):
    data = redis_client.get(reserva_id)
    
    if not data:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    reserva = json.loads(data)
    
    # Verificar permisos
    if reserva["user_id"] != user["user_id"] and "administrador" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="No tiene permisos")
    
    redis_client.delete(reserva_id)
    
    return {"message": "Reserva cancelada"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)