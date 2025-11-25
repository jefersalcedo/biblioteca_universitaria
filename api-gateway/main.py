from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import json

app = FastAPI(title="API Gateway - Biblioteca Universitaria")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de servicios - CORREGIDA
SERVICES = {
    "autenticacion": "http://microservicio-autenticacion:8001",
    "catalogo": "http://microservicio-catalogo:8001",  # Cambiado de 8002 a 8001
    "prestamos": "http://microservicio-prestamos:8003",
    "reservas": "http://microservicio-reservas:8004"
}

@app.get("/")
async def root():
    return {
        "message": "API Gateway - Sistema de Biblioteca Universitaria",
        "services": list(SERVICES.keys())
    }

@app.api_route("/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(service_name: str, path: str, request: Request):
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Servicio {service_name} no encontrado")
    
    # Construir URL destino
    base_url = SERVICES[service_name]
    target_url = f"{base_url}/{path}"
    
    # Headers
    headers = {key: value for key, value in request.headers.items() 
               if key.lower() not in ["host", "content-length"]}
    
    # Body
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    # Realizar petición
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
                timeout=30.0
            )
            
            # Manejar diferentes tipos de respuesta
            if response.status_code == 204:  # No Content
                return JSONResponse(content={}, status_code=response.status_code)
            
            try:
                response_data = response.json()
                return JSONResponse(content=response_data, status_code=response.status_code)
            except json.JSONDecodeError:
                # Si no es JSON, devolver el texto
                return JSONResponse(
                    content={"detail": response.text},
                    status_code=response.status_code
                )
                
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503, 
                detail=f"Servicio {service_name} no disponible. No se puede conectar."
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, 
                detail=f"Timeout en servicio {service_name}. El servicio no respondió a tiempo."
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error interno del gateway: {str(e)}"
            )

@app.get("/health")
async def health_check():
    health_status = {"gateway": "healthy"}
    
    async with httpx.AsyncClient() as client:
        for service_name, url in SERVICES.items():
            try:
                response = await client.get(f"{url}/health", timeout=5.0)
                if response.status_code == 200:
                    try:
                        service_data = response.json()
                        health_status[service_name] = {
                            "status": "healthy",
                            "data": service_data
                        }
                    except:
                        health_status[service_name] = {
                            "status": "healthy",
                            "data": {"raw_response": response.text}
                        }
                else:
                    health_status[service_name] = {
                        "status": "unhealthy",
                        "status_code": response.status_code,
                        "error": response.text
                    }
            except Exception as e:
                health_status[service_name] = {
                    "status": "unreachable",
                    "error": str(e)
                }
    
    return health_status

# Endpoint específico para login que maneja mejor los errores
@app.post("/autenticacion/login")
async def login_proxy(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            body = await request.body()
            response = await client.post(
                "http://microservicio-autenticacion:8001/login",
                content=body,
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return JSONResponse(content=response.json(), status_code=200)
            else:
                return JSONResponse(
                    content={"detail": "Error de autenticación"},
                    status_code=response.status_code
                )
                
        except httpx.ConnectError:
            return JSONResponse(
                content={"detail": "Servicio de autenticación no disponible"},
                status_code=503
            )
        except Exception as e:
            return JSONResponse(
                content={"detail": f"Error interno: {str(e)}"},
                status_code=500
            )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")