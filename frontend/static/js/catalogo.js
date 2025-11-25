// Configuración
const API_BASE = 'http://localhost:8000';

// Estado
let books = [];
let currentUser = null;
let filteredBooks = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
    loadBooks();
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

// Cargar libros desde MongoDB
async function loadBooks() {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/catalogo/libros`);
        
        if (response.ok) {
            books = await response.json();
            filteredBooks = [...books];
            displayBooks(books);
            loadFilters(books);
            updateResultsCount(books.length);
        } else {
            throw new Error('Error al cargar libros');
        }
    } catch (error) {
        console.error('Error loading books:', error);
        showError('Error al cargar el catálogo. Verifica que el servicio esté funcionando.');
    } finally {
        showLoading(false);
    }
}

// Mostrar libros en el grid
function displayBooks(booksToShow) {
    const booksGrid = document.getElementById('books-grid');
    
    if (booksToShow.length === 0) {
        booksGrid.innerHTML = `
            <div class="no-data">
                <i class="fas fa-book-open fa-3x"></i>
                <h3>No se encontraron libros</h3>
                <p>Intenta con otros términos de búsqueda o filtros</p>
            </div>
        `;
        return;
    }
    
    booksGrid.innerHTML = booksToShow.map(book => `
        <div class="book-card">
            <div class="book-header">
                <h3>${book.titulo}</h3>
                <span class="book-category">${book.categoria}</span>
            </div>
            <div class="book-meta">
                <div class="meta-item">
                    <i class="fas fa-user"></i>
                    <strong>Autor:</strong> ${book.autor}
                </div>
                <div class="meta-item">
                    <i class="fas fa-calendar"></i>
                    <strong>Año:</strong> ${book.año_publicacion}
                </div>
                <div class="meta-item">
                    <i class="fas fa-building"></i>
                    <strong>Editorial:</strong> ${book.editorial}
                </div>
                <div class="meta-item">
                    <i class="fas fa-barcode"></i>
                    <strong>ISBN:</strong> ${book.isbn}
                </div>
                ${book.descripcion ? `
                <div class="meta-item description">
                    <i class="fas fa-file-alt"></i>
                    <strong>Descripción:</strong> ${book.descripcion}
                </div>
                ` : ''}
            </div>
            <div class="availability ${book.ejemplares_disponibles > 0 ? 'available' : 'unavailable'}">
                <i class="fas ${book.ejemplares_disponibles > 0 ? 'fa-check-circle' : 'fa-times-circle'}"></i>
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

// Cargar filtros
function loadFilters(books) {
    const categorias = [...new Set(books.map(book => book.categoria))].sort();
    const autores = [...new Set(books.map(book => book.autor))].sort();
    
    const categoriaSelect = document.getElementById('categoria-filter');
    const autorSelect = document.getElementById('autor-filter');
    
    categorias.forEach(categoria => {
        categoriaSelect.innerHTML += `<option value="${categoria}">${categoria}</option>`;
    });
    
    autores.forEach(autor => {
        autorSelect.innerHTML += `<option value="${autor}">${autor}</option>`;
    });
}

// Filtrar libros
function filterBooks() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const categoriaFilter = document.getElementById('categoria-filter').value;
    const autorFilter = document.getElementById('autor-filter').value;
    
    filteredBooks = books.filter(book => {
        const matchesSearch = book.titulo.toLowerCase().includes(searchTerm) ||
                            book.autor.toLowerCase().includes(searchTerm) ||
                            book.categoria.toLowerCase().includes(searchTerm);
        
        const matchesCategoria = !categoriaFilter || book.categoria === categoriaFilter;
        const matchesAutor = !autorFilter || book.autor === autorFilter;
        
        return matchesSearch && matchesCategoria && matchesAutor;
    });
    
    displayBooks(filteredBooks);
    updateResultsCount(filteredBooks.length);
}

// Limpiar filtros
function clearFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('categoria-filter').value = '';
    document.getElementById('autor-filter').value = '';
    filterBooks();
}

// Actualizar contador de resultados
function updateResultsCount(count) {
    const resultsElement = document.getElementById('results-count');
    resultsElement.textContent = `${count} libro${count !== 1 ? 's' : ''} encontrado${count !== 1 ? 's' : ''}`;
}

// Mostrar error
function showError(message) {
    const booksGrid = document.getElementById('books-grid');
    booksGrid.innerHTML = `
        <div class="error-message">
            <i class="fas fa-exclamation-triangle fa-2x"></i>
            <h3>Error</h3>
            <p>${message}</p>
            <button class="btn btn-primary" onclick="loadBooks()">
                <i class="fas fa-redo"></i> Reintentar
            </button>
        </div>
    `;
}

// Reservar libro - CONECTADO AL MICROSERVICIO DE PRÉSTAMOS
// Reservar libro - CONECTADO AL MICROSERVICIO DE RESERVAS CORREGIDO
// Reservar libro - CONECTADO AL MICROSERVICIO DE RESERVAS CORREGIDO
async function reserveBook(bookId) {
    if (!currentUser) {
        alert('Debes iniciar sesión para reservar libros');
        return;
    }
    
    try {
        showLoading(true);
        console.log(`Reservando libro ID: ${bookId} para usuario: ${currentUser.id}`);
        
        // Usar la función global para crear reserva
        if (typeof window.crearReservaDesdeCatalogo === 'function') {
            await window.crearReservaDesdeCatalogo(bookId);
            loadBooks(); // Recargar catálogo para actualizar disponibilidad
        } else {
            // Fallback si la función global no está disponible
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
                const bookTitle = books.find(b => b.id === bookId)?.titulo || `ID: ${bookId}`;
                alert(`✅ Reserva realizada exitosamente\n\n📚 Libro: ${bookTitle}\n📅 La reserva vence: ${new Date(data.fecha_vencimiento).toLocaleDateString()}`);
                loadBooks();
            } else {
                alert('❌ Error al reservar el libro: ' + (data.detail || data.error || 'Error desconocido'));
            }
        }
    } catch (error) {
        console.error('Error en reserva:', error);
        alert('🔌 Error de conexión al reservar el libro: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Prestar libro - CONECTADO AL MICROSERVICIO DE PRÉSTAMOS
async function loanBook(bookId) {
    if (!currentUser) {
        alert('Debes iniciar sesión para solicitar préstamos');
        return;
    }
    
    try {
        showLoading(true);
        
        // Crear préstamo en el microservicio de préstamos
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
            alert(`✅ Préstamo realizado exitosamente\n\n📖 Libro: ${books.find(b => b.id === bookId)?.titulo || `ID: ${bookId}`}\n📅 Fecha de devolución: ${new Date(data.fecha_devolucion_esperada).toLocaleDateString()}`);
            
        } else {
            alert('❌ Error al realizar el préstamo: ' + (data.detail || data.error || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error en préstamo:', error);
        alert('🔌 Error de conexión al realizar el préstamo');
    } finally {
        showLoading(false);
    }
}