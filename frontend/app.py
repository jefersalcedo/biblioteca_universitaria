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

def get_user_info():
    """Obtiene información completa del usuario desde el servicio de autenticación"""
    if "access_token" not in session:
        return None
    
    try:
        response = requests.get(
            "http://authentication:8001/users/me",
            headers=get_auth_header(),
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    return session.get("user")

# ==================== ROUTES ====================

@app.route("/")
def index():
    """Página principal"""
    user_info = get_user_info()
    return render_template("index.html", user=user_info)

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
                
                # ===== CORRECCIÓN: Obtener información completa del usuario INMEDIATAMENTE =====
                try:
                    user_response = requests.get(
                        "http://authentication:8001/users/me",
                        headers={"Authorization": f"Bearer {data['access_token']}"},
                        timeout=5
                    )
                    
                    if user_response.status_code == 200:
                        user_info = user_response.json()
                        session["user"] = user_info
                        app.logger.info(f"Usuario autenticado: {user_info}")
                        flash(f"¡Bienvenido {user_info.get('full_name', username)}!", "success")
                    else:
                        # Fallback: guardar info básica
                        app.logger.warning("No se pudo obtener info del usuario, usando fallback")
                        session["user"] = {
                            "username": username,
                            "is_authenticated": True,
                            "roles": []
                        }
                        flash("¡Bienvenido!", "success")
                except Exception as e:
                    app.logger.error(f"Error al obtener info del usuario: {str(e)}")
                    session["user"] = {
                        "username": username,
                        "is_authenticated": True,
                        "roles": []
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
    libros_data = []
    try:
        response = requests.get(
            "http://catalogo:8002/libros",
            timeout=5
        )
        
        if response.status_code == 200:
            libros_data = response.json()
        else:
            app.logger.warning(f"Error del servicio de catálogo: {response.status_code}")
            flash("Error al cargar el catálogo", "error")
    except Exception as e:
        app.logger.error(f"Error al cargar libros: {str(e)}")
        flash("Error al conectar con el servicio de catálogo", "error")
    
    return render_template("libros.html", libros=libros_data, user=get_user_info())

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
    
    return render_template("prestamos.html", prestamos=prestamos_data, user=get_user_info())

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
    
    return render_template("reservas.html", reservas=reservas_data, user=get_user_info())

# ==================== PANEL DE ADMINISTRACIÓN ====================

@app.route("/admin")
def admin_panel():
    """Panel de administración"""
    if "access_token" not in session:
        flash("Debes iniciar sesión", "warning")
        return redirect(url_for("login"))
    
    # Verificar que el usuario sea admin
    user = get_user_info()
    app.logger.info(f"Usuario en admin_panel: {user}")
    
    if not user or "administrador" not in user.get("roles", []):
        flash("No tienes permisos de administrador", "error")
        return redirect(url_for("index"))
    
    usuarios_data = []
    try:
        response = requests.get(
            "http://authentication:8001/admin/users",
            headers=get_auth_header(),
            timeout=5
        )
        
        if response.status_code == 200:
            usuarios_data = response.json()
        else:
            app.logger.warning(f"Error al cargar usuarios: {response.status_code}")
            flash("Error al cargar usuarios", "error")
    except Exception as e:
        app.logger.error(f"Error al cargar usuarios: {str(e)}")
        flash("Error al conectar con el servicio de autenticación", "error")
    
    return render_template("admin.html", usuarios=usuarios_data, user=user)

@app.route("/admin/usuario/<int:user_id>/editar", methods=["GET", "POST"])
def editar_usuario(user_id):
    """Editar usuario"""
    if "access_token" not in session:
        flash("Debes iniciar sesión", "warning")
        return redirect(url_for("login"))
    
    # Verificar que el usuario sea admin
    user = get_user_info()
    if not user or "administrador" not in user.get("roles", []):
        flash("No tienes permisos de administrador", "error")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        # Obtener datos del formulario
        roles_seleccionados = request.form.getlist("roles")
        is_active = request.form.get("is_active") == "on"
        full_name = request.form.get("full_name")
        
        data = {
            "full_name": full_name,
            "is_active": is_active,
            "roles": roles_seleccionados
        }
        
        try:
            response = requests.put(
                f"http://authentication:8001/admin/users/{user_id}",
                headers=get_auth_header(),
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                flash("Usuario actualizado exitosamente", "success")
                return redirect(url_for("admin_panel"))
            else:
                error_msg = response.json().get("detail", "Error al actualizar usuario")
                flash(error_msg, "error")
        except Exception as e:
            app.logger.error(f"Error al actualizar usuario: {str(e)}")
            flash("Error al actualizar usuario", "error")
    
    # GET - Obtener datos del usuario
    try:
        response = requests.get(
            f"http://authentication:8001/admin/users/{user_id}",
            headers=get_auth_header(),
            timeout=5
        )
        
        if response.status_code == 200:
            usuario_data = response.json()
        else:
            flash("Usuario no encontrado", "error")
            return redirect(url_for("admin_panel"))
    except Exception as e:
        app.logger.error(f"Error al obtener usuario: {str(e)}")
        flash("Error al cargar usuario", "error")
        return redirect(url_for("admin_panel"))
    
    # Obtener roles disponibles
    roles_disponibles = [
        {"value": "estudiante", "label": "Estudiante"},
        {"value": "profesor", "label": "Profesor"},
        {"value": "administrador", "label": "Administrador"}
    ]
    
    return render_template(
        "admin_editar.html", 
        usuario=usuario_data, 
        roles_disponibles=roles_disponibles,
        user=user
    )

@app.route("/admin/usuario/<int:user_id>/eliminar", methods=["POST"])
def eliminar_usuario(user_id):
    """Eliminar usuario"""
    if "access_token" not in session:
        flash("Debes iniciar sesión", "warning")
        return redirect(url_for("login"))
    
    # Verificar que el usuario sea admin
    user = get_user_info()
    if not user or "administrador" not in user.get("roles", []):
        flash("No tienes permisos de administrador", "error")
        return redirect(url_for("index"))
    
    try:
        response = requests.delete(
            f"http://authentication:8001/admin/users/{user_id}",
            headers=get_auth_header(),
            timeout=5
        )
        
        if response.status_code == 200:
            flash("Usuario eliminado exitosamente", "success")
        else:
            error_msg = response.json().get("detail", "Error al eliminar usuario")
            flash(error_msg, "error")
    except Exception as e:
        app.logger.error(f"Error al eliminar usuario: {str(e)}")
        flash("Error al eliminar usuario", "error")
    
    return redirect(url_for("admin_panel"))

@app.route("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Frontend"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)