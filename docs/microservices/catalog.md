# Microservicio de Catálogo

## Descripción General

El microservicio de catálogo es responsable de gestionar toda la información bibliográfica del sistema, incluyendo libros, autores, categorías y disponibilidad.

## Responsabilidades

    ✅Gestión de libros 
    ✅Búsqueda y filtrado avanzado
    ✅Gestión de categorías
    ✅Control de disponibilidad
    ✅Información bibliográfica completa
    ✅Estadísticas del catálogo

## Arquitectura del Servicio

```mermaid
graph TB
    subgraph "API Endpoints"
        EP1[GET /books]
        EP2[GET /books/:id]
        EP3[POST /books]
        EP4[PUT /books/:id]
        EP5[DELETE /books/:id]
        EP6[GET /books/search]
    end
    
    subgraph "Business Logic"
        BL[Catalog Service]
        SEARCH[Search Engine]
        VALID[Validator]
    end
    
    subgraph "Data Layer"
        MODELS[Mongoose Models]
        DB[(MongoDB)]
    end
    
    EP1 & EP2 & EP3 & EP4 & EP5 & EP6 --> BL
    BL --> SEARCH
    BL --> VALID
    BL --> MODELS
    MODELS --> DB
    
    style EP1 fill:#e3f2fd
    style EP2 fill:#e3f2fd
    style EP3 fill:#e3f2fd
    style BL fill:#f3e5f5
    style DB fill:#c8e6c9
```

## Endpoints 

### Listar Todos los Libros

**Endpoint**: `GET /catalog/books`

Lista todos los libros con paginación.

**Query Parameters**:
```
page: int = 1          # Número de página
limit: int = 10        # Libros por página
category: str = None   # Filtrar por categoría
```

**Response** 
```json
{
  "total": 150,
  "page": 1,
  "limit": 10,
  "books": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "isbn": "978-3-16-148410-0",
      "title": "Clean Code",
      "author": "Robert C. Martin",
      "publisher": "Prentice Hall",
      "year": 2008,
      "category": "Programación",
      "description": "Guía de buenas prácticas",
      "total_copies": 5,
      "available_copies": 3,
      "is_available": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Flujo de Listado:

```mermaid
sequenceDiagram
    participant C as Cliente
    participant API as Catalog API
    participant DB as MongoDB
    
    C->>API: GET /books?page=1&limit=10
    API->>DB: find().skip(0).limit(10)
    DB-->>API: Lista de libros
    API->>API: Calcular total de páginas
    API-->>C: 200 + Libros + Metadata
```




