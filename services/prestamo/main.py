from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from datetime import datetime, timedelta
from typing import Optional, List
import httpx
import os

# ==================== CONFIGURACIÓN ====================

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("PRESTAMOS_DATABASE_URL", "postgresql://postgres:postgres@postgres_prestamos:5432/prestamos_db")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth:8001")
    CATALOGOS_SERVICE_URL: str = os.getenv("CATALOGOS_SERVICE_URL", "http://catalogos:8002")
    
    class Config:
        env_file = ".env"

settings = Settings()

# ==================== BASE DE DATOS ====================

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== MODELOS ====================

class Prestamo(Base):
    __tablename__ = "prestamos"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    libro_id = Column(String, nullable=False)
    fecha_prestamo = Column(DateTime, default=datetime.utcnow)
    fecha_devolucion_esperada = Column(DateTime)
    fecha_devolucion_real = Column(DateTime, nullable=True)
    devuelto = Column(Boolean, default=False)
    multa = Column(Integer, default=0)  # En pesos

# ==================== ESQUEMAS ====================

class PrestamoCreate(BaseModel):
    libro_id: str

class PrestamoResponse(BaseModel):
    id: int
    user_id: int
    libro_id: str
    fecha_prestamo: datetime
    fecha_devolucion_esperada: datetime
    fecha_devolucion_real: Optional[datetime]
    devuelto: bool
    multa: int
    
    class Config:
        from_attributes = True

# ==================== APP FASTAPI ====================

app = FastAPI(title="Préstamos Service")

# Inicializar DB
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

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
    return {"status": "healthy", "service": "Prestamos Service"}

@app.post("/prestamos", response_model=PrestamoResponse, status_code=201)
async def crear_prestamo(
    prestamo: PrestamoCreate, 
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Verificar disponibilidad del libro en el servicio de catálogos
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.CATALOGOS_SERVICE_URL}/libros/{prestamo.libro_id}")
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Libro no encontrado")
            
            libro = response.json()
            if libro.get("cantidad_disponible", 0) <= 0:
                raise HTTPException(status_code=400, detail="Libro no disponible")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Servicio de catálogos no disponible")
    
    # Crear préstamo (15 días por defecto)
    db_prestamo = Prestamo(
        user_id=user["user_id"],
        libro_id=prestamo.libro_id,
        fecha_devolucion_esperada=datetime.utcnow() + timedelta(days=15)
    )
    
    db.add(db_prestamo)
    db.commit()
    db.refresh(db_prestamo)
    
    return db_prestamo

@app.get("/prestamos", response_model=List[PrestamoResponse])
async def listar_prestamos(
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Administradores ven todos, usuarios solo los suyos
    if "administrador" in user.get("roles", []):
        prestamos = db.query(Prestamo).all()
    else:
        prestamos = db.query(Prestamo).filter(Prestamo.user_id == user["user_id"]).all()
    
    return prestamos

@app.get("/prestamos/{prestamo_id}", response_model=PrestamoResponse)
async def obtener_prestamo(
    prestamo_id: int,
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    # Verificar permisos
    if prestamo.user_id != user["user_id"] and "administrador" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="No tiene permisos")
    
    return prestamo

@app.post("/prestamos/{prestamo_id}/devolver", response_model=PrestamoResponse)
async def devolver_prestamo(
    prestamo_id: int,
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    if prestamo.devuelto:
        raise HTTPException(status_code=400, detail="El préstamo ya fue devuelto")
    
    # Calcular multa si hay retraso
    now = datetime.utcnow()
    prestamo.fecha_devolucion_real = now
    prestamo.devuelto = True
    
    if now > prestamo.fecha_devolucion_esperada:
        dias_retraso = (now - prestamo.fecha_devolucion_esperada).days
        prestamo.multa = dias_retraso * 5000  # $5000 por día de retraso
    
    db.commit()
    db.refresh(prestamo)
    
    return prestamo

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)