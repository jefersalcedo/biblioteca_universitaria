# Microservicio de Reservas

## Descripción General

El microservicio de reservas gestiona la cola de espera para libros que no están disponibles, notificando a los usuarios cuando el libro que reservaron está disponible nuevamente.

## Responsabilidades

    ✅Crear reservas para libros no disponibles
    ✅Notificar cuando libro esté disponible
    ✅Cancelar reservas
    ✅Expiración automática de reservas
    ✅Estadísticas de reservas

## Arquitectura del Servicio

```mermaid
graph TB
    subgraph "API Endpoints"
        EP1[POST /reservations]
        EP2[GET /reservations/:id]
        EP3[DELETE /reservations/:id]
        EP4[GET /reservations/user/:user_id]
        EP5[POST /reservations/:id/notify]
    end
    
    subgraph "Business Logic"
        BL[Reservations Service]
        QUEUE[Queue Manager]
        NOTIF[Notification Service]
    end
    
    subgraph "External Services"
        AUTH[Auth Service]
        CAT[Catalog Service]
    end
    
    subgraph "Data Layer"
        CACHE[(Redis)]
    end
    
    EP1 & EP2 & EP3 & EP4 & EP5 --> BL
    BL --> QUEUE
    BL --> NOTIF
    BL --> AUTH
    BL --> CAT
    BL --> CACHE
    
    style EP1 fill:#e3f2fd
    style BL fill:#f3e5f5
    style CACHE fill:#ffecb3
```

## Endpoints 

### Crear Reserva

**Endpoint**: `POST /reservations`

Crea una nueva reserva para un libro no disponible.

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
  "reservation_id": "res_1705329600_123",
  "user_id": 123,
  "book_id": "507f1f77bcf86cd799439011",
  "book_title": "Clean Code",
  "reservation_date": "2024-01-15T10:30:00Z",
  "status": "pending",
  "position_in_queue": 3,
  "estimated_wait_days": 45,
  "message": "Reserva creada exitosamente. Eres el número 3 en la cola."
}
```

## Flujo de Creación

```mermaid
sequenceDiagram
    participant U as Usuario
    participant API as Reservations API
    participant CAT as Catalog Service
    participant REDIS as Redis
    
    U->>API: POST /reservations
    API->>CAT: GET /books/:id
    CAT-->>API: Libro NO disponible
    API->>REDIS: LLEN book:queue:{book_id}
    REDIS-->>API: 2 en cola
    API->>REDIS: RPUSH book:queue:{book_id}
    API->>REDIS: SET reservation:{id}
    REDIS-->>API: Guardado
    API-->>U: 201 + Posición: 3
```

