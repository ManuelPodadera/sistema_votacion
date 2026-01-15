"""
Módulo de modelos de datos (dataclasses).
Define las estructuras de datos usadas en la aplicación.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class ActivityStatus(Enum):
    """Estados posibles de una actividad."""
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class Student:
    """Representa un estudiante en la whitelist."""
    id: Optional[int] = None
    group_name: str = ""
    full_name: str = ""
    active: bool = True
    created_at: str = ""
    
    @classmethod
    def from_row(cls, row) -> 'Student':
        """Crea un Student desde una fila de SQLite."""
        return cls(
            id=row['id'],
            group_name=row['group_name'],
            full_name=row['full_name'],
            active=bool(row['active']),
            created_at=row['created_at']
        )


@dataclass
class Activity:
    """Representa una actividad de votación."""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    status: ActivityStatus = ActivityStatus.DRAFT
    access_pin_hash: str = ""
    created_at: str = ""
    
    @classmethod
    def from_row(cls, row) -> 'Activity':
        """Crea una Activity desde una fila de SQLite."""
        return cls(
            id=row['id'],
            title=row['title'],
            description=row['description'] or "",
            status=ActivityStatus(row['status']),
            access_pin_hash=row['access_pin_hash'] or "",
            created_at=row['created_at']
        )


@dataclass
class Video:
    """Representa un vídeo asociado a una actividad."""
    id: Optional[int] = None
    activity_id: int = 0
    group_name: str = ""
    title: str = ""
    video_url: str = ""
    created_at: str = ""
    
    @classmethod
    def from_row(cls, row) -> 'Video':
        """Crea un Video desde una fila de SQLite."""
        return cls(
            id=row['id'],
            activity_id=row['activity_id'],
            group_name=row['group_name'],
            title=row['title'],
            video_url=row['video_url'],
            created_at=row['created_at']
        )


@dataclass
class Vote:
    """Representa un voto de un estudiante."""
    id: Optional[int] = None
    activity_id: int = 0
    student_id: int = 0
    submitted_at: str = ""
    client_fingerprint_hash: str = ""
    locked: bool = True
    
    @classmethod
    def from_row(cls, row) -> 'Vote':
        """Crea un Vote desde una fila de SQLite."""
        return cls(
            id=row['id'],
            activity_id=row['activity_id'],
            student_id=row['student_id'],
            submitted_at=row['submitted_at'],
            client_fingerprint_hash=row['client_fingerprint_hash'] or "",
            locked=bool(row['locked'])
        )


@dataclass
class VoteRankItem:
    """Representa un item del ranking en un voto."""
    vote_id: int = 0
    video_id: int = 0
    rank: int = 0
    
    @classmethod
    def from_row(cls, row) -> 'VoteRankItem':
        """Crea un VoteRankItem desde una fila de SQLite."""
        return cls(
            vote_id=row['vote_id'],
            video_id=row['video_id'],
            rank=row['rank']
        )


@dataclass
class VoteDetail:
    """Voto con información detallada para visualización."""
    vote_id: int = 0
    student_name: str = ""
    student_group: str = ""
    submitted_at: str = ""
    rankings: List[dict] = field(default_factory=list)  # Lista de {video_title, rank}
