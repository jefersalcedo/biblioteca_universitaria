// Configuración
const API_BASE = 'http://localhost:8000';

// Estado de la aplicación
let currentUser = null;
let books = [];
let loans = [];
let reservations = [];

// Elementos del DOM
const navbar = document.getElementById('navbar');
const pages = document.querySelectorAll('.page');
const navLinks = document.querySelectorAll('.nav-link');

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    // Verificar autenticación antes de mostrar la app
    checkAuthStatus();
    setupEventListeners();
     // Leer la página actual de la URL
    const path = window.location.pathname;
    const currentPage = path.substring(1) || 'dashboard';
    showPage(currentPage);
});

// NUEVA FUNCIÓN: Verificar autenticación
function checkAuthStatus() {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
        currentUser = JSON.parse(userData);
        showApp();
    } else {
        // Si no está autenticado, redirigir al login
        window.location.href = '/';
    }
}

// Configurar event listeners
function setupEventListeners() {
    // Nav toggle para móviles
    document.getElementById('nav-toggle').addEventListener('click', toggleNav);
    
    // Navegación
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            navigateTo(page); // USAR NUEVA FUNCIÓN DE NAVEGACIÓN
        });
    });
}

// MEJORADO: Función para navegar entre páginas manteniendo el historial
function navigateTo(page) {
    const path = page === 'dashboard' ? '/app' : `/${page}`;
    
    // Solo actualizar el historial si estamos cambiando de página
    if (window.location.pathname !== path) {
        window.history.pushState({ page: page }, '', path);
    }
    
    showPage(page);
}

// MEJORADO: Manejar navegación con el botón "Atrás" del navegador
window.addEventListener('popstate', function(event) {
    const path = window.location.pathname;
    
    console.log('Popstate triggered, path:', path);
    
    // Verificar si el usuario está autenticado
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (!token || !userData) {
        // Usuario no autenticado - ir al login
        window.location.href = '/';
        return;
    }
    
    // Usuario autenticado - manejar navegación
    if (path === '/' || path === '/app') {
        showPage('dashboard');
    } else {
        const page = path.substring(1);
        if (['catalogo', 'prestamos', 'reservas'].includes(page)) {
            showPage(page);
        } else {
            // Página no reconocida, redirigir al dashboard
            window.history.replaceState({}, '', '/app');
            showPage('dashboard');
        }
    }
});

// Mostrar aplicación
function showApp() {
    navbar.style.display = 'block';
    showPage('dashboard');
    updateUserInfo();
    loadDashboardData();
}

// Mostrar página específica
function showPage(pageName) {
    // Ocultar todas las páginas
    pages.forEach(page => page.classList.remove('active'));
    
    // Mostrar página seleccionada
    document.getElementById(pageName).classList.add('active');
    
    // Actualizar navegación activa
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `/${pageName}` || link.getAttribute('data-page') === pageName) {
            link.classList.add('active');
        }
    });
    
    // Cerrar menú móvil si está abierto
    document.getElementById('nav-menu').classList.remove('active');
    
    // Cargar datos específicos de la página
    switch(pageName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'catalogo':
            loadBooks();
            break;
        case 'prestamos':
            loadLoans();
            break;
        case 'reservas':
            loadReservations();
            break;
    }
}




window.addEventListener('popstate', function(event) {
    const path = window.location.pathname;
    const page = path.substring(1) || 'dashboard';
    showPage(page);
});

// Actualizar información del usuario
function updateUserInfo() {
    document.getElementById('user-name').textContent = currentUser.full_name;
    document.getElementById('user-role').textContent = currentUser.role;
}

// Toggle navegación móvil
function toggleNav() {
    document.getElementById('nav-menu').classList.toggle('active');
}

// Mostrar/ocultar loading
function showLoading(show) {
    document.getElementById('loading').classList.toggle('hidden', !show);
}

// Cargar datos del dashboard - VERSIÓN MEJORADA CON ESTADÍSTICAS REALES
// Cargar datos del dashboard - VERSIÓN CORREGIDA
async function loadDashboardData() {
    try {
        showLoading(true);
        
        // Obtener estadísticas REALES y específicas del usuario
        const [totalLibros, prestamosActivos, reservasActivas] = await Promise.all([
            getTotalLibros(),
            getPrestamosActivos(),
            getTotalReservas() // Esta ahora cuenta solo las activas del usuario
        ]);

        console.log('Estadísticas dashboard:', {
            totalLibros,
            prestamosActivos, 
            reservasActivas
        });

        // Actualizar la UI con IDs específicos
        document.getElementById('total-libros').textContent = totalLibros;
        document.getElementById('prestamos-activos').textContent = prestamosActivos;
        document.getElementById('reservas-activas').textContent = reservasActivas;
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        // Mostrar datos por defecto en caso de error
        document.getElementById('total-libros').textContent = '0';
        document.getElementById('prestamos-activos').textContent = '0';
        document.getElementById('reservas-activas').textContent = '0';
    } finally {
        showLoading(false);
    }
}

// FUNCIONES DE ESTADÍSTICAS INTEGRADAS DESDE CATALOGO.JS Y PRESTAMOS.JS

// Obtener total de libros desde el microservicio de catálogo
async function getTotalLibros() {
    try {
        const response = await fetch(`${API_BASE}/catalogo/libros`);
        if (response.ok) {
            const libros = await response.json();
            return Array.isArray(libros) ? libros.length : 0;
        }
        return 0;
    } catch (error) {
        console.error('Error obteniendo total de libros:', error);
        return 0;
    }
}

// Obtener préstamos activos desde el microservicio de préstamos
// Obtener préstamos activos del usuario actual
async function getPrestamosActivos() {
    try {
        if (!currentUser) return 0;
        
        const response = await fetch(`${API_BASE}/prestamos/prestamos`);
        if (response.ok) {
            const prestamos = await response.json();
            if (Array.isArray(prestamos)) {
                // Filtrar solo los préstamos ACTIVOS del usuario actual
                return prestamos.filter(p => p.estado === 'activo' && p.usuario_id === currentUser.id).length;
            }
        }
        return 0;
    } catch (error) {
        console.error('Error obteniendo préstamos activos:', error);
        return 0;
    }
}

// Obtener total de reservas (por implementar)
// Obtener total de reservas ACTIVAS del usuario actual
async function getTotalReservas() {
    try {
        if (!currentUser) return 0;
        
        const response = await fetch(`${API_BASE}/reservas/reservas/usuario/${currentUser.id}`);
        if (response.ok) {
            const reservas = await response.json();
            if (Array.isArray(reservas)) {
                // Contar solo las reservas ACTIVAS del usuario
                return reservas.filter(r => r.estado === 'activa').length;
            }
        }
        return 0;
    } catch (error) {
        console.error('Error obteniendo reservas:', error);
        return 0;
    }
}

// FUNCIONES DE CATÁLOGO

// Cargar libros
async function loadBooks() {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/catalogo/libros`);
        if (response.ok) {
            books = await response.json();
            displayBooks(books);
            loadFilters(books); // Cargar filtros
        } else {
            throw new Error('Error al cargar libros');
        }
    } catch (error) {
        console.error('Error loading books:', error);
        alert('Error al cargar el catálogo');
    } finally {
        showLoading(false);
    }
}

function loadFilters(books) {
    const categorias = [...new Set(books.map(book => book.categoria))];
    const autores = [...new Set(books.map(book => book.autor))];
    
    // Agregar filtros al HTML (necesitarás agregar estos elementos al HTML)
    const filtersContainer = document.getElementById('filters-container');
    if (filtersContainer) {
        filtersContainer.innerHTML = `
            <div class="filter-group">
                <label for="categoria-filter">Categoría:</label>
                <select id="categoria-filter" onchange="filterBooks()">
                    <option value="">Todas</option>
                    ${categorias.map(cat => `<option value="${cat}">${cat}</option>`).join('')}
                </select>
            </div>
            <div class="filter-group">
                <label for="autor-filter">Autor:</label>
                <select id="autor-filter" onchange="filterBooks()">
                    <option value="">Todos</option>
                    ${autores.map(aut => `<option value="${aut}">${aut}</option>`).join('')}
                </select>
            </div>
        `;
    }
}

// Mostrar libros
function displayBooks(booksToShow) {
    const booksGrid = document.getElementById('books-grid');
    
    if (booksToShow.length === 0) {
        booksGrid.innerHTML = '<p class="no-data">No se encontraron libros</p>';
        return;
    }
    
    booksGrid.innerHTML = booksToShow.map(book => `
        <div class="book-card">
            <h3>${book.titulo}</h3>
            <div class="book-meta">
                <div><strong>Autor:</strong> ${book.autor}</div>
                <div><strong>Categoría:</strong> ${book.categoria}</div>
                <div><strong>Año:</strong> ${book.año_publicacion}</div>
                <div><strong>Editorial:</strong> ${book.editorial}</div>
                ${book.descripcion ? `<div><strong>Descripción:</strong> ${book.descripcion}</div>` : ''}
            </div>
            <div class="availability ${book.ejemplares_disponibles > 0 ? 'available' : 'unavailable'}">
                ${book.ejemplares_disponibles} de ${book.ejemplares_totales} ejemplares disponibles
            </div>
            <div class="book-actions">
                <button class="btn btn-primary" onclick="reserveBook(${book.id})" 
                        ${book.ejemplares_disponibles === 0 ? 'disabled' : ''}>
                    <i class="fas fa-calendar-plus"></i> Reservar
                </button>
                <button class="btn btn-success" onclick="loanBook(${book.id})"
                        ${book.ejemplares_disponibles === 0 ? 'disabled' : ''}>
                    <i class="fas fa-exchange-alt"></i> Prestar
                </button>
            </div>
        </div>
    `).join('');
}

// Filtrar libros
function filterBooks() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const categoriaFilter = document.getElementById('categoria-filter')?.value || '';
    const autorFilter = document.getElementById('autor-filter')?.value || '';
    
    const filteredBooks = books.filter(book => 
        book.titulo.toLowerCase().includes(searchTerm) &&
        (categoriaFilter === '' || book.categoria === categoriaFilter) &&
        (autorFilter === '' || book.autor === autorFilter)
    );
    
    displayBooks(filteredBooks);
}

// Reservar libro - MEJORADA CON MANEJO DE USUARIO
// Reservar libro - MEJORADA CON MANEJO DE USUARIO
async function reserveBook(bookId) {
    if (!currentUser) {
        alert('Debes iniciar sesión para reservar libros');
        return;
    }
    
    try {
        showLoading(true);
        console.log(`Reservando libro: ${bookId} para usuario: ${currentUser.id}`);
        
        const response = await fetch(`${API_BASE}/reservas/reservas`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                usuario_id: currentUser.id,
                libro_id: bookId,
                dias_reserva: 3
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✅ Libro reservado exitosamente');
            loadBooks();
            loadReservations();
        } else {
            alert('❌ Error al reservar el libro: ' + (data.detail || data.error));
        }
    } catch (error) {
        console.error('Error reservando libro:', error);
        alert('❌ Error de conexión: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Prestar libro - MEJORADA CON MANEJO DE USUARIO
async function loanBook(bookId) {
    if (!currentUser) {
        alert('Debes iniciar sesión para solicitar préstamos');
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/prestamos/prestamos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                usuario_id: currentUser.id,
                libro_id: bookId,
                dias_prestamo: 15
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✅ Préstamo realizado exitosamente');
            loadBooks();
            loadLoans();
        } else {
            alert('❌ Error al realizar el préstamo: ' + (data.detail || data.error));
        }
    } catch (error) {
        alert('❌ Error de conexión: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// FUNCIONES DE PRÉSTAMOS

// Cargar préstamos - MEJORADA PARA FILTRAR POR USUARIO
async function loadLoans() {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/prestamos/prestamos`);
        if (response.ok) {
            loans = await response.json();
            // Filtrar préstamos del usuario actual
            const userLoans = loans.filter(loan => loan.usuario_id === currentUser.id);
            displayLoans(userLoans);
        } else {
            throw new Error('Error al cargar préstamos');
        }
    } catch (error) {
        console.error('Error loading loans:', error);
        const container = document.getElementById('loans-container');
        container.innerHTML = '<p class="no-data">No tienes préstamos activos</p>';
    } finally {
        showLoading(false);
    }
}

// Mostrar préstamos
function displayLoans(loansToShow) {
    const container = document.getElementById('loans-container');
    
    if (!loansToShow || loansToShow.length === 0) {
        container.innerHTML = '<p class="no-data">No tienes préstamos activos</p>';
        return;
    }
    
    container.innerHTML = loansToShow.map(loan => `
        <div class="book-card">
            <h3>Préstamo #${loan.id}</h3>
            <div class="book-meta">
                <div><strong>Libro ID:</strong> ${loan.libro_id}</div>
                <div><strong>Fecha préstamo:</strong> ${new Date(loan.fecha_prestamo).toLocaleDateString()}</div>
                <div><strong>Devolución esperada:</strong> ${new Date(loan.fecha_devolucion_esperada).toLocaleDateString()}</div>
                <div><strong>Estado:</strong> ${loan.estado}</div>
                ${loan.multa > 0 ? `<div><strong>Multa:</strong> $${loan.multa}</div>` : ''}
            </div>
            ${loan.estado === 'activo' ? `
                <div class="book-actions">
                    <button class="btn btn-primary" onclick="returnBook(${loan.id})">
                        <i class="fas fa-undo"></i> Devolver
                    </button>
                </div>
            ` : ''}
        </div>
    `).join('');
}

// Devolver libro
async function returnBook(loanId) {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/prestamos/prestamos/${loanId}/devolver`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✅ Libro devuelto exitosamente');
            loadLoans();
        } else {
            alert('❌ Error al devolver el libro: ' + (data.detail || data.error));
        }
    } catch (error) {
        alert('❌ Error de conexión: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// FUNCIONES DE RESERVAS

// Cargar reservas - MEJORADA PARA FILTRAR POR USUARIO
async function loadReservations() {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/reservas/reservas/usuario/${currentUser.id}`);
        if (response.ok) {
            reservations = await response.json();
            console.log('Reservas cargadas:', reservations); // Para debug
            displayReservations(reservations);
        } else {
            throw new Error('Error al cargar reservas');
        }
    } catch (error) {
        console.error('Error loading reservations:', error);
        const container = document.getElementById('reservations-container');
        container.innerHTML = `
            <div class="no-data">
                <i class="fas fa-calendar-check fa-3x"></i>
                <h3>No tienes reservas activas</h3>
                <p>Error al cargar las reservas: ${error.message}</p>
                <button class="btn btn-primary" onclick="loadReservations()">
                    <i class="fas fa-redo"></i> Reintentar
                </button>
            </div>
        `;
    } finally {
        showLoading(false);
    }
}

// Mostrar reservas
function displayReservations(reservationsToShow) {
    const container = document.getElementById('reservations-container');
    
    console.log('Mostrando reservas:', reservationsToShow); // Para debug
    
    if (!reservationsToShow || reservationsToShow.length === 0) {
        container.innerHTML = `
            <div class="no-data">
                <i class="fas fa-calendar-check fa-3x"></i>
                <h3>No tienes reservas activas</h3>
                <p>Visita el catálogo para hacer una reserva</p>
                <button class="btn btn-primary" onclick="showPage('catalogo')">
                    <i class="fas fa-book-open"></i> Ir al Catálogo
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = reservationsToShow.map(res => `
        <div class="book-card">
            <h3>Reserva #${res.id.substring(0, 8)}...</h3>
            <div class="book-meta">
                <div><strong>Libro ID:</strong> ${res.libro_id}</div>
                <div><strong>Fecha reserva:</strong> ${new Date(res.fecha_reserva).toLocaleDateString()}</div>
                <div><strong>Vence:</strong> ${new Date(res.fecha_vencimiento).toLocaleDateString()}</div>
                <div><strong>Estado:</strong> <span class="status-${res.estado}">${res.estado}</span></div>
                ${res.notificado ? `<div><strong>Notificado:</strong> Sí</div>` : ''}
            </div>
            ${res.estado === 'activa' ? `
                <div class="book-actions">
                    <button class="btn btn-danger" onclick="cancelReservation('${res.id}')">
                        <i class="fas fa-times"></i> Cancelar
                    </button>
                </div>
            ` : ''}
        </div>
    `).join('');
}

// Cancelar reserva
async function cancelReservation(reservationId) {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/reservas/reservas/${reservationId}/cancelar`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✅ Reserva cancelada exitosamente');
            loadReservations();
        } else {
            alert('❌ Error al cancelar la reserva: ' + (data.detail || data.error));
        }
    } catch (error) {
        alert('❌ Error de conexión: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

// Manejar navegación con el botón "Atrás" del navegador
window.addEventListener('popstate', function(event) {
    const path = window.location.pathname;
    
    // Si estamos en cualquier página excepto login y dashboard, redirigir al dashboard
    if (path !== '/' && path !== '/app') {
        // Verificar si el usuario está autenticado
        const token = localStorage.getItem('token');
        const userData = localStorage.getItem('user');
        
        if (token && userData) {
            // Usuario autenticado - ir al dashboard
            window.location.href = '/app';
        } else {
            // Usuario no autenticado - ir al login
            window.location.href = '/';
        }
    }
});

// Función para navegar entre páginas manteniendo el historial
function navigateTo(page) {
    const path = page === 'dashboard' ? '/app' : `/${page}`;
    window.history.pushState({}, '', path);
    showPage(page);
}