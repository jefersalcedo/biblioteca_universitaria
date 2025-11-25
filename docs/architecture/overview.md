# Visión General de la Arquitectura

## Introducción

El Sistema de PIGBU Biblioteca Universitaria implementa una **arquitectura de microservicios** que divide la aplicación en servicios independientes, cada uno con una responsabilidad específica y bien definida.

## Principios Arquitectónicos

### 1. Separación de Responsabilidades

Cada microservicio tiene una única responsabilidad bien definida:

- **Autenticación**: Gestión de usuarios y seguridad
- **Catálogo**: Información de libros y recursos
- **Préstamos**: Transacciones de préstamo y devolución
- **Reservas**: Sistema de reservas y cola de espera

### 2. Autonomía de Servicios

Los servicios son independientes y pueden:

- Desplegarse de forma independiente
- Escalar según necesidad
- Usar diferentes tecnologías
- Tener su propia base de datos

### 3. Comunicación por API

La comunicación entre componentes se realiza mediante:

- **HTTP/REST**: Para comunicación síncrona
- **JSON**: Como formato de intercambio de datos
- **JWT**: Para autenticación y autorización

## Diagrama de Arquitectura Completo

```mermaid
graph TB
    subgraph "Usuario Final"
        U[Navegador Web]
    end
    
    subgraph "Frontend Layer"
        FE[Flask Frontend<br/>Puerto 5000]
    end
    
    subgraph "API Gateway Layer"
        GW[API Gateway<br/>Puerto 8000]
        MW1[Middleware: CORS]
        MW2[Middleware: Auth]
        MW3[Middleware: Logging]
    end
    
    subgraph "Microservices Layer"
        AUTH[Auth Service<br/>Puerto 8001]
        CAT[Catalog Service<br/>Puerto 8002]
        LOAN[Loans Service<br/>Puerto 8003]
        RES[Reservations Service<br/>Puerto 8004]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Puerto 5432)]
        MONGO[(MongoDB<br/>Puerto 27017)]
        REDIS[(Redis<br/>Puerto 6379)]
    end
    
    subgraph "Container Orchestration"
        DOCKER[Docker Compose]
    end
    
    U -->|HTTPS| FE
    FE -->|REST API| GW
    GW --> MW1
    MW1 --> MW2
    MW2 --> MW3
    MW3 --> AUTH
    MW3 --> CAT
    MW3 --> LOAN
    MW3 --> RES
    
    AUTH ---|SQL| PG
    LOAN ---|SQL| PG
    CAT ---|NoSQL| MONGO
    RES ---|Cache| REDIS
    
    DOCKER -.->|Gestiona| FE
    DOCKER -.->|Gestiona| GW
    DOCKER -.->|Gestiona| AUTH
    DOCKER -.->|Gestiona| CAT
    DOCKER -.->|Gestiona| LOAN
    DOCKER -.->|Gestiona| RES
    DOCKER -.->|Gestiona| PG
    DOCKER -.->|Gestiona| MONGO
    DOCKER -.->|Gestiona| REDIS
    
    style U fill:#64b5f6
    style FE fill:#81c784
    style GW fill:#ffb74d
    style AUTH fill:#ba68c8
    style CAT fill:#4db6ac
    style LOAN fill:#f06292
    style RES fill:#fff176
    style PG fill:#90a4ae
    style MONGO fill:#a1887f
    style REDIS fill:#ef5350
```

## Capas del Sistema

### 1. Capa de Presentación

**Frontend con Flask**

Proporciona la interfaz de usuario web:

```
Frontend
├── Templates (HTML/Jinja2)
├── Static Assets (CSS/JS)
└── Lógica de Presentación
```

**Características**:

- Diseño responsivo con CSS moderno
- JavaScript vanilla para interactividad
- Integración con API Gateway
- Manejo de sesiones y tokens

### 2. Capa de Gateway

**API Gateway**

Punto de entrada único para todas las peticiones:

```python
# Ejemplo de configuración del Gateway
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Responsabilidades**:

- Enrutamiento de peticiones
- Autenticación centralizada
- Rate limiting
- Logging y monitoreo
- Manejo de errores global

### 3. Capa de Microservicios

Cada microservicio implementa lógica de negocio específica:

#### Servicio de Autenticación

```mermaid
sequenceDiagram
    participant U as Usuario
    participant GW as API Gateway
    participant AUTH as Auth Service
    participant DB as PostgreSQL
    
    U->>GW: POST /auth/login
    GW->>AUTH: Reenvía petición
    AUTH->>DB: Valida credenciales
    DB-->>AUTH: Usuario encontrado
    AUTH-->>AUTH: Genera JWT
    AUTH-->>GW: Token JWT
    GW-->>U: Token + Info Usuario
```

#### Servicio de Catálogo

```mermaid
sequenceDiagram
    participant U as Usuario
    participant GW as API Gateway
    participant CAT as Catalog Service
    participant DB as MongoDB
    
    U->>GW: GET /catalog/books?search=python
    GW->>CAT: Reenvía petición
    CAT->>DB: Busca libros
    DB-->>CAT: Lista de libros
    CAT-->>GW: JSON con resultados
    GW-->>U: Respuesta formateada
```

#### Servicio de Préstamos

```mermaid
sequenceDiagram
    participant U as Usuario
    participant GW as API Gateway
    participant LOAN as Loans Service
    participant DB as PostgreSQL
    participant CAT as Catalog Service
    
    U->>GW: POST /loans/create
    GW->>LOAN: Reenvía petición
    LOAN->>CAT: Verifica disponibilidad
    CAT-->>LOAN: Libro disponible
    LOAN->>DB: Crea préstamo
    DB-->>LOAN: Préstamo creado
    LOAN->>CAT: Actualiza disponibilidad
    LOAN-->>GW: Confirmación
    GW-->>U: Préstamo exitoso
```

#### Servicio de Reservas

```mermaid
sequenceDiagram
    participant U as Usuario
    participant GW as API Gateway
    participant RES as Reservations Service
    participant CACHE as Redis
    participant CAT as Catalog Service
    
    U->>GW: POST /reservations/create
    GW->>RES: Reenvía petición
    RES->>CAT: Verifica disponibilidad
    CAT-->>RES: No disponible
    RES->>CACHE: Añade a cola
    CACHE-->>RES: Posición en cola
    RES-->>GW: Reserva confirmada
    GW-->>U: Número en cola
```

### 4. Capa de Datos

El sistema utiliza múltiples tecnologías de almacenamiento:

=== "PostgreSQL"
    **Uso**: Datos transaccionales y relacionales
    
    - Usuarios y autenticación
    - Préstamos y devoluciones
    - Historial de transacciones
    
    **Ventajas**:
    - Relaciones complejas
    - Integridad referencial

=== "MongoDB"
    **Uso**: Documentos y datos no estructurados
    
    - Catálogo de libros
    - Metadatos bibliográficos
    - Búsquedas flexibles
    
    **Ventajas**:
    - Esquema flexible
    - Búsquedas de texto completo
    - Escalabilidad horizontal

=== "Redis"
    **Uso**: Caché y datos temporales
    
    - Cola de reservas
    - Sesiones activas
    - Caché de consultas
    
    **Ventajas**:
    - Acceso ultra rápido
    - Estructuras de datos avanzadas
    - Expiración automática


## Consideraciones de Seguridad

### Autenticación y Autorización

```mermaid
graph LR
    A[Usuario] -->|Credenciales| B[Login]
    B -->|JWT| C[Token]
    C -->|Header| D[Request]
    D -->|Valida| E[Gateway]
    E -->|OK| F[Microservicio]
    E -->|Fail| G[401 Unauthorized]
    
    style C fill:#4caf50
    style E fill:#ff9800
    style G fill:#f44336
```

### Principios Aplicados

1. **Autenticación en Gateway**: Validación centralizada de tokens
2. **JWT con Expiración**: Tokens de corta duración
3. **HTTPS**: Encriptación de datos en tránsito

## Escalabilidad

### Estrategias de Escalado

```mermaid
graph TB
    subgraph "Horizontal Scaling"
        LB[Load Balancer]
        MS1[Microservice Instance 1]
        MS2[Microservice Instance 2]
        MS3[Microservice Instance 3]
        
        LB --> MS1
        LB --> MS2
        LB --> MS3
    end
    
    subgraph "Database Scaling"
        MASTER[(Master DB)]
        REPLICA1[(Replica 1)]
        REPLICA2[(Replica 2)]
        
        MASTER -.->|Replication| REPLICA1
        MASTER -.->|Replication| REPLICA2
    end
    
    MS1 & MS2 & MS3 --> MASTER
    MS1 & MS2 & MS3 -.->|Read| REPLICA1 & REPLICA2
```


!!! info "Documentación de Microservicios"
    Para detalles específicos de cada microservicio, consulta la sección [Microservicios](../microservices/authentication.md).