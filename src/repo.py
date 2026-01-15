"""
Módulo de repositorio (CRUD).
Contiene todas las operaciones de base de datos para las entidades.
"""

from typing import List, Optional, Tuple
import pandas as pd

from .db import get_db_connection
from .models import Student, Activity, ActivityStatus, Video, Vote, VoteRankItem
from .utils import get_current_timestamp, normalize_name, normalize_group, hash_pin


# ============================================================================
# ESTUDIANTES (STUDENTS)
# ============================================================================

def get_all_students(active_only: bool = True) -> List[Student]:
    """
    Obtiene todos los estudiantes.
    
    Args:
        active_only: Si True, solo devuelve estudiantes activos
    
    Returns:
        Lista de estudiantes
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if active_only:
            cursor.execute("SELECT * FROM students WHERE active = 1 ORDER BY group_name, full_name")
        else:
            cursor.execute("SELECT * FROM students ORDER BY group_name, full_name")
        return [Student.from_row(row) for row in cursor.fetchall()]


def get_student_by_id(student_id: int) -> Optional[Student]:
    """Obtiene un estudiante por su ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        return Student.from_row(row) if row else None


def get_student_by_group_and_name(group_name: str, full_name: str) -> Optional[Student]:
    """Obtiene un estudiante por grupo y nombre."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM students WHERE group_name = ? AND full_name = ? AND active = 1",
            (group_name, full_name)
        )
        row = cursor.fetchone()
        return Student.from_row(row) if row else None


def get_groups() -> List[str]:
    """Obtiene la lista de grupos únicos."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT group_name FROM students WHERE active = 1 ORDER BY group_name")
        return [row['group_name'] for row in cursor.fetchall()]


def get_students_by_group(group_name: str) -> List[Student]:
    """Obtiene los estudiantes de un grupo."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM students WHERE group_name = ? AND active = 1 ORDER BY full_name",
            (group_name,)
        )
        return [Student.from_row(row) for row in cursor.fetchall()]


def upsert_student(group_name: str, full_name: str) -> int:
    """
    Inserta o actualiza un estudiante.
    
    Args:
        group_name: Nombre del grupo
        full_name: Nombre completo del estudiante
    
    Returns:
        ID del estudiante
    """
    group_name = normalize_group(group_name)
    full_name = normalize_name(full_name)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar si existe
        cursor.execute(
            "SELECT id FROM students WHERE group_name = ? AND full_name = ?",
            (group_name, full_name)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Actualizar (reactivar si estaba inactivo)
            cursor.execute(
                "UPDATE students SET active = 1 WHERE id = ?",
                (existing['id'],)
            )
            return existing['id']
        else:
            # Insertar nuevo
            cursor.execute(
                "INSERT INTO students (group_name, full_name, active, created_at) VALUES (?, ?, 1, ?)",
                (group_name, full_name, get_current_timestamp())
            )
            return cursor.lastrowid


def import_students_from_df(df: pd.DataFrame, group_col: str = "Grupo", name_col: str = "Nombre ALUMNO") -> Tuple[int, int]:
    """
    Importa estudiantes desde un DataFrame.
    
    Args:
        df: DataFrame con los datos
        group_col: Nombre de la columna del grupo
        name_col: Nombre de la columna del nombre
    
    Returns:
        Tupla (insertados, actualizados)
    """
    inserted = 0
    updated = 0
    
    for _, row in df.iterrows():
        group = str(row.get(group_col, "")).strip()
        name = str(row.get(name_col, "")).strip()
        
        if not group or not name:
            continue
        
        # Verificar si existe antes del upsert para contar correctamente
        existing = get_student_by_group_and_name(normalize_group(group), normalize_name(name))
        
        upsert_student(group, name)
        
        if existing:
            updated += 1
        else:
            inserted += 1
    
    return inserted, updated


def get_students_count() -> int:
    """Obtiene el número total de estudiantes activos."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM students WHERE active = 1")
        return cursor.fetchone()['count']


def delete_all_students():
    """Elimina todos los estudiantes (desactiva)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE students SET active = 0")


# ============================================================================
# ACTIVIDADES (ACTIVITIES)
# ============================================================================

def get_all_activities() -> List[Activity]:
    """Obtiene todas las actividades."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activities ORDER BY created_at DESC")
        return [Activity.from_row(row) for row in cursor.fetchall()]


def get_activity_by_id(activity_id: int) -> Optional[Activity]:
    """Obtiene una actividad por su ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
        row = cursor.fetchone()
        return Activity.from_row(row) if row else None


def get_open_activities() -> List[Activity]:
    """Obtiene las actividades abiertas."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activities WHERE status = 'OPEN' ORDER BY created_at DESC")
        return [Activity.from_row(row) for row in cursor.fetchall()]


def create_activity(title: str, description: str = "", pin: str = "") -> int:
    """
    Crea una nueva actividad.
    
    Args:
        title: Título de la actividad
        description: Descripción (opcional)
        pin: PIN de acceso (opcional)
    
    Returns:
        ID de la actividad creada
    """
    pin_hash = hash_pin(pin) if pin else None
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO activities (title, description, status, access_pin_hash, created_at) 
               VALUES (?, ?, 'DRAFT', ?, ?)""",
            (title, description, pin_hash, get_current_timestamp())
        )
        return cursor.lastrowid


def update_activity(activity_id: int, title: str, description: str, pin: str = None):
    """
    Actualiza una actividad.
    
    Args:
        activity_id: ID de la actividad
        title: Nuevo título
        description: Nueva descripción
        pin: Nuevo PIN (None para no cambiar, "" para eliminar)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if pin is not None:
            pin_hash = hash_pin(pin) if pin else None
            cursor.execute(
                "UPDATE activities SET title = ?, description = ?, access_pin_hash = ? WHERE id = ?",
                (title, description, pin_hash, activity_id)
            )
        else:
            cursor.execute(
                "UPDATE activities SET title = ?, description = ? WHERE id = ?",
                (title, description, activity_id)
            )


def update_activity_status(activity_id: int, status: ActivityStatus):
    """Actualiza el estado de una actividad."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE activities SET status = ? WHERE id = ?",
            (status.value, activity_id)
        )


def delete_activity(activity_id: int):
    """Elimina una actividad y todos sus datos relacionados."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))


def duplicate_activity(activity_id: int) -> int:
    """
    Duplica una actividad con sus vídeos.
    
    Args:
        activity_id: ID de la actividad a duplicar
    
    Returns:
        ID de la nueva actividad
    """
    activity = get_activity_by_id(activity_id)
    if not activity:
        raise ValueError("Actividad no encontrada")
    
    # Crear nueva actividad
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO activities (title, description, status, access_pin_hash, created_at) 
               VALUES (?, ?, 'DRAFT', ?, ?)""",
            (f"{activity.title} (copia)", activity.description, 
             activity.access_pin_hash, get_current_timestamp())
        )
        new_activity_id = cursor.lastrowid
        
        # Copiar vídeos
        videos = get_videos_by_activity(activity_id)
        for video in videos:
            cursor.execute(
                """INSERT INTO videos (activity_id, group_name, title, video_url, created_at) 
                   VALUES (?, ?, ?, ?, ?)""",
                (new_activity_id, video.group_name, video.title, video.video_url, get_current_timestamp())
            )
        
        return new_activity_id


# ============================================================================
# VÍDEOS (VIDEOS)
# ============================================================================

def get_videos_by_activity(activity_id: int) -> List[Video]:
    """Obtiene los vídeos de una actividad."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM videos WHERE activity_id = ? ORDER BY group_name, title",
            (activity_id,)
        )
        return [Video.from_row(row) for row in cursor.fetchall()]


def get_video_by_id(video_id: int) -> Optional[Video]:
    """Obtiene un vídeo por su ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        return Video.from_row(row) if row else None


def create_video(activity_id: int, group_name: str, title: str, video_url: str) -> int:
    """
    Crea un nuevo vídeo.
    
    Returns:
        ID del vídeo creado
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO videos (activity_id, group_name, title, video_url, created_at) 
               VALUES (?, ?, ?, ?, ?)""",
            (activity_id, normalize_group(group_name), title.strip(), video_url.strip(), get_current_timestamp())
        )
        return cursor.lastrowid


def update_video(video_id: int, group_name: str, title: str, video_url: str):
    """Actualiza un vídeo."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE videos SET group_name = ?, title = ?, video_url = ? WHERE id = ?",
            (normalize_group(group_name), title.strip(), video_url.strip(), video_id)
        )


def delete_video(video_id: int):
    """Elimina un vídeo."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))


def import_videos_from_df(activity_id: int, df: pd.DataFrame, 
                          group_col: str = "Grupo", title_col: str = "Título", 
                          url_col: str = "URL") -> int:
    """
    Importa vídeos desde un DataFrame.
    
    Returns:
        Número de vídeos importados
    """
    count = 0
    for _, row in df.iterrows():
        group = str(row.get(group_col, "")).strip()
        title = str(row.get(title_col, "")).strip()
        url = str(row.get(url_col, "")).strip()
        
        if not group or not title or not url:
            continue
        
        create_video(activity_id, group, title, url)
        count += 1
    
    return count


# ============================================================================
# VOTOS (VOTES)
# ============================================================================

def has_student_voted(activity_id: int, student_id: int) -> bool:
    """Verifica si un estudiante ya votó en una actividad."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM votes WHERE activity_id = ? AND student_id = ?",
            (activity_id, student_id)
        )
        return cursor.fetchone() is not None


def create_vote(activity_id: int, student_id: int, rankings: dict, 
                fingerprint: str = "") -> int:
    """
    Crea un voto con sus rankings.
    
    Args:
        activity_id: ID de la actividad
        student_id: ID del estudiante
        rankings: Dict {video_id: rank}
        fingerprint: Fingerprint del cliente (opcional)
    
    Returns:
        ID del voto creado
    
    Raises:
        ValueError: Si el estudiante ya votó o hay error de validación
    """
    if has_student_voted(activity_id, student_id):
        raise ValueError("El estudiante ya ha votado en esta actividad")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Crear el voto
        cursor.execute(
            """INSERT INTO votes (activity_id, student_id, submitted_at, client_fingerprint_hash, locked) 
               VALUES (?, ?, ?, ?, 1)""",
            (activity_id, student_id, get_current_timestamp(), fingerprint or None)
        )
        vote_id = cursor.lastrowid
        
        # Insertar los rankings
        for video_id, rank in rankings.items():
            cursor.execute(
                "INSERT INTO vote_rank_items (vote_id, video_id, rank) VALUES (?, ?, ?)",
                (vote_id, video_id, rank)
            )
        
        return vote_id


def get_votes_by_activity(activity_id: int) -> List[Vote]:
    """Obtiene todos los votos de una actividad."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM votes WHERE activity_id = ? ORDER BY submitted_at",
            (activity_id,)
        )
        return [Vote.from_row(row) for row in cursor.fetchall()]


def get_vote_details(vote_id: int) -> List[VoteRankItem]:
    """Obtiene los detalles de un voto (rankings)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM vote_rank_items WHERE vote_id = ? ORDER BY rank",
            (vote_id,)
        )
        return [VoteRankItem.from_row(row) for row in cursor.fetchall()]


def get_votes_count_by_activity(activity_id: int) -> int:
    """Obtiene el número de votos en una actividad."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM votes WHERE activity_id = ?",
            (activity_id,)
        )
        return cursor.fetchone()['count']


def get_students_who_voted(activity_id: int) -> List[int]:
    """Obtiene los IDs de estudiantes que han votado en una actividad."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT student_id FROM votes WHERE activity_id = ?",
            (activity_id,)
        )
        return [row['student_id'] for row in cursor.fetchall()]


def get_students_pending_vote(activity_id: int) -> List[Student]:
    """Obtiene los estudiantes que NO han votado en una actividad."""
    voted_ids = get_students_who_voted(activity_id)
    all_students = get_all_students(active_only=True)
    
    if not voted_ids:
        return all_students
    
    return [s for s in all_students if s.id not in voted_ids]


def get_detailed_votes_for_export(activity_id: int) -> pd.DataFrame:
    """
    Obtiene todos los votos detallados para exportación.
    
    Returns:
        DataFrame con columnas: estudiante, grupo_estudiante, video, grupo_video, posicion, fecha_voto
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                s.full_name as estudiante,
                s.group_name as grupo_estudiante,
                v.title as video,
                v.group_name as grupo_video,
                vri.rank as posicion,
                vt.submitted_at as fecha_voto
            FROM votes vt
            JOIN students s ON vt.student_id = s.id
            JOIN vote_rank_items vri ON vt.id = vri.vote_id
            JOIN videos v ON vri.video_id = v.id
            WHERE vt.activity_id = ?
            ORDER BY s.group_name, s.full_name, vri.rank
        """, (activity_id,))
        
        rows = cursor.fetchall()
        if not rows:
            return pd.DataFrame()
        
        return pd.DataFrame([dict(row) for row in rows])
