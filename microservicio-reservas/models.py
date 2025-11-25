from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class EstadoReserva(str, Enum):
    ACTIVA = "activa"
    CUMPLIDA = "cumplida"
    CANCELADA = "cancelada"
    VENCIDA = "vencida"
    EXPIRADA = "expirada"

class TipoNotificacion(str, Enum):
    VENCIMIENTO = "vencimiento"
    DISPONIBLE = "disponible"
    RECORDATORIO = "recordatorio"
    CANCELACION = "cancelacion"

# Modelos Pydantic para request/response
class ReservaCreate(BaseModel):
    usuario_id: int = Field(..., description="ID del usuario")
    libro_id: int = Field(..., description="ID del libro")
    dias_reserva: int = Field(default=7, description="Días de duración de la reserva")

class ReservaResponse(BaseModel):
    id: str
    usuario_id: int
    libro_id: int
    fecha_reserva: datetime
    fecha_vencimiento: datetime
    estado: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class NotificacionCreate(BaseModel):
    usuario_id: int
    tipo: TipoNotificacion
    mensaje: str
    reserva_id: Optional[str] = None

class NotificacionResponse(BaseModel):
    id: str
    usuario_id: int
    tipo: str
    mensaje: str
    reserva_id: Optional[str] = None
    leida: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class ReservaUpdate(BaseModel):
    estado: Optional[EstadoReserva] = None

# Modelos para MongoDB
class ReservaDocument:
    def __init__(self, usuario_id: int, libro_id: int, fecha_vencimiento: datetime):
        self.usuario_id = usuario_id
        self.libro_id = libro_id
        self.fecha_reserva = datetime.utcnow()
        self.fecha_vencimiento = fecha_vencimiento
        self.estado = EstadoReserva.ACTIVA
        self.created_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            "usuario_id": self.usuario_id,
            "libro_id": self.libro_id,
            "fecha_reserva": self.fecha_reserva,
            "fecha_vencimiento": self.fecha_vencimiento,
            "estado": self.estado,
            "created_at": self.created_at
        }