from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os

app = FastAPI(title="Biblioteca Universitaria")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URLs de servicios
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://authentication:8001")
CATALOGOS_SERVICE_URL = os.getenv("CATALOGOS_SERVICE_URL", "http://catalogo:8002")
PRESTAMOS_SERVICE_URL = os.getenv("PRESTAMOS_SERVICE_URL", "http://prestamo:8003")
RESERVAS_SERVICE_URL = os.getenv("RESERVAS_SERVICE_URL", "http://reserva:8004")

# ==================== HELPERS ====================

async def forward_request(url: str, request: Request):
    """Reenvía la petición al microservicio correspondiente"""
    async with httpx.AsyncClient() as client:
        # Copiar headers (incluyendo Authorization)
        headers = dict(request.headers)
        headers.pop("host", None)  # Remover host header
        
        # Obtener body si existe
        body = await request.body()
        
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params
            )
            
            return JSONResponse(
                content=response.json() if response.text else {},
                status_code=response.status_code
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check del gateway y servicios"""
    services_status = {}
    
    async with httpx.AsyncClient() as client:
        # Verificar cada servicio
        services = {
            "authentication": f"{AUTH_SERVICE_URL}/health",
            "catalogo": f"{CATALOGOS_SERVICE_URL}/health",
            "prestamo": f"{PRESTAMOS_SERVICE_URL}/health",
            "reserva": f"{RESERVAS_SERVICE_URL}/health"
        }
        
        for service_name, url in services.items():
            try:
                response = await client.get(url, timeout=2.0)
                services_status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                services_status[service_name] = "unavailable"
    
    all_healthy = all(status == "healthy" for status in services_status.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "gateway": "API Gateway",
        "services": services_status
    }

# ==================== AUTH ROUTES ====================

@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def auth_proxy(path: str, request: Request):
    """Proxy para el servicio de autenticación"""
    url = f"{AUTH_SERVICE_URL}/{path}"
    return await forward_request(url, request)

# ==================== CATÁLOGOS ROUTES ====================

@app.api_route("/api/catalogos/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catalogos_proxy(path: str, request: Request):
    """Proxy para el servicio de catálogos"""
    url = f"{CATALOGOS_SERVICE_URL}/{path}"
    return await forward_request(url, request)

# ==================== PRÉSTAMOS ROUTES ====================

@app.api_route("/api/prestamos/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def prestamos_proxy(path: str, request: Request):
    """Proxy para el servicio de préstamos"""
    url = f"{PRESTAMOS_SERVICE_URL}/{path}"
    return await forward_request(url, request)

# ==================== RESERVAS ROUTES ====================

@app.api_route("/api/reservas/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def reservas_proxy(path: str, request: Request):
    """Proxy para el servicio de reservas"""
    url = f"{RESERVAS_SERVICE_URL}/{path}"
    return await forward_request(url, request)

# ==================== ROOT ====================

@app.get("/")
async def root():
    return {
        "message": "Sistema de Biblioteca Universitaria",
        "version": "1.0.0",
        "services": {
            "authentication": "/api/authentication",
            "catalogo": "/api/catalogo",
            "prestamo": "/api/prestamo",
            "reserva": "/api/reserva"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)