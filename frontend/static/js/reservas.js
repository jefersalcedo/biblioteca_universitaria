// Configuración
const API_BASE = 'http://localhost:8000';

// Estado
let currentUser = null;
let reservas = [];
let notificaciones = [];
let filteredReservas = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    console.log('reservas.js inicializado');
    checkAuthStatus();
    setupEventListeners();
});

// Configurar event listeners
function setupEventListeners() {
    // Nav toggle para móviles
    const navToggle = document.getElementById('nav-toggle');
    if (navToggle) {
        navToggle.addEventListener('click', toggleNav);
    }
}

// Verificar autenticación
function checkAuthStatus() {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    console.log('Verificando autenticación...', { token: !!token, userData: !!userData });
    
    if (token && userData) {
        try {
            currentUser = JSON.parse(userData);
            console.log('Usuario autenticado:', currentUser);
            updateUserInfo();
            loadReservas();
            loadNotificaciones();
        } catch (error) {
            console.error('Error parsing user data:', error);
            redirectToLogin();
        }
    } else {
        console.log('No autenticado, redirigiendo...');
        redirectToLogin();
    }
}

function redirectToLogin() {
    window.location.href = '/';
}

// Actualizar información del usuario
function updateUserInfo() {
    if (currentUser && document.getElementById('user-name')) {
        document.getElementById('user-name').textContent = currentUser.full_name || 'Usuario';
    }
}

// Toggle navegación móvil
function toggleNav() {
    const navMenu = document.getElementById('nav-menu');
    if (navMenu) {
        navMenu.classList.toggle('active');
    }
}

// Logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

// Mostrar/ocultar loading
function showLoading(show) {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.classList.toggle('hidden', !show);
    }
}

// Cargar reservas del usuario
async function loadReservas() {
    try {
        console.log('Cargando reservas para usuario:', currentUser.id);
        showLoading(true);
        
        const response = await fetch(`${API_BASE}/reservas/reservas/usuario/${currentUser.id}`);
        console.log('Response status:', response.status);
        
        if (response.ok) {
            reservas = await response.json();
            console.log('Reservas recibidas:', reservas);
            
            filteredReservas = [...reservas];
            displayReservas(reservas);
            updateResultsCount(reservas.length);
        } else {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error loading reservations:', error);
        showError('Error al cargar las reservas: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Mostrar reservas en el grid
function displayReservas(reservasToShow) {
    const grid = document.getElementById('reservations-grid');
    
    if (!grid) {
        console.error('Elemento reservations-grid no encontrado');
        return;
    }
    
    console.log('Mostrando reservas:', reservasToShow);
    
    if (!reservasToShow || reservasToShow.length === 0) {
        grid.innerHTML = `
            <div class="no-data">
                <i class="fas fa-calendar-check fa-3x"></i>
                <h3>No tienes reservas</h3>
                <p>Visita el catálogo para hacer una reserva</p>
                <button class="btn btn-primary" onclick="window.location.href='/catalogo'">
                    <i class="fas fa-book-open"></i> Ir al Catálogo
                </button>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = reservasToShow.map(reserva => `
        <div class="reservation-card ${reserva.estado}">
            <div class="reservation-header">
                <h3>Reserva #${reserva.id ? reserva.id.substring(0, 8) + '...' : 'N/A'}</h3>
                <span class="reservation-status ${reserva.estado}">${getEstadoText(reserva.estado)}</span>
            </div>
            
            <div class="reservation-meta">
                <div class="meta-item">
                    <i class="fas fa-book"></i>
                    <strong>Libro ID:</strong> ${reserva.libro_id || 'N/A'}
                </div>
                <div class="meta-item">
                    <i class="fas fa-calendar-plus"></i>
                    <strong>Fecha Reserva:</strong> ${reserva.fecha_reserva ? new Date(reserva.fecha_reserva).toLocaleDateString() : 'N/A'}
                </div>
                <div class="meta-item">
                    <i class="fas fa-flag-checkered"></i>
                    <strong>Vence:</strong> ${reserva.fecha_vencimiento ? new Date(reserva.fecha_vencimiento).toLocaleDateString() : 'N/A'}
                </div>
                <div class="meta-item">
                    <i class="fas fa-info-circle"></i>
                    <strong>Estado:</strong> ${getEstadoText(reserva.estado)}
                </div>
            </div>
            
            <div class="reservation-actions">
                ${reserva.estado === 'activa' ? `
                    <button class="btn btn-danger" onclick="cancelarReserva('${reserva.id}')">
                        <i class="fas fa-times"></i> Cancelar Reserva
                    </button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// Filtrar reservas
function filterReservations() {
    const estadoFilter = document.getElementById('estado-filter').value;
    
    if (!estadoFilter) {
        filteredReservas = [...reservas];
    } else {
        filteredReservas = reservas.filter(reserva => reserva.estado === estadoFilter);
    }
    
    displayReservas(filteredReservas);
    updateResultsCount(filteredReservas.length);
}

// Limpiar filtros
function clearFilters() {
    document.getElementById('estado-filter').value = '';
    filterReservations();
}

// Actualizar contador de resultados
function updateResultsCount(count) {
    const resultsElement = document.getElementById('results-count');
    if (resultsElement) {
        resultsElement.textContent = `${count} reserva${count !== 1 ? 's' : ''} encontrada${count !== 1 ? 's' : ''}`;
    }
}

// Cancelar reserva
// Cancelar reserva - VERSIÓN MEJORADA
async function cancelarReserva(reservaId) {
    if (!confirm('¿Estás seguro de que quieres cancelar esta reserva?')) return;
    
    try {
        showLoading(true);
        console.log(`Cancelando reserva: ${reservaId}`);
        
        const response = await fetch(`${API_BASE}/reservas/reservas/${reservaId}/cancelar`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            alert('✅ Reserva cancelada exitosamente');
            
            // Recargar datos
            await loadReservas(); 
            await loadNotificaciones();
            
            // Actualizar dashboard
            await actualizarDashboard();
            
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al cancelar la reserva');
        }
    } catch (error) {
        console.error('Error canceling reservation:', error);
        alert('❌ Error al cancelar la reserva: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Cargar notificaciones
async function loadNotificaciones() {
    try {
        const response = await fetch(`${API_BASE}/reservas/notificaciones/usuario/${currentUser.id}`);
        
        if (response.ok) {
            notificaciones = await response.json();
            console.log('Notificaciones recibidas:', notificaciones);
            displayNotificaciones(notificaciones.filter(n => !n.leida));
        } else {
            console.warn('Error cargando notificaciones:', response.status);
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

// Mostrar notificaciones
function displayNotificaciones(notificacionesToShow) {
    const list = document.getElementById('notifications-list');
    
    if (!list) return;
    
    if (!notificacionesToShow || notificacionesToShow.length === 0) {
        list.innerHTML = `
            <div class="no-data">
                <i class="fas fa-bell-slash fa-2x"></i>
                <p>No tienes notificaciones nuevas</p>
            </div>
        `;
        return;
    }
    
    list.innerHTML = notificacionesToShow.map(notif => `
        <div class="notification-item ${notif.tipo}">
            <div class="notification-icon">
                <i class="fas ${getNotificationIcon(notif.tipo)}"></i>
            </div>
            <div class="notification-content">
                <p class="notification-message">${notif.mensaje}</p>
                <small class="notification-time">${notif.fecha_creacion ? new Date(notif.fecha_creacion).toLocaleString() : 'N/A'}</small>
            </div>
            <button class="btn btn-sm" onclick="marcarNotificacionLeida('${notif.id}')">
                <i class="fas fa-check"></i>
            </button>
        </div>
    `).join('');
}

// Función para actualizar el contador del dashboard
async function actualizarDashboard() {
    try {
        // Solo actualizar si estamos en el dashboard
        if (window.location.pathname === '/app' || window.location.pathname === '/') {
            // Recargar datos del dashboard
            const scriptPrincipal = document.querySelector('script[src*="script.js"]');
            if (scriptPrincipal && typeof window.loadDashboardData === 'function') {
                window.loadDashboardData();
            }
        }
        
        // También actualizar el contador en la página de reservas si existe
        const reservasActivas = filteredReservas.filter(r => r.estado === 'activa').length;
        const dashboardReservas = document.getElementById('reservas-activas');
        if (dashboardReservas) {
            dashboardReservas.textContent = reservasActivas;
        }
    } catch (error) {
        console.error('Error actualizando dashboard:', error);
    }
}

// Marcar notificación como leída
async function marcarNotificacionLeida(notificacionId) {
    try {
        const response = await fetch(`${API_BASE}/reservas/notificaciones/${notificacionId}/leer`, {
            method: 'POST'
        });
        
        if (response.ok) {
            loadNotificaciones(); // Recargar notificaciones
        }
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

// Funciones auxiliares
function getEstadoText(estado) {
    const estados = {
        'activa': 'Activa',
        'cancelada': 'Cancelada',
        'vencida': 'Vencida',
        'completada': 'Completada'
    };
    return estados[estado] || estado || 'Desconocido';
}

function getNotificationIcon(tipo) {
    const icons = {
        'vencimiento': 'fa-exclamation-triangle',
        'disponible': 'fa-check-circle',
        'recordatorio': 'fa-bell',
        'cancelacion': 'fa-times-circle'
    };
    return icons[tipo] || 'fa-bell';
}

function showError(message) {
    const grid = document.getElementById('reservations-grid');
    if (grid) {
        grid.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle fa-2x"></i>
                <h3>Error</h3>
                <p>${message}</p>
                <button class="btn btn-primary" onclick="loadReservas()">
                    <i class="fas fa-redo"></i> Reintentar
                </button>
            </div>
        `;
    }
}

// Función global para crear reserva desde otras páginas
// Función global para crear reserva desde otras páginas
window.crearReservaDesdeCatalogo = async function(libroId) {
    if (!currentUser) {
        alert('Debes iniciar sesión para reservar libros');
        return;
    }
    
    try {
        showLoading(true);
        console.log(`Creando reserva para libro: ${libroId}, usuario: ${currentUser.id}`);
        
        const response = await fetch(`${API_BASE}/reservas/reservas`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                usuario_id: currentUser.id,
                libro_id: libroId,
                dias_reserva: 3
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            alert('✅ Reserva creada exitosamente');
            
            // Actualizar dashboard
            await actualizarDashboard();
            
            // Si estamos en la página de reservas, recargar la lista
            if (window.location.pathname === '/reservas') {
                await loadReservas();
            }
            
            return data;
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al crear la reserva');
        }
    } catch (error) {
        console.error('Error creando reserva:', error);
        alert('❌ Error al crear la reserva: ' + error.message);
        throw error;
    } finally {
        showLoading(false);
    }
};