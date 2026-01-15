"""
Módulo de votación.
Maneja la lógica de validación y persistencia de votos.
"""

from typing import List, Dict, Tuple
import streamlit as st

from .repo import (
    get_videos_by_activity,
    get_activity_by_id,
    has_student_voted,
    create_vote
)
from .models import Video, ActivityStatus


def validate_ranking(activity_id: int, rankings: Dict[int, int]) -> Tuple[bool, str]:
    """
    Valida que el ranking sea correcto.
    
    Args:
        activity_id: ID de la actividad
        rankings: Dict {video_id: rank}
    
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    videos = get_videos_by_activity(activity_id)
    n_videos = len(videos)
    video_ids = {v.id for v in videos}
    
    # Verificar que todos los vídeos estén rankeados
    if set(rankings.keys()) != video_ids:
        return False, "Debes ordenar todos los vídeos"
    
    # Verificar que los ranks sean de 1 a N
    rank_values = set(rankings.values())
    expected_ranks = set(range(1, n_videos + 1))
    
    if rank_values != expected_ranks:
        return False, f"Los rangos deben ser del 1 al {n_videos} sin repetir"
    
    return True, ""


def submit_vote(activity_id: int, student_id: int, rankings: Dict[int, int], 
                fingerprint: str = "") -> Tuple[bool, str]:
    """
    Envía un voto.
    
    Args:
        activity_id: ID de la actividad
        student_id: ID del estudiante
        rankings: Dict {video_id: rank}
        fingerprint: Fingerprint del cliente (opcional)
    
    Returns:
        Tupla (éxito, mensaje)
    """
    # Verificar actividad abierta
    activity = get_activity_by_id(activity_id)
    if not activity or activity.status != ActivityStatus.OPEN:
        return False, "La actividad no está abierta para votar"
    
    # Verificar que no haya votado ya
    if has_student_voted(activity_id, student_id):
        return False, "Ya has votado en esta actividad"
    
    # Validar ranking
    is_valid, error = validate_ranking(activity_id, rankings)
    if not is_valid:
        return False, error
    
    # Crear el voto
    try:
        vote_id = create_vote(activity_id, student_id, rankings, fingerprint)
        return True, f"Voto registrado correctamente (ID: {vote_id})"
    except Exception as e:
        return False, f"Error al registrar el voto: {str(e)}"


def initialize_video_order(activity_id: int):
    """
    Inicializa el orden de vídeos en la sesión si no existe.
    
    Args:
        activity_id: ID de la actividad
    """
    if 'video_order' not in st.session_state or st.session_state.get('video_order_activity') != activity_id:
        videos = get_videos_by_activity(activity_id)
        st.session_state['video_order'] = [v.id for v in videos]
        st.session_state['video_order_activity'] = activity_id


def get_current_video_order() -> List[int]:
    """
    Obtiene el orden actual de vídeos.
    
    Returns:
        Lista de IDs de vídeos en orden
    """
    return st.session_state.get('video_order', [])


def move_video_up(video_id: int):
    """Mueve un vídeo una posición arriba (mejor ranking)."""
    order = st.session_state.get('video_order', [])
    if video_id in order:
        idx = order.index(video_id)
        if idx > 0:
            order[idx], order[idx-1] = order[idx-1], order[idx]
            st.session_state['video_order'] = order


def move_video_down(video_id: int):
    """Mueve un vídeo una posición abajo (peor ranking)."""
    order = st.session_state.get('video_order', [])
    if video_id in order:
        idx = order.index(video_id)
        if idx < len(order) - 1:
            order[idx], order[idx+1] = order[idx+1], order[idx]
            st.session_state['video_order'] = order


def get_rankings_from_order() -> Dict[int, int]:
    """
    Convierte el orden actual a rankings.
    
    Returns:
        Dict {video_id: rank} donde rank 1 es el mejor
    """
    order = get_current_video_order()
    return {video_id: rank + 1 for rank, video_id in enumerate(order)}
