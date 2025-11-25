from models import libros_collection, autores_collection, categorias_collection
from datetime import datetime

def inicializar_datos():
    """Inicializa MongoDB con datos de ejemplo"""
    
    # Verificar si ya existen datos
    if libros_collection.count_documents({}) > 0:
        print("✅ MongoDB ya contiene datos")
        return
    
    # Insertar autores
    autores = [
        {"_id": 1, "nombre": "Gabriel García Márquez", "nacionalidad": "Colombiana"},
        {"_id": 2, "nombre": "Isabel Allende", "nacionalidad": "Chilena"},
        {"_id": 3, "nombre": "Mario Vargas Llosa", "nacionalidad": "Peruana"},
        {"_id": 4, "nombre": "Julio Cortázar", "nacionalidad": "Argentina"},
        {"_id": 5, "nombre": "Jorge Luis Borges", "nacionalidad": "Argentina"},
        {"_id": 6, "nombre": "Pablo Neruda", "nacionalidad": "Chilena"},
        {"_id": 7, "nombre": "Stephen King", "nacionalidad": "Estadounidense"},
        {"_id": 8, "nombre": "J.K. Rowling", "nacionalidad": "Británica"},
        {"_id": 9, "nombre": "George Orwell", "nacionalidad": "Británica"},
        {"_id": 10, "nombre": "Jane Austen", "nacionalidad": "Británica"},
        {"_id": 11, "nombre": "Isaac Asimov", "nacionalidad": "Rusa"},
        {"_id": 12, "nombre": "Carl Sagan", "nacionalidad": "Estadounidense"},
        {"_id": 13, "nombre": "Yuval Noah Harari", "nacionalidad": "Israelí"},
        {"_id": 14, "nombre": "Miguel de Cervantes", "nacionalidad": "Española"},
        {"_id": 15, "nombre": "William Shakespeare", "nacionalidad": "Británica"}
    ]
    
    autores_collection.insert_many(autores)
    
    # Insertar 30 libros de ejemplo
    libros = [
        {
            "_id": 1, "titulo": "Cien años de soledad", "autor_id": 1, 
            "autor": "Gabriel García Márquez", "categoria": "Literatura",
            "isbn": "9788437604947", "año_publicacion": 1967, 
            "editorial": "Sudamericana", "ejemplares_disponibles": 5, 
            "ejemplares_totales": 8, "descripcion": "Una obra maestra del realismo mágico"
        },
        {
            "_id": 2, "titulo": "La casa de los espíritus", "autor_id": 2,
            "autor": "Isabel Allende", "categoria": "Literatura", 
            "isbn": "9788401337208", "año_publicacion": 1982,
            "editorial": "Plaza & Janés", "ejemplares_disponibles": 4, 
            "ejemplares_totales": 6, "descripcion": "Novela familiar y política"
        },
        {
            "_id": 3, "titulo": "La ciudad y los perros", "autor_id": 3,
            "autor": "Mario Vargas Llosa", "categoria": "Literatura",
            "isbn": "9788420471839", "año_publicacion": 1963,
            "editorial": "Seix Barral", "ejemplares_disponibles": 3,
            "ejemplares_totales": 5, "descripcion": "Novela sobre cadetes militares"
        },
        {
            "_id": 4, "titulo": "Rayuela", "autor_id": 4,
            "autor": "Julio Cortázar", "categoria": "Literatura", 
            "isbn": "9788432216420", "año_publicacion": 1963,
            "editorial": "Sudamericana", "ejemplares_disponibles": 2,
            "ejemplares_totales": 4, "descripcion": "Novela experimental"
        },
        {
            "_id": 5, "titulo": "Ficciones", "autor_id": 5,
            "autor": "Jorge Luis Borges", "categoria": "Literatura",
            "isbn": "9788466337201", "año_publicacion": 1944,
            "editorial": "Sur", "ejemplares_disponibles": 6,
            "ejemplares_totales": 8, "descripcion": "Colección de cuentos"
        },
        {
            "_id": 6, "titulo": "Veinte poemas de amor", "autor_id": 6,
            "autor": "Pablo Neruda", "categoria": "Poesía",
            "isbn": "9789561128270", "año_publicacion": 1924,
            "editorial": "Nascimento", "ejemplares_disponibles": 7,
            "ejemplares_totales": 10, "descripcion": "Poesía romántica"
        },
        {
            "_id": 7, "titulo": "It", "autor_id": 7,
            "autor": "Stephen King", "categoria": "Terror",
            "isbn": "9781501142970", "año_publicacion": 1986,
            "editorial": "Viking Press", "ejemplares_disponibles": 4,
            "ejemplares_totales": 6, "descripcion": "Novela de terror"
        },
        {
            "_id": 8, "titulo": "Harry Potter y la piedra filosofal", "autor_id": 8,
            "autor": "J.K. Rowling", "categoria": "Fantasía",
            "isbn": "9788478884459", "año_publicacion": 1997,
            "editorial": "Salamandra", "ejemplares_disponibles": 8,
            "ejemplares_totales": 12, "descripcion": "Primer libro de la saga"
        },
        {
            "_id": 9, "titulo": "1984", "autor_id": 9,
            "autor": "George Orwell", "categoria": "Ciencia Ficción",
            "isbn": "9788499890944", "año_publicacion": 1949,
            "editorial": "Secker & Warburg", "ejemplares_disponibles": 5,
            "ejemplares_totales": 7, "descripcion": "Novela distópica"
        },
        {
            "_id": 10, "titulo": "Orgullo y prejuicio", "autor_id": 10,
            "autor": "Jane Austen", "categoria": "Romance",
            "isbn": "9788491050292", "año_publicacion": 1813,
            "editorial": "T. Egerton", "ejemplares_disponibles": 6,
            "ejemplares_totales": 9, "descripcion": "Clásico romántico"
        },
        
        {
            "_id": 11, "titulo": "Fundación", "autor_id": 11,
            "autor": "Isaac Asimov", "categoria": "Ciencia Ficción", 
            "isbn": "9780553293357", "año_publicacion": 1951,
            "editorial": "Gnome Press", "ejemplares_disponibles": 3,
            "ejemplares_totales": 5, "descripcion": "Saga de ciencia ficción"
        },
        {
            "_id": 12, "titulo": "Cosmos", "autor_id": 12,
            "autor": "Carl Sagan", "categoria": "Ciencia",
            "isbn": "9780345331359", "año_publicacion": 1980,
            "editorial": "Random House", "ejemplares_disponibles": 4,
            "ejemplares_totales": 6, "descripcion": "Divulgación científica"
        },
        {
            "_id": 13, "titulo": "Sapiens", "autor_id": 13,
            "autor": "Yuval Noah Harari", "categoria": "Historia",
            "isbn": "9788499926223", "año_publicacion": 2014,
            "editorial": "Debate", "ejemplares_disponibles": 5,
            "ejemplares_totales": 7, "descripcion": "Historia de la humanidad"
        },
        {
            "_id": 14, "titulo": "Don Quijote de la Mancha", "autor_id": 14,
            "autor": "Miguel de Cervantes", "categoria": "Literatura",
            "isbn": "9788467021936", "año_publicacion": 1605,
            "editorial": "Francisco de Robles", "ejemplares_disponibles": 6,
            "ejemplares_totales": 8, "descripcion": "Clásico de la literatura"
        },
        {
            "_id": 15, "titulo": "Hamlet", "autor_id": 15,
            "autor": "William Shakespeare", "categoria": "Teatro",
            "isbn": "9780140714548", "año_publicacion": 1603,
            "editorial": "Simon & Schuster", "ejemplares_disponibles": 4,
            "ejemplares_totales": 6, "descripcion": "Tragedia shakespiriana"
        }
    ]
    
    libros_collection.insert_many(libros)
    print(f"✅ MongoDB inicializado con {len(libros)} libros y {len(autores)} autores")