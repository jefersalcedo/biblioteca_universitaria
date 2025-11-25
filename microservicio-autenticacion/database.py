from sqlalchemy.orm import Session
from models import SessionLocal, Usuario
from passlib.context import CryptContext
import hashlib
import secrets

# CAMBIAR A PBKDF2 que no tiene límite de longitud
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    default="pbkdf2_sha256",
    pbkdf2_sha256__default_rounds=30000
)

def get_user_by_username(db: Session, username: str):
    return db.query(Usuario).filter(Usuario.username == username).first()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def initialize_database():
    """Inicializa la base de datos con datos de prueba"""
    from models import create_tables
    create_tables()
    
    db = SessionLocal()
    try:
        # ELIMINAR TODOS LOS USUARIOS EXISTENTES PRIMERO
        db.query(Usuario).delete()
        db.commit()
        
        # Crear usuarios de prueba - AHORA CON MÁS USUARIOS ESTÁTICOS
        usuarios_prueba = [
            Usuario(
                username="admin",
                email="admin@universidad.edu",
                password_hash=pwd_context.hash("admin123"),
                full_name="Administrador Principal",
                role="administrador"
            ),
            Usuario(
                username="profesor1", 
                email="profesor1@universidad.edu",
                password_hash=pwd_context.hash("profesor123"),
                full_name="Dr. Carlos Rodríguez",
                role="profesor"
            ),
            Usuario(
                username="profesor2",
                email="profesor2@universidad.edu", 
                password_hash=pwd_context.hash("profesor123"),
                full_name="Dra. María González",
                role="profesor"
            ),
            Usuario(
                username="estudiante1",
                email="estudiante1@universidad.edu", 
                password_hash=pwd_context.hash("estudiante123"),
                full_name="Ana López",
                role="estudiante"
            ),
            Usuario(
                username="estudiante2",
                email="estudiante2@universidad.edu", 
                password_hash=pwd_context.hash("estudiante123"),
                full_name="Juan Pérez",
                role="estudiante"
            ),
            Usuario(
                username="estudiante3",
                email="estudiante3@universidad.edu", 
                password_hash=pwd_context.hash("estudiante123"),
                full_name="Laura Martínez",
                role="estudiante"
            ),
            Usuario(
                username="estudiante4",
                email="estudiante4@universidad.edu", 
                password_hash=pwd_context.hash("estudiante123"),
                full_name="Pedro Sánchez",
                role="estudiante"
            ),
            Usuario(
                username="estudiante5",
                email="estudiante5@universidad.edu", 
                password_hash=pwd_context.hash("estudiante123"),
                full_name="Sofía Ramírez",
                role="estudiante"
            ),
            Usuario(
                username="bibliotecario",
                email="bibliotecario@universidad.edu", 
                password_hash=pwd_context.hash("bibliotecario123"),
                full_name="Roberto Castro",
                role="bibliotecario"
            )
        ]
        
        for usuario in usuarios_prueba:
            db.add(usuario)
        
        db.commit()
        print(f"✅ Base de datos inicializada con {len(usuarios_prueba)} usuarios de prueba")
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        db.rollback()
    finally:
        db.close()