from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

# ==================== HELPERS ====================

def get_auth_header():
    """Obtiene el header de autorización desde la sesión"""
    token = session.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

# ==================== ROUTES ====================

@app.route("/")
def index():
    """Página principal"""
    return render_template("index.html", user=session.get("user"))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login de usuarios"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        try:
            # Llamar directamente al servicio de autenticación
            response = requests.post(
                "http://authentication:8001/login",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                session["access_token"] = data["access_token"]
                session["token_type"] = data.get("token_type", "bearer")
                
                # Guardar información básica del usuario
                session["user"] = {
                    "username": username,
                    "is_authenticated": True
                }
                
                flash("¡Bienvenido!", "success")
                return redirect(url_for("index"))
            else:
                flash("Credenciales incorrectas", "error")
                
        except requests.exceptions.Timeout:
            flash("Tiempo de espera agotado. Intenta de nuevo.", "error")
        except requests.exceptions.ConnectionError:
            flash("Error de conexión con el servidor.", "error")
        except Exception as e:
            app.logger.error(f"Error en login: {str(e)}")
            flash("Error inesperado. Por favor intenta de nuevo.", "error")
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Registro de nuevos usuarios"""
    if request.method == "POST":
        data = {
            "email": request.form.get("email"),
            "username": request.form.get("username"),
            "full_name": request.form.get("full_name"),
            "password": request.form.get("password")
        }
        
        try:
            response = requests.post(
                "http://authentication:8001/register",
                json=data,
                timeout=5
            )
            
            if response.status_code == 200 or response.status_code == 201:
                flash("Usuario creado exitosamente. Por favor inicia sesión.", "success")
                return redirect(url_for("login"))
            else:
                error_msg = response.json().get("detail", "Error al crear usuario")
                flash(error_msg, "error")
                
        except Exception as e:
            app.logger.error(f"Error en registro: {str(e)}")
            flash("Error al crear usuario", "error")
    
    return render_template("register.html")

@app.route("/logout")
def logout():
    """Cerrar sesión"""
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("index"))

@app.route("/libros")
def libros():
    """Lista de libros del catálogo"""
    try:
        response = requests.get(
            "http://catalogo:8002/libros",
            timeout=5
        )
        
        if response.status_code == 200:
            libros_data = response.json()
            return render_template("libros.html", libros=libros_data, user=session.get("user"))
    except Exception as e:
        app.logger.error(f"Error al cargar libros: {str(e)}")
    
    flash("Error al cargar libros", "error")
    return redirect(url_for("index"))

@app.route("/mis-prestamos")
def mis_prestamos():
    """Préstamos del usuario actual"""
    if "access_token" not in session:
        flash("Debes iniciar sesión", "warning")
        return redirect(url_for("login"))
    
    prestamos_data = []
    try:
        response = requests.get(
            "http://prestamo:8003/prestamos",
            headers=get_auth_header(),
            timeout=5
        )
        
        if response.status_code == 200:
            prestamos_data = response.json()
        else:
            app.logger.warning(f"Error del servicio de préstamos: {response.status_code}")
    except Exception as e:
        app.logger.error(f"Error al cargar préstamos: {str(e)}")
    
    # Siempre mostrar la página, aunque esté vacía
    return render_template("prestamos.html", prestamos=prestamos_data, user=session.get("user"))


@app.route("/mis-reservas")
def mis_reservas():
    """Reservas del usuario actual"""
    if "access_token" not in session:
        flash("Debes iniciar sesión", "warning")
        return redirect(url_for("login"))
    
    reservas_data = []
    try:
        response = requests.get(
            "http://reserva:8004/reservas",
            headers=get_auth_header(),
            timeout=5
        )
        
        if response.status_code == 200:
            reservas_data = response.json()
        else:
            app.logger.warning(f"Error del servicio de reservas: {response.status_code}")
    except Exception as e:
        app.logger.error(f"Error al cargar reservas: {str(e)}")
    
    # Siempre mostrar la página, aunque esté vacía
    return render_template("reservas.html", reservas=reservas_data, user=session.get("user"))

@app.route("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Frontend"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)