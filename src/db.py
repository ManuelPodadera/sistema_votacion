"""
Módulo de conexión y configuración de la base de datos SQLite.
Incluye la inicialización del esquema.
"""

import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager

# Ruta de la base de datos
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "app.db"


def ensure_db_directory():
    """Asegura que el directorio de la base de datos existe."""
    DB_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """
    Obtiene una conexión a la base de datos SQLite.
    
    Returns:
        Conexión a SQLite
    """
    ensure_db_directory()
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
    conn.execute("PRAGMA foreign_keys = ON")  # Habilitar claves foráneas
    return conn


@contextmanager
def get_db_connection():
    """
    Context manager para conexiones a la base de datos.
    Asegura que la conexión se cierre correctamente.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """
    Inicializa el esquema de la base de datos.
    Crea todas las tablas si no existen.
    """
    ensure_db_directory()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Tabla de estudiantes (whitelist)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT NOT NULL,
                full_name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                UNIQUE(group_name, full_name)
            )
        """)
        
        # Índice para búsqueda por grupo
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_students_group 
            ON students(group_name)
        """)
        
        # Tabla de actividades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'DRAFT',
                access_pin_hash TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Tabla de vídeos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                group_name TEXT NOT NULL,
                title TEXT NOT NULL,
                video_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
            )
        """)
        
        # Índice para búsqueda de vídeos por actividad
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_videos_activity 
            ON videos(activity_id)
        """)
        
        # Tabla de votos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                submitted_at TEXT NOT NULL,
                client_fingerprint_hash TEXT,
                locked INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE(activity_id, student_id)
            )
        """)
        
        # Índices para votos
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_votes_activity 
            ON votes(activity_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_votes_student 
            ON votes(student_id)
        """)
        
        # Tabla de items del ranking (detalle del voto)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vote_rank_items (
                vote_id INTEGER NOT NULL,
                video_id INTEGER NOT NULL,
                rank INTEGER NOT NULL,
                PRIMARY KEY (vote_id, video_id),
                FOREIGN KEY (vote_id) REFERENCES votes(id) ON DELETE CASCADE,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
                UNIQUE(vote_id, rank)
            )
        """)
        
        conn.commit()
        print("✅ Base de datos inicializada correctamente")


def reset_database():
    """
    Elimina y recrea la base de datos.
    ¡CUIDADO! Esto borra todos los datos.
    """
    if DB_PATH.exists():
        os.remove(DB_PATH)
    init_database()


# Inicializar la base de datos al importar el módulo
if not DB_PATH.exists():
    init_database()
