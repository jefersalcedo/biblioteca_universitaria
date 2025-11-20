from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, EmailStr, Field
from pydantic_settings import BaseSettings
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List
import enum
import os

# ==================== CONFIGURACIÓN ====================

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("AUTH_DATABASE_URL", "postgresql://postgres:postgres@postgres_authentication:5432/authentication_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
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

class UserRole(str, enum.Enum):
    ESTUDIANTE = "estudiante"
    PROFESOR = "profesor"
    ADMINISTRADOR = "administrador"

user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    roles = relationship("Role", secondary=user_roles, back_populates="users")

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(UserRole), unique=True, nullable=False)
    description = Column(String)
    
    users = relationship("User", secondary=user_roles, back_populates="roles")

# ==================== ESQUEMAS ====================

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    roles: List[UserRole] = [UserRole.ESTUDIANTE]

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_active: bool
    roles: List[str]
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[UserRole]] = None

class UserListResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    roles: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ==================== SEGURIDAD ====================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def is_admin(user: dict) -> bool:
    """Verificar si el usuario es administrador"""
    return "administrador" in user.get("roles", [])

# ==================== CRUD ====================

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    
    # Asignar roles por defecto si no se especifican
    if not user.roles:
        user.roles = [UserRole.ESTUDIANTE]
    
    for role_name in user.roles:
        role = db.query(Role).filter(Role.name == role_name.value).first()
        if not role:
            # Crear el rol si no existe
            role = Role(name=role_name.value)
            db.add(role)
            db.flush()
        db_user.roles.append(role)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

# ==================== APP FASTAPI ====================

app = FastAPI(title="Auth Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar DB
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            # Crear roles primero
            for role_enum in UserRole:
                role = db.query(Role).filter(Role.name == role_enum.value).first()
                if not role:
                    role = Role(name=role_enum.value)
                    db.add(role)
            db.commit()
            
            # Crear admin con rol de administrador
            admin_data = UserCreate(
                username="admin",
                email="admin@biblioteca.com",
                password="Admin123!",
                full_name="Administrador del Sistema",
                roles=[UserRole.ADMINISTRADOR]
            )
            create_user(db, admin_data)
    finally:
        db.close()

# ==================== ENDPOINTS ====================

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Auth Service"}

@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario"""
    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="El usuario o email ya existe"
        )
    
    # Crear el usuario
    created_user = create_user(db, user)
    
    # Convertir roles de objetos a strings
    role_names = [role.name.value for role in created_user.roles]
    
    # Retornar con roles como strings
    return {
        "id": created_user.id,
        "username": created_user.username,
        "email": created_user.email,
        "full_name": created_user.full_name,
        "is_active": created_user.is_active,
        "roles": role_names
    }

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    
    access_token = create_access_token(data={"sub": user.id, "username": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    role_names = [role.name.value for role in current_user.roles]
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "roles": role_names
    }

@app.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(User).all()
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "roles": [role.name.value for role in user.roles]
        })
    return result

@app.post("/verify")
def verify_token(token: str, db: Session = Depends(get_db)):
    """Endpoint para que otros servicios verifiquen tokens"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "roles": [role.name.value for role in user.roles]
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== ENDPOINTS DE ADMINISTRACIÓN ====================

@app.get("/admin/users", response_model=List[UserListResponse])
async def listar_usuarios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    #Listar todos los usuarios (solo admins)
    user_roles = [role.name.value for role in current_user.roles]
    if "administrador" not in user_roles:
        raise HTTPException(status_code=403, detail="No tiene permisos de administrador")
    
    users = db.query(User).all()
    result = []
    
    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "roles": [role.name.value for role in user.roles],
            "created_at": user.created_at
        })
    
    return result

@app.get("/admin/users/{user_id}", response_model=UserListResponse)
async def obtener_usuario(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    #Obtener información de un usuario específico (solo admins)
    user_roles = [role.name.value for role in current_user.roles]
    if "administrador" not in user_roles:
        raise HTTPException(status_code=403, detail="No tiene permisos de administrador")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "roles": [role.name.value for role in user.roles],
        "created_at": user.created_at
    }

@app.put("/admin/users/{user_id}", response_model=UserListResponse)
async def actualizar_usuario(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    #Actualizar información de un usuario (solo admins)
    user_roles = [role.name.value for role in current_user.roles]
    if "administrador" not in user_roles:
        raise HTTPException(status_code=403, detail="No tiene permisos de administrador")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizar campos básicos
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    # Actualizar roles
    if user_update.roles is not None:
        # Limpiar roles actuales
        user.roles.clear()
        
        # Agregar nuevos roles
        for role_name in user_update.roles:
            role = db.query(Role).filter(Role.name == role_name.value).first()
            if not role:
                # Crear el rol si no existe
                role = Role(name=role_name.value)
                db.add(role)
                db.flush()
            user.roles.append(role)
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "roles": [role.name.value for role in user.roles],
        "created_at": user.created_at
    }

@app.delete("/admin/users/{user_id}")
async def eliminar_usuario(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un usuario (solo admins)"""
    user_roles = [role.name.value for role in current_user.roles]
    if "administrador" not in user_roles:
        raise HTTPException(status_code=403, detail="No tiene permisos de administrador")
    
    # No permitir que el admin se elimine a sí mismo
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(user)
    db.commit()
    
    return {"message": "Usuario eliminado exitosamente"}

@app.get("/roles")
def obtener_roles():
    """Obtener lista de roles disponibles"""
    return [
        {"value": "estudiante", "label": "Estudiante"},
        {"value": "profesor", "label": "Profesor"},
        {"value": "administrador", "label": "Administrador"}
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)