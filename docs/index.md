# Sistema de Biblioteca Universitaria

¡Bienvenido a la documentación del Sistema de PIGBU Biblioteca Universitaria!

## Arquitectura del Sistema
```mermaid
graph TB
    Frontend[Frontend Flask] --> Gateway[API Gateway]
    Gateway --> Auth[Autenticación]
    Gateway --> Catalog[Catálogo]
    Gateway --> Loans[Préstamos]
    Gateway --> Reservations[Reservas]
    
    Auth --> PG[(PostgreSQL)]
    Catalog --> Mongo[(MongoDB)]
    Loans --> PG
    Reservations --> Redis[(Redis)]
```

## Características

- ✅ Autenticación con JWT
- ✅ Catálogo de libros
- ✅ Sistema de préstamos
- ✅ Reservas con cola

## Inicio 
Crea las imagenes de contenedores

```bash
docker-compose build --no-cache
```
Levanta el servicio 

```bash
docker-compose up
```

Accede a: http://localhost:5000
