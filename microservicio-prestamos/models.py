from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import os

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin123@localhost:5432/biblioteca")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Prestamo(Base):
    __tablename__ = "prestamos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False)
    libro_id = Column(Integer, nullable=False)
    fecha_prestamo = Column(DateTime, default=datetime.utcnow)
    fecha_devolucion_esperada = Column(DateTime, nullable=False)
    fecha_devolucion_real = Column(DateTime, nullable=True)
    estado = Column(String(20), default="activo")  # activo, devuelto, vencido
    multa = Column(Float, default=0.0)
    dias_retraso = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False)
    libro_id = Column(Integer, nullable=False)
    fecha_reserva = Column(DateTime, default=datetime.utcnow)
    fecha_vencimiento = Column(DateTime, nullable=False)
    estado = Column(String(20), default="activa")  # activa, cumplida, cancelada, vencida
    created_at = Column(DateTime, default=datetime.utcnow)

# Crear tablas
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()