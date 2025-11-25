// Configuración
const API_BASE = 'http://localhost:8000';

// Estado
let currentUser = null;
let prestamos = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
    loadPrestamos();
});

// Verificar autenticación
function checkAuthStatus() {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
        currentUser = JSON.parse(userData);
        updateUserInfo();
    } else {
        window.location.href = '/';
    }
}

// Actualizar información del usuario
function updateUserInfo() {
    if (currentUser) {
        document.getElementById('user-name').textContent = currentUser.full_name;
        document.getElementById('user-role').textContent = currentUser.role;
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
    document.getElementById('loading').classList.toggle('hidden', !show);
}

// Cargar préstamos
async function loadPrestamos() {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/prestamos/prestamos/usuario/${currentUser.id}`);
        
        if (response.ok) {
            prestamos = await response.json();
            displayPrestamosActivos(prestamos.filter(p => p.estado === 'activo'));
            displayHistorial(prestamos.filter(p => p.estado !== 'activo'));
        } else {
            throw new Error('Error al cargar préstamos');
        }
    } catch (error) {
        console.error('Error loading loans:', error);
        showError('Error al cargar los préstamos');
    } finally {
        showLoading(false);
    }
}

// Mostrar préstamos activos
function displayPrestamosActivos(prestamosActivos) {
    const container = document.getElementById('loans-container');
    
    if (prestamosActivos.length === 0) {
        container.innerHTML = `
            <div class="no-data">
                <i class="fas fa-exchange-alt fa-3x"></i>
                <h3>No tienes préstamos activos</h3>
                <p>Visita el catálogo para solicitar un préstamo</p>
                <button class="btn btn-primary" onclick="window.location.href='/catalogo'">
                    <i class="fas fa-book-open"></i> Ir al Catálogo
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = prestamosActivos.map(prestamo => `
        <div class="loan-card ${prestamo.estado}">
            <div class="loan-header">
                <h3>Préstamo #${prestamo.id}</h3>
                <span class="loan-status ${prestamo.estado}">${getEstadoText(prestamo.estado)}</span>
            </div>
            <div class="loan-meta">
                <div class="meta-item">
                    <i class="fas fa-book"></i>
                    <strong>Libro ID:</strong> ${prestamo.libro_id}
                </div>
                <div class="meta-item">
                    <i class="fas fa-calendar-alt"></i>
                    <strong>Préstamo:</strong> ${new Date(prestamo.fecha_prestamo).toLocaleDateString()}
                </div>
                <div class="meta-item">
                    <i class="fas fa-flag-checkered"></i>
                    <strong>Devolución:</strong> ${new Date(prestamo.fecha_devolucion_esperada).toLocaleDateString()}
                </div>
                ${prestamo.multa > 0 ? `
                <div class="meta-item warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Multa:</strong> $${prestamo.multa.toFixed(2)}
                </div>
                ` : ''}
            </div>
            <div class="loan-actions">
                <button class="btn btn-success" onclick="devolverLibro(${prestamo.id})">
                    <i class="fas fa-undo"></i> Devolver Libro
                </button>
                <button class="btn btn-info" onclick="verDetallesPrestamo(${prestamo.id})">
                    <i class="fas fa-info-circle"></i> Detalles
                </button>
            </div>
        </div>
    `).join('');
}

// Mostrar historial de préstamos
function displayHistorial(prestamosHistorial) {
    const container = document.getElementById('history-container');
    
    if (prestamosHistorial.length === 0) {
        container.innerHTML = `
            <div class="no-data">
                <i class="fas fa-history fa-3x"></i>
                <h3>No hay historial de préstamos</h3>
                <p>Tu historial de préstamos anteriores aparecerá aquí</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = prestamosHistorial.map(prestamo => `
        <div class="history-card">
            <div class="history-header">
                <h3>Préstamo #${prestamo.id}</h3>
                <span class="history-status ${prestamo.estado}">${getEstadoText(prestamo.estado)}</span>
            </div>
            <div class="history-meta">
                <div class="meta-item">
                    <i class="fas fa-book"></i>
                    <strong>Libro ID:</strong> ${prestamo.libro_id}
                </div>
                <div class="meta-item">
                    <i class="fas fa-calendar"></i>
                    <strong>Préstamo:</strong> ${new Date(prestamo.fecha_prestamo).toLocaleDateString()}
                </div>
                <div class="meta-item">
                    <i class="fas fa-flag-checkered"></i>
                    <strong>Devolución Esperada:</strong> ${new Date(prestamo.fecha_devolucion_esperada).toLocaleDateString()}
                </div>
                ${prestamo.fecha_devolucion_real ? `
                <div class="meta-item">
                    <i class="fas fa-check-circle"></i>
                    <strong>Devolución Real:</strong> ${new Date(prestamo.fecha_devolucion_real).toLocaleDateString()}
                </div>
                ` : ''}
                <div class="meta-item">
                    <i class="fas fa-info-circle"></i>
                    <strong>Estado:</strong> ${getEstadoText(prestamo.estado)}
                </div>
                ${prestamo.multa > 0 ? `
                <div class="meta-item warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Multa:</strong> $${prestamo.multa.toFixed(2)}
                </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// Devolver libro
async function devolverLibro(prestamoId) {
    if (!confirm('¿Estás seguro de que quieres devolver este libro?')) return;
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/prestamos/prestamos/${prestamoId}/devolver`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            alert(`✅ Libro devuelto exitosamente${result.multa > 0 ? `\nMulta aplicada: $${result.multa.toFixed(2)}` : ''}`);
            loadPrestamos(); // Recargar la lista
        } else {
            throw new Error('Error al devolver el libro');
        }
    } catch (error) {
        console.error('Error returning book:', error);
        alert('❌ Error al devolver el libro');
    } finally {
        showLoading(false);
    }
}

// Funciones auxiliares
function getEstadoText(estado) {
    const estados = {
        'activo': 'Activo',
        'devuelto': 'Devuelto',
        'vencido': 'Vencido'
    };
    return estados[estado] || estado;
}

function showError(message) {
    const container = document.getElementById('loans-container');
    container.innerHTML = `
        <div class="error-message">
            <i class="fas fa-exclamation-triangle fa-2x"></i>
            <h3>Error</h3>
            <p>${message}</p>
            <button class="btn btn-primary" onclick="loadPrestamos()">
                <i class="fas fa-redo"></i> Reintentar
            </button>
        </div>
    `;
}

// Modal functions
function verDetallesPrestamo(prestamoId) {
    const prestamo = prestamos.find(p => p.id === prestamoId);
    if (!prestamo) return;
    
    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = `
        <div class="modal-details">
            <div class="detail-item">
                <strong>ID Préstamo:</strong> ${prestamo.id}
            </div>
            <div class="detail-item">
                <strong>Libro ID:</strong> ${prestamo.libro_id}
            </div>
            <div class="detail-item">
                <strong>Usuario ID:</strong> ${prestamo.usuario_id}
            </div>
            <div class="detail-item">
                <strong>Fecha Préstamo:</strong> ${new Date(prestamo.fecha_prestamo).toLocaleString()}
            </div>
            <div class="detail-item">
                <strong>Devolución Esperada:</strong> ${new Date(prestamo.fecha_devolucion_esperada).toLocaleString()}
            </div>
            <div class="detail-item">
                <strong>Estado:</strong> <span class="status ${prestamo.estado}">${getEstadoText(prestamo.estado)}</span>
            </div>
            ${prestamo.fecha_devolucion_real ? `
            <div class="detail-item">
                <strong>Devolución Real:</strong> ${new Date(prestamo.fecha_devolucion_real).toLocaleString()}
            </div>
            ` : ''}
            ${prestamo.multa > 0 ? `
            <div class="detail-item warning">
                <strong>Multa:</strong> $${prestamo.multa.toFixed(2)}
            </div>
            <div class="detail-item warning">
                <strong>Días Retraso:</strong> ${prestamo.dias_retraso || 0}
            </div>
            ` : ''}
        </div>
    `;
    
    document.getElementById('loan-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('loan-modal').classList.add('hidden');
}

// Cerrar modal al hacer clic fuera
window.onclick = function(event) {
    const modal = document.getElementById('loan-modal');
    if (event.target === modal) {
        closeModal();
    }
}