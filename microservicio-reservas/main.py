from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from bson import ObjectId

# Importar nuestros módulos de MongoDB
from database import get_database, initialize_database, calcular_fecha_vencimiento, verificar_reserva_activa, crear_notificacion
from models import EstadoReserva, TipoNotificacion, ReservaDocument

app = FastAPI(title="Microservicio de Reservas")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EstadoReserva(str, Enum):
    ACTIVA = "activa"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"
    VENCIDA = "vencida"

class ReservaCreate(BaseModel):
    usuario_id: int
    libro_id: int
    dias_reserva: int = 3

class ReservaResponse(BaseModel):
    id: str
    usuario_id: int
    libro_id: int
    fecha_reserva: datetime
    fecha_vencimiento: datetime
    estado: str
    notificado: bool = False

class NotificacionResponse(BaseModel):
    id: str
    usuario_id: int
    tipo: str
    mensaje: str
    reserva_id: Optional[str] = None
    leida: bool
    fecha_creacion: datetime

# Tarea en segundo plano para verificar reservas vencidas
async def verificar_reservas_vencidas():
    """Tarea periódica para verificar y actualizar reservas vencidas"""
    while True:
        try:
            db = get_database()
            fecha_actual = datetime.utcnow()
            
            # Buscar reservas activas que hayan vencido
            reservas_vencidas = db.reservas.find({
                "estado": EstadoReserva.ACTIVA,
                "fecha_vencimiento": {"$lt": fecha_actual}
            })
            
            for reserva in reservas_vencidas:
                # Actualizar estado a vencida
                db.reservas.update_one(
                    {"_id": reserva["_id"]},
                    {"$set": {"estado": EstadoReserva.VENCIDA, "notificado": True}}
                )
                
                # Crear notificación de vencimiento
                crear_notificacion(
                    db,
                    reserva["usuario_id"],
                    TipoNotificacion.VENCIMIENTO,
                    f"Tu reserva del libro ID {reserva['libro_id']} ha vencido",
                    str(reserva["_id"])
                )
                
                print(f"📅 Reserva {reserva['_id']} marcada como vencida")
            
            await asyncio.sleep(3600)  # Verificar cada hora
            
        except Exception as e:
            print(f"Error en verificación de reservas vencidas: {e}")
            await asyncio.sleep(300)

# Inicializar base de datos al iniciar
@app.on_event("startup")
async def startup_event():
    print("🚀 Inicializando microservicio de reservas con MongoDB...")
    initialize_database()
    print("✅ Base de datos de reservas lista")
    
    # Iniciar tarea en segundo plano
    asyncio.create_task(verificar_reservas_vencidas())

@app.get("/")
async def root():
    return {"message": "Microservicio de Reservas funcionando con MongoDB"}

@app.post("/reservas", response_model=ReservaResponse)
async def crear_reserva(reserva_data: ReservaCreate, background_tasks: BackgroundTasks):
    db = get_database()
    
    try:
        print(f"📝 Creando reserva para usuario {reserva_data.usuario_id}, libro {reserva_data.libro_id}")
        
        # Verificar si ya existe una reserva activa para el mismo libro y usuario
        if verificar_reserva_activa(db, reserva_data.usuario_id, reserva_data.libro_id):
            raise HTTPException(
                status_code=400, 
                detail="Ya tienes una reserva activa para este libro"
            )
        
        # Calcular fecha de vencimiento
        fecha_vencimiento = calcular_fecha_vencimiento(reserva_data.dias_reserva)
        
        # Crear reserva
        reserva_doc = ReservaDocument(
            usuario_id=reserva_data.usuario_id,
            libro_id=reserva_data.libro_id,
            fecha_vencimiento=fecha_vencimiento
        )
        
        # Convertir a dict y agregar campo notificado
        reserva_dict = reserva_doc.to_dict()
        reserva_dict["notificado"] = False
        
        result = db.reservas.insert_one(reserva_dict)
        
        # Obtener la reserva creada
        reserva_creada = db.reservas.find_one({"_id": result.inserted_id})
        
        # Crear notificación de reserva exitosa
        crear_notificacion(
            db,
            reserva_data.usuario_id,
            TipoNotificacion.RECORDATORIO,
            f"Reserva creada exitosamente para el libro ID {reserva_data.libro_id}. Vence el {fecha_vencimiento.strftime('%d/%m/%Y')}",
            str(result.inserted_id)
        )
        
        print(f"✅ Reserva creada exitosamente: {result.inserted_id}")
        
        return {
            "id": str(reserva_creada["_id"]),
            "usuario_id": reserva_creada["usuario_id"],
            "libro_id": reserva_creada["libro_id"],
            "fecha_reserva": reserva_creada["fecha_reserva"],
            "fecha_vencimiento": reserva_creada["fecha_vencimiento"],
            "estado": reserva_creada["estado"],
            "notificado": reserva_creada["notificado"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creando reserva: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creando reserva: {str(e)}")

@app.get("/reservas", response_model=List[ReservaResponse])
async def listar_reservas():
    db = get_database()
    
    reservas = db.reservas.find().sort("fecha_reserva", -1)
    
    return [
        {
            "id": str(reserva["_id"]),
            "usuario_id": reserva["usuario_id"],
            "libro_id": reserva["libro_id"],
            "fecha_reserva": reserva["fecha_reserva"],
            "fecha_vencimiento": reserva["fecha_vencimiento"],
            "estado": reserva["estado"],
            "notificado": reserva.get("notificado", False)
        }
        for reserva in reservas
    ]

@app.get("/reservas/usuario/{usuario_id}", response_model=List[ReservaResponse])
async def obtener_reservas_usuario(usuario_id: int):
    db = get_database()
    
    print(f"📋 Obteniendo reservas para usuario: {usuario_id}")
    
    reservas = db.reservas.find({"usuario_id": usuario_id}).sort("fecha_reserva", -1)
    reservas_list = list(reservas)
    
    print(f"✅ Encontradas {len(reservas_list)} reservas para usuario {usuario_id}")
    
    return [
        {
            "id": str(reserva["_id"]),
            "usuario_id": reserva["usuario_id"],
            "libro_id": reserva["libro_id"],
            "fecha_reserva": reserva["fecha_reserva"],
            "fecha_vencimiento": reserva["fecha_vencimiento"],
            "estado": reserva["estado"],
            "notificado": reserva.get("notificado", False)
        }
        for reserva in reservas_list
    ]

@app.get("/reservas/{reserva_id}", response_model=ReservaResponse)
async def obtener_reserva(reserva_id: str):
    db = get_database()
    
    try:
        reserva = db.reservas.find_one({"_id": ObjectId(reserva_id)})
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        return {
            "id": str(reserva["_id"]),
            "usuario_id": reserva["usuario_id"],
            "libro_id": reserva["libro_id"],
            "fecha_reserva": reserva["fecha_reserva"],
            "fecha_vencimiento": reserva["fecha_vencimiento"],
            "estado": reserva["estado"],
            "notificado": reserva.get("notificado", False)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail="ID de reserva inválido")

@app.post("/reservas/{reserva_id}/cancelar")
async def cancelar_reserva(reserva_id: str):
    db = get_database()
    
    try:
        reserva = db.reservas.find_one({"_id": ObjectId(reserva_id)})
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        if reserva["estado"] != EstadoReserva.ACTIVA:
            raise HTTPException(status_code=400, detail="Solo se pueden cancelar reservas activas")
        
        # Actualizar estado
        db.reservas.update_one(
            {"_id": ObjectId(reserva_id)},
            {"$set": {"estado": EstadoReserva.CANCELADA, "notificado": True}}
        )
        
        # Crear notificación de cancelación
        crear_notificacion(
            db,
            reserva["usuario_id"],
            TipoNotificacion.CANCELACION,
            f"Tu reserva del libro ID {reserva['libro_id']} ha sido cancelada",
            reserva_id
        )
        
        print(f"✅ Reserva {reserva_id} cancelada exitosamente")
        
        return {"message": "Reserva cancelada exitosamente"}
        
    except Exception as e:
        print(f"❌ Error cancelando reserva: {str(e)}")
        raise HTTPException(status_code=400, detail="ID de reserva inválido")

# NUEVOS ENDPOINTS PARA NOTIFICACIONES
@app.get("/notificaciones/usuario/{usuario_id}", response_model=List[NotificacionResponse])
async def obtener_notificaciones_usuario(usuario_id: int):
    db = get_database()
    
    notificaciones = db.notificaciones.find({"usuario_id": usuario_id}).sort("fecha_creacion", -1)
    
    return [
        {
            "id": str(notif["_id"]),
            "usuario_id": notif["usuario_id"],
            "tipo": notif["tipo"],
            "mensaje": notif["mensaje"],
            "reserva_id": notif.get("reserva_id"),
            "leida": notif["leida"],
            "fecha_creacion": notif["fecha_creacion"]
        }
        for notif in notificaciones
    ]

@app.post("/notificaciones/{notificacion_id}/leer")
async def marcar_notificacion_leida(notificacion_id: str):
    db = get_database()
    
    try:
        result = db.notificaciones.update_one(
            {"_id": ObjectId(notificacion_id)},
            {"$set": {"leida": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Notificación no encontrada")
        
        return {"message": "Notificación marcada como leída"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail="ID de notificación inválido")

@app.get("/health")
async def health_check():
    db = get_database()
    
    try:
        # Verificar conexión a MongoDB
        db.command("ping")
        
        total_reservas = db.reservas.count_documents({})
        reservas_activas = db.reservas.count_documents({"estado": EstadoReserva.ACTIVA})
        
        return {
            "status": "healthy", 
            "service": "reservas", 
            "database": "MongoDB",
            "total_reservas": total_reservas,
            "reservas_activas": reservas_activas
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "reservas", 
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)