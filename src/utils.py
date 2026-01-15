"""
Módulo de utilidades generales.
Incluye funciones de hashing, normalización de nombres y fechas.
"""

import hashlib
from datetime import datetime
import re


def hash_pin(pin: str, salt: str = "video_ranking_2026") -> str:
    """
    Genera un hash SHA-256 del PIN con salt.
    
    Args:
        pin: El PIN a hashear
        salt: Salt para el hash (por defecto fijo)
    
    Returns:
        Hash hexadecimal del PIN
    """
    combined = f"{salt}:{pin}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()


def verify_pin(pin: str, stored_hash: str, salt: str = "video_ranking_2026") -> bool:
    """
    Verifica si un PIN coincide con su hash almacenado.
    
    Args:
        pin: El PIN introducido por el usuario
        stored_hash: El hash almacenado en la base de datos
        salt: Salt usado para el hash
    
    Returns:
        True si el PIN es correcto, False en caso contrario
    """
    return hash_pin(pin, salt) == stored_hash


def normalize_name(name: str) -> str:
    """
    Normaliza un nombre:
    - Elimina espacios al inicio y final
    - Convierte múltiples espacios en uno solo
    - Mantiene la capitalización original
    
    Args:
        name: Nombre a normalizar
    
    Returns:
        Nombre normalizado
    """
    if not name:
        return ""
    # Eliminar espacios extra
    normalized = re.sub(r'\s+', ' ', name.strip())
    return normalized


def normalize_group(group: str) -> str:
    """
    Normaliza el nombre del grupo.
    
    Args:
        group: Nombre del grupo
    
    Returns:
        Nombre del grupo normalizado
    """
    if not group:
        return ""
    return group.strip().upper()


def get_current_timestamp() -> str:
    """
    Obtiene el timestamp actual en formato ISO.
    
    Returns:
        Timestamp en formato ISO 8601
    """
    return datetime.now().isoformat()


def format_datetime_display(iso_datetime: str) -> str:
    """
    Formatea un datetime ISO para mostrar al usuario.
    
    Args:
        iso_datetime: Datetime en formato ISO
    
    Returns:
        Datetime formateado para display
    """
    try:
        dt = datetime.fromisoformat(iso_datetime)
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return iso_datetime or ""


def generate_fingerprint(user_agent: str, ip: str = "") -> str:
    """
    Genera un fingerprint hash básico del cliente.
    
    Args:
        user_agent: User agent del navegador
        ip: Dirección IP (opcional)
    
    Returns:
        Hash del fingerprint
    """
    combined = f"{user_agent}:{ip}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:32]
