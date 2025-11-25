from flask import Flask, render_template, jsonify, request
import requests
import os

app = Flask(__name__)
app.secret_key = 'biblioteca_secret_2024'

# Configuración
API_BASE = os.environ.get('API_BASE', 'http://api-gateway:8000')

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/app')
def main_app():
    return render_template('index.html')

@app.route('/catalogo')
def catalogo():
    return render_template('catalogo.html')   #ruta catalogos

@app.route('/prestamos')
def prestamos():
    return render_template('prestamos.html')  # ruta prestamo

@app.route('/reservas')
def reservas():
    return render_template('reservas.html')   # ruta reserva

@app.route('/api/login', methods=['POST'])
def login():
    try:
        # Obtener datos JSON del request del navegador
        data = request.get_json()
        # Realizar petición POST al API Gateway
        response = requests.post(f'{API_BASE}/autenticacion/login', json=data)
        # Retornar respuesta del backend al navegador
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        # Manejar errores de conexión
        return jsonify({'error': 'Error de conexión con el servidor'}), 503

@app.route('/api/books')
def get_books():
    try:
        response = requests.get(f'{API_BASE}/catalogo/libros')
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': 'Error de conexión con el servidor'}), 503

@app.route('/api/loans')
def get_loans():
    try:
        response = requests.get(f'{API_BASE}/prestamos/prestamos')
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': 'Error de conexión con el servidor'}), 503

@app.route('/api/reservations')
def get_reservations():
    try:
        response = requests.get(f'{API_BASE}/reservas/reservas')
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': 'Error de conexión con el servidor'}), 503

@app.route('/api/loans', methods=['POST'])
def create_loan():
    try:
        data = request.get_json()
        response = requests.post(f'{API_BASE}/prestamos/prestamos', json=data)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': 'Error de conexión con el servidor'}), 503

@app.route('/api/loans/<int:loan_id>/return', methods=['POST'])
def return_loan(loan_id):
    try:
        response = requests.post(f'{API_BASE}/prestamos/prestamos/{loan_id}/devolver')
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': 'Error de conexión con el servidor'}), 503

@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    try:
        data = request.get_json()
        response = requests.post(f'{API_BASE}/reservas/reservas', json=data)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': 'Error de conexión con el servidor'}), 503

@app.route('/api/reservations/<int:reservation_id>/cancel', methods=['POST'])
def cancel_reservation(reservation_id):
    try:
        response = requests.post(f'{API_BASE}/reservas/reservas/{reservation_id}/cancelar')
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': 'Error de conexión con el servidor'}), 503

# NUEVOS ENDPOINTS PARA MANEJAR USUARIOS
@app.route('/api/users')
def get_users():
    """Obtener lista de usuarios para pruebas"""
    try:
        # Esto es para desarrollo - en producción se obtendría de la base de datos
        users = [
            {"id": 1, "username": "admin", "full_name": "Administrador Principal", "role": "administrador"},
            {"id": 2, "username": "profesor1", "full_name": "Dr. Carlos Rodríguez", "role": "profesor"},
            {"id": 3, "username": "profesor2", "full_name": "Dra. María González", "role": "profesor"},
            {"id": 4, "username": "estudiante1", "full_name": "Ana López", "role": "estudiante"},
            {"id": 5, "username": "estudiante2", "full_name": "Juan Pérez", "role": "estudiante"},
            {"id": 6, "username": "estudiante3", "full_name": "Laura Martínez", "role": "estudiante"},
            {"id": 7, "username": "estudiante4", "full_name": "Pedro Sánchez", "role": "estudiante"},
            {"id": 8, "username": "estudiante5", "full_name": "Sofía Ramírez", "role": "estudiante"},
            {"id": 9, "username": "bibliotecario", "full_name": "Roberto Castro", "role": "bibliotecario"}
        ]
        return jsonify(users), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'frontend'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)