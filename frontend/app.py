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
        
        # Llamar al API Gateway
        response = requests.post(
            f"{API_GATEWAY_URL}/api/authentication/login",
            data={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            session["access_token"] = data["access_token"]
            
            # Obtener info del usuario
            user_response = requests.get(
                f"{API_GATEWAY_URL}/api/authentication/users/me",
                headers={"Authorization": f"Bearer {data['access_token']}"}
            )
            
            if user_response.status_code == 200:
                session["user"] = user_response.json()
                flash("Bienvenido!", "success")
                return redirect(url_for("index"))
        
        flash("Credenciales incorrectas", "error")
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Registro de nuevos usuarios"""
    if request.method == "POST":
        data = {
            "email": request.form.get("email"),
            "username": request.form.get("username"),
            "full_name": request.form.get("full_name"),
            "password": request.form.get("password"),
            "roles": ["estudiante"]
        }
        
        response = requests.post(
            f"{API_GATEWAY_URL}/api/authentication/register",
            json=data
        )
        
        if response.status_code == 201:
            flash("Usuario creado exitosamente. Por favor inicia sesión.", "success")
            return redirect(url_for("login"))
        else:
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
    response = requests.get(f"{API_GATEWAY_URL}/api/catalogo/libros")
    
    if response.status_code == 200:
        libros = response.json()
        return render_template("libros.html", libros=libros, user=session.get("user"))
    
    flash("Error al cargar libros", "error")
    return redirect(url_for("index"))

@app.route("/mis-prestamos")
def mis_prestamos():
    """Préstamos del usuario actual"""
    if "access_token" not in session:
        flash("Debes iniciar sesión", "warning")
        return redirect(url_for("login"))
    
    response = requests.get(
        f"{API_GATEWAY_URL}/api/prestamo/prestamo",
        headers=get_auth_header()
    )
    
    if response.status_code == 200:
        prestamo = response.json()
        return render_template("prestamo.html", prestamo=prestamo, user=session.get("user"))
    
    flash("Error al cargar préstamos", "error")
    return redirect(url_for("index"))

@app.route("/mis-reservas")
def mis_reservas():
    """Reservas del usuario actual"""
    if "access_token" not in session:
        flash("Debes iniciar sesión", "warning")
        return redirect(url_for("login"))
    
    response = requests.get(
        f"{API_GATEWAY_URL}/api/reserva/reserva",
        headers=get_auth_header()
    )
    
    if response.status_code == 200:
        reserva = response.json()
        return render_template("reserva.html", reserva=reserva, user=session.get("user"))
    
    flash("Error al cargar reservas", "error")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)