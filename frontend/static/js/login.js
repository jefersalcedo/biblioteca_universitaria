// Configuración
const API_BASE = 'http://localhost:8000';

// Elementos del DOM
const loginForm = document.getElementById('login-form');
const loading = document.getElementById('loading');

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si ya está autenticado
    checkAuthStatus();
    setupEventListeners();
});

// Verificar si ya hay sesión activa
function checkAuthStatus() {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
        // Si ya está autenticado, redirigir a la aplicación
        window.location.href = '/app';
    }
}

// Configurar event listeners
function setupEventListeners() {
    loginForm.addEventListener('submit', handleLogin);
}

// Manejar login
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/autenticacion/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Guardar token y datos del usuario
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // Redirigir a la aplicación principal
            window.location.href = '/app';
        } else {
            alert('Error: ' + (data.detail || 'Credenciales inválidas'));
        }
    } catch (error) {
        alert('Error de conexión: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Mostrar/ocultar loading
function showLoading(show) {
    loading.classList.toggle('hidden', !show);
}