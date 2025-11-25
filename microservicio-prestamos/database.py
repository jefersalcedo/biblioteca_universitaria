from sqlalchemy.orm import Session
from models import SessionLocal, Prestamo, Reserva, create_tables
from datetime import datetime, timedelta

def initialize_database():
    """Inicializa la base de datos con tablas de préstamos y reservas"""
    create_tables()
    
    db = SessionLocal()
    try:
        # Verificar si ya existen datos
        if db.query(Prestamo).count() == 0:
            print("✅ Tablas de préstamos y reservas creadas correctamente")
        else:
            print("✅ Base de datos de préstamos ya contiene datos")
            
    except Exception as e:
        print(f"❌ Error inicializando base de datos de préstamos: {e}")
        db.rollback()
    finally:
        db.close()

def calcular_multa(fecha_devolucion_esperada, fecha_devolucion_real):
    """Calcula la multa por retraso en la devolución"""
    if fecha_devolucion_real > fecha_devolucion_esperada:
        dias_retraso = (fecha_devolucion_real - fecha_devolucion_esperada).days
        multa = dias_retraso * 2.0  # $2 por día de retraso
        return multa, dias_retraso
    return 0.0, 0