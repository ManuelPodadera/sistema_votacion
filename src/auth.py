"""
Módulo de autenticación.
Maneja el login de alumnos y administrador.
"""

import streamlit as st
from typing import Optional, Tuple

from .repo import (
    get_student_by_group_and_name,
    get_activity_by_id,
    has_student_voted
)
from .models import Student, Activity
from .utils import verify_pin


def check_admin_password(password: str) -> bool:
    """
    Verifica la contraseña del administrador.
    
    Args:
        password: Contraseña introducida
    
    Returns:
        True si la contraseña es correcta
    """
    try:
        admin_password = st.secrets["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError):
        st.error("⚠️ ERROR: No se ha configurado ADMIN_PASSWORD en los secretos.")
        st.info("Configura los secretos en Streamlit Cloud: Settings → Secrets → añade ADMIN_PASSWORD")
        return False
    
    return password == admin_password


def login_admin(password: str) -> bool:
    """
    Intenta hacer login como administrador.
    
    Args:
        password: Contraseña introducida
    
    Returns:
        True si el login es exitoso
    """
    if check_admin_password(password):
        st.session_state['is_admin'] = True
        st.session_state['admin_logged_in'] = True
        return True
    return False


def logout_admin():
    """Cierra la sesión del administrador."""
    st.session_state['is_admin'] = False
    st.session_state['admin_logged_in'] = False


def is_admin_logged_in() -> bool:
    """Verifica si el administrador está logueado."""
    return st.session_state.get('admin_logged_in', False)


def authenticate_student(group_name: str, full_name: str, activity_id: int, pin: str) -> Tuple[bool, str, Optional[Student]]:
    """
    Autentica a un estudiante para una actividad.
    
    Args:
        group_name: Nombre del grupo
        full_name: Nombre completo del estudiante
        activity_id: ID de la actividad
        pin: PIN de acceso a la actividad
    
    Returns:
        Tupla (éxito, mensaje_error, estudiante)
    """
    # Verificar que el estudiante existe
    student = get_student_by_group_and_name(group_name, full_name)
    if not student:
        return False, "Estudiante no encontrado en la lista", None
    
    if not student.active:
        return False, "El estudiante no está activo", None
    
    # Verificar la actividad
    activity = get_activity_by_id(activity_id)
    if not activity:
        return False, "Actividad no encontrada", None
    
    if activity.status.value != "OPEN":
        return False, "La actividad no está abierta para votar", None
    
    # Verificar el PIN
    if activity.access_pin_hash:
        if not verify_pin(pin, activity.access_pin_hash):
            return False, "PIN incorrecto", None
    
    # Verificar si ya votó
    if has_student_voted(activity_id, student.id):
        return False, "Ya has votado en esta actividad", None
    
    return True, "", student


def login_student(group_name: str, full_name: str, activity_id: int, pin: str) -> Tuple[bool, str]:
    """
    Intenta hacer login como estudiante.
    
    Args:
        group_name: Nombre del grupo
        full_name: Nombre completo
        activity_id: ID de la actividad
        pin: PIN de la actividad
    
    Returns:
        Tupla (éxito, mensaje_error)
    """
    success, error, student = authenticate_student(group_name, full_name, activity_id, pin)
    
    if success and student:
        st.session_state['student_id'] = student.id
        st.session_state['student_name'] = student.full_name
        st.session_state['student_group'] = student.group_name
        st.session_state['current_activity_id'] = activity_id
        st.session_state['student_logged_in'] = True
        return True, ""
    
    return False, error


def logout_student():
    """Cierra la sesión del estudiante."""
    keys_to_remove = [
        'student_id', 'student_name', 'student_group',
        'current_activity_id', 'student_logged_in',
        'video_order', 'vote_submitted'
    ]
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]


def is_student_logged_in() -> bool:
    """Verifica si hay un estudiante logueado."""
    return st.session_state.get('student_logged_in', False)


def get_current_student_id() -> Optional[int]:
    """Obtiene el ID del estudiante actual."""
    return st.session_state.get('student_id')


def get_current_activity_id() -> Optional[int]:
    """Obtiene el ID de la actividad actual."""
    return st.session_state.get('current_activity_id')
