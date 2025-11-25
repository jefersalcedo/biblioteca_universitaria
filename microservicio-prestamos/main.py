from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.orm import Session

# Importar nuestros módulos
from models import get_db, Prestamo, Reserva, create_tables
from database import initialize_database, calcular_multa

app = FastAPI(title="Microservicio de Préstamos")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EstadoPrestamo(str, Enum):
    ACTIVO = "activo"
    DEVUELTO = "devuelto"
    VENCIDO = "vencido"

class EstadoReserva(str, Enum):
    ACTIVA = "activa"
    CUMPLIDA = "cumplida"
    CANCELADA = "cancelada"
    VENCIDA = "vencida"

class PrestamoResponse(BaseModel):
    id: int
    usuario_id: int
    libro_id: int
    fecha_prestamo: datetime
    fecha_devolucion_esperada: datetime
    fecha_devolucion_real: Optional[datetime] = None
    estado: str
    multa: float = 0.0
    dias_retraso: int = 0

    class Config:
        orm_mode = True

class PrestamoCreate(BaseModel):
    usuario_id: int
    libro_id: int
    dias_prestamo: int = 15

class ReservaResponse(BaseModel):
    id: int
    usuario_id: int
    libro_id: int
    fecha_reserva: datetime
    fecha_vencimiento: datetime
    estado: str

    class Config:
        orm_mode = True

class ReservaCreate(BaseModel):
    usuario_id: int
    libro_id: int

# Inicializar base de datos al iniciar
@app.on_event("startup")
async def startup_event():
    print("🚀 Inicializando base de datos de préstamos...")
    initialize_database()
    print("✅ Base de datos de préstamos lista")

@app.get("/")
async def root():
    return {"message": "Microservicio de Préstamos funcionando"}

# PRÉSTAMOS
@app.post("/prestamos", response_model=PrestamoResponse)
async def crear_prestamo(prestamo_data: PrestamoCreate, db: Session = Depends(get_db)):
    try:
        fecha_prestamo = datetime.utcnow()
        fecha_devolucion = fecha_prestamo + timedelta(days=prestamo_data.dias_prestamo)
        
        prestamo = Prestamo(
            usuario_id=prestamo_data.usuario_id,
            libro_id=prestamo_data.libro_id,
            fecha_prestamo=fecha_prestamo,
            fecha_devolucion_esperada=fecha_devolucion,
            estado="activo"
        )
        
        db.add(prestamo)
        db.commit()
        db.refresh(prestamo)
        
        return prestamo
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando préstamo: {str(e)}")

@app.get("/prestamos", response_model=List[PrestamoResponse])
async def listar_prestamos(db: Session = Depends(get_db)):
    return db.query(Prestamo).all()

@app.get("/prestamos/usuario/{usuario_id}", response_model=List[PrestamoResponse])
async def obtener_prestamos_usuario(usuario_id: int, db: Session = Depends(get_db)):
    return db.query(Prestamo).filter(Prestamo.usuario_id == usuario_id).all()

@app.get("/prestamos/{prestamo_id}", response_model=PrestamoResponse)
async def obtener_prestamo(prestamo_id: int, db: Session = Depends(get_db)):
    prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    return prestamo

@app.post("/prestamos/{prestamo_id}/devolver")
async def devolver_libro(prestamo_id: int, db: Session = Depends(get_db)):
    prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    if prestamo.estado == "devuelto":
        raise HTTPException(status_code=400, detail="El libro ya fue devuelto")
    
    fecha_devolucion = datetime.utcnow()
    prestamo.fecha_devolucion_real = fecha_devolucion
    prestamo.estado = "devuelto"
    
    # Calcular multa si hay retraso
    multa, dias_retraso = calcular_multa(prestamo.fecha_devolucion_esperada, fecha_devolucion)
    prestamo.multa = multa
    prestamo.dias_retraso = dias_retraso
    
    db.commit()
    
    return {
        "message": "Libro devuelto exitosamente", 
        "multa": multa,
        "dias_retraso": dias_retraso
    }

# RESERVAS
@app.post("/reservas", response_model=ReservaResponse)
async def crear_reserva(reserva_data: ReservaCreate, db: Session = Depends(get_db)):
    try:
        fecha_reserva = datetime.utcnow()
        fecha_vencimiento = fecha_reserva + timedelta(days=7)  # 7 días para reserva
        
        reserva = Reserva(
            usuario_id=reserva_data.usuario_id,
            libro_id=reserva_data.libro_id,
            fecha_reserva=fecha_reserva,
            fecha_vencimiento=fecha_vencimiento,
            estado="activa"
        )
        
        db.add(reserva)
        db.commit()
        db.refresh(reserva)
        
        return reserva
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando reserva: {str(e)}")

@app.get("/reservas", response_model=List[ReservaResponse])
async def listar_reservas(db: Session = Depends(get_db)):
    return db.query(Reserva).all()

@app.get("/reservas/usuario/{usuario_id}", response_model=List[ReservaResponse])
async def obtener_reservas_usuario(usuario_id: int, db: Session = Depends(get_db)):
    return db.query(Reserva).filter(Reserva.usuario_id == usuario_id).all()

@app.post("/reservas/{reserva_id}/cancelar")
async def cancelar_reserva(reserva_id: int, db: Session = Depends(get_db)):
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if reserva.estado != "activa":
        raise HTTPException(status_code=400, detail="Solo se pueden cancelar reservas activas")
    
    reserva.estado = "cancelada"
    db.commit()
    
    return {"message": "Reserva cancelada exitosamente"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    total_prestamos = db.query(Prestamo).count()
    total_reservas = db.query(Reserva).count()
    return {
        "status": "healthy", 
        "service": "prestamos", 
        "total_prestamos": total_prestamos,
        "total_reservas": total_reservas
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)