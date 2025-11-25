from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import hashlib
import time
from sqlalchemy import text

# Importar nuestros módulos
from models import get_db, create_tables
from database import get_user_by_username, verify_password, initialize_database

app = FastAPI(title="Microservicio de Autenticación")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

def create_access_token(username: str, role: str):
    token_data = f"{username}_{role}_{time.time()}"
    return hashlib.sha256(token_data.encode()).hexdigest()

def wait_for_database(max_retries=30, delay=2):
    """Espera a que PostgreSQL esté disponible"""
    from models import SessionLocal
    
    for i in range(max_retries):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            print("✅ PostgreSQL está listo")
            return True
        except Exception as e:
            print(f"⏳ Esperando PostgreSQL... ({i+1}/{max_retries}) - {e}")
            time.sleep(delay)
    
    print("❌ No se pudo conectar a PostgreSQL después de varios intentos")
    return False

# Inicializar base de datos al iniciar
@app.on_event("startup")
async def startup_event():
    print("🚀 Inicializando base de datos...")
    initialize_database()
    print("✅ Base de datos lista")

@app.get("/")
async def root():
    return {"message": "Microservicio de Autenticación funcionando"}

@app.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    try:
        # Buscar usuario en la base de datos
        user_db = get_user_by_username(db, login_data.username)
        
        if not user_db:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # Verificar contraseña con bcrypt
        if not verify_password(login_data.password, user_db.password_hash):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # Crear token
        access_token = create_access_token(user_db.username, user_db.role)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_db.id,
                "username": user_db.username,
                "email": user_db.email,
                "role": user_db.role,
                "full_name": user_db.full_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/users/me")
async def read_users_me(token: str):
    # Por ahora mantenemos esta función simple
    return {"message": "Endpoint de usuario actual"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Verificar conexión a la base de datos
        db.execute("SELECT 1")
        return {
            "status": "healthy", 
            "service": "autenticacion",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "service": "autenticacion", 
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/test")
async def test(db: Session = Depends(get_db)):
    users = db.query(Usuario).all()
    return {
        "message": "Test exitoso", 
        "total_users": len(users),
        "users": [user.username for user in users]
    }

# Esto es importante para ejecución directa
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)