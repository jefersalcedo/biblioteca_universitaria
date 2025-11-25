# Microservicio de Préstamos

## Descripción General

El microservicio de préstamos gestiona todo el ciclo de vida de los préstamos de libros, desde la solicitud hasta la devolución, incluyendo el cálculo de multas por retraso.

## Responsabilidades

    ✅ Crear préstamos de libros
    ✅ Devolver libros
    ✅ Renovar préstamos
    ✅ Calcular multas por retraso
    ✅ Historial de préstamos
    ✅ Reportes de préstamos activos

## Arquitectura del Servicio

```mermaid
graph TB
    subgraph "API Endpoints"
        EP1[POST /loans]
        EP2[GET /loans/:id]
        EP3[POST /loans/:id/return]
        EP4[POST /loans/:id/renew]
        EP5[GET /loans/user/:user_id]
    end
    
    subgraph "Business Logic"
        BL[Loans Service]
        CALC[Fine Calculator]
        VALID[Validator]
    end
    
    subgraph "External Services"
        AUTH[Auth Service]
        CAT[Catalog Service]
    end
    
    subgraph "Data Layer"
        MODELS[SQLAlchemy Models]
        DB[(PostgreSQL)]
    end
    
    EP1 & EP2 & EP3 & EP4 & EP5 --> BL
    BL --> CALC
    BL --> VALID
    BL --> AUTH
    BL --> CAT
    BL --> MODELS
    MODELS --> DB
    
    style EP1 fill:#e3f2fd
    style BL fill:#f3e5f5
    style DB fill:#c8e6c9
```

## Endpoints 

## Crear Préstamo

**Endpoint**: `POST /loans`

Crea un nuevo préstamo de libro.

**Request**
```json
{
  "user_id": 123,
  "book_id": "507f1f77bcf86cd799439011"
}
```

**Response**
```json
{
  "id": 1,
  "user_id": 123,
  "book_id": "507f1f77bcf86cd799439011",
  "loan_date": "2024-01-15",
  "due_date": "2024-01-30",
  "status": "active",
  "fine_amount": 0.00,
  "is_returned": false,
  "message": "Préstamo creado exitosamente"
}
```

## Flujo de Creación

```mermaid
sequenceDiagram
    participant U as Usuario
    participant API as Loans API
    participant AUTH as Auth Service
    participant CAT as Catalog Service
    participant DB as PostgreSQL
    
    U->>API: POST /loans
    API->>AUTH: Verificar usuario
    AUTH-->>API: Usuario válido
    API->>CAT: GET /books/:id
    CAT-->>API: Libro disponible
    API->>DB: INSERT préstamo
    DB-->>API: Préstamo creado
    API->>CAT: PATCH /books/:id/availability
    CAT-->>API: Disponibilidad actualizada
    API-->>U: 201 + Info préstamo
```

