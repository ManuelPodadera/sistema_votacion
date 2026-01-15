"""
Módulo de puntuación y agregación.
Implementa el método Borda count y estadísticas.
"""

from typing import Dict, List, Tuple
import pandas as pd
from collections import defaultdict
import statistics

from .repo import (
    get_videos_by_activity,
    get_votes_by_activity,
    get_vote_details,
    get_students_count,
    get_votes_count_by_activity,
    get_students_who_voted,
    get_students_pending_vote
)
from .models import Video


def calculate_borda_scores(activity_id: int) -> Dict[int, int]:
    """
    Calcula los puntos Borda para cada vídeo.
    
    Método: Si hay N vídeos, rank=1 da N-1 puntos, rank=N da 0 puntos.
    
    Args:
        activity_id: ID de la actividad
    
    Returns:
        Dict {video_id: puntos_borda}
    """
    videos = get_videos_by_activity(activity_id)
    n_videos = len(videos)
    
    if n_videos == 0:
        return {}
    
    scores = {v.id: 0 for v in videos}
    votes = get_votes_by_activity(activity_id)
    
    for vote in votes:
        rank_items = get_vote_details(vote.id)
        for item in rank_items:
            # Puntos = N - rank (rank 1 = N-1 puntos, rank N = 0 puntos)
            points = n_videos - item.rank
            scores[item.video_id] = scores.get(item.video_id, 0) + points
    
    return scores


def get_ranking_results(activity_id: int) -> pd.DataFrame:
    """
    Obtiene el ranking final con puntuaciones Borda.
    
    Args:
        activity_id: ID de la actividad
    
    Returns:
        DataFrame con columnas: posicion, video_id, titulo, grupo, puntos_borda, votos_recibidos
    """
    videos = get_videos_by_activity(activity_id)
    scores = calculate_borda_scores(activity_id)
    n_votes = get_votes_count_by_activity(activity_id)
    
    if not videos:
        return pd.DataFrame()
    
    data = []
    for video in videos:
        data.append({
            'video_id': video.id,
            'titulo': video.title,
            'grupo': video.group_name,
            'puntos_borda': scores.get(video.id, 0),
            'votos_recibidos': n_votes
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values('puntos_borda', ascending=False).reset_index(drop=True)
    df['posicion'] = range(1, len(df) + 1)
    
    # Reordenar columnas
    df = df[['posicion', 'video_id', 'titulo', 'grupo', 'puntos_borda', 'votos_recibidos']]
    
    return df


def get_rank_distribution(activity_id: int) -> pd.DataFrame:
    """
    Obtiene la distribución de posiciones por vídeo.
    
    Args:
        activity_id: ID de la actividad
    
    Returns:
        DataFrame con vídeos como filas y posiciones como columnas
    """
    videos = get_videos_by_activity(activity_id)
    votes = get_votes_by_activity(activity_id)
    n_videos = len(videos)
    
    if not videos or not votes:
        return pd.DataFrame()
    
    # Inicializar distribución
    distribution = {v.id: {r: 0 for r in range(1, n_videos + 1)} for v in videos}
    video_titles = {v.id: f"{v.title} ({v.group_name})" for v in videos}
    
    for vote in votes:
        rank_items = get_vote_details(vote.id)
        for item in rank_items:
            distribution[item.video_id][item.rank] += 1
    
    # Construir DataFrame
    data = []
    for video_id, ranks in distribution.items():
        row = {'video': video_titles[video_id]}
        for rank, count in ranks.items():
            row[f'Pos {rank}'] = count
        data.append(row)
    
    return pd.DataFrame(data)


def get_rank_statistics(activity_id: int) -> pd.DataFrame:
    """
    Obtiene estadísticas de rank por vídeo (media, desviación estándar).
    
    Args:
        activity_id: ID de la actividad
    
    Returns:
        DataFrame con video, media_rank, desv_std
    """
    videos = get_videos_by_activity(activity_id)
    votes = get_votes_by_activity(activity_id)
    
    if not videos or not votes:
        return pd.DataFrame()
    
    # Recopilar ranks por vídeo
    video_ranks = {v.id: [] for v in videos}
    video_titles = {v.id: f"{v.title} ({v.group_name})" for v in videos}
    
    for vote in votes:
        rank_items = get_vote_details(vote.id)
        for item in rank_items:
            video_ranks[item.video_id].append(item.rank)
    
    # Calcular estadísticas
    data = []
    for video_id, ranks in video_ranks.items():
        if ranks:
            mean_rank = statistics.mean(ranks)
            std_rank = statistics.stdev(ranks) if len(ranks) > 1 else 0
        else:
            mean_rank = 0
            std_rank = 0
        
        data.append({
            'video': video_titles[video_id],
            'media_rank': round(mean_rank, 2),
            'desv_std': round(std_rank, 2)
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values('media_rank').reset_index(drop=True)
    
    return df


def get_participation_stats(activity_id: int) -> Dict:
    """
    Obtiene estadísticas de participación.
    
    Args:
        activity_id: ID de la actividad
    
    Returns:
        Dict con total_alumnos, han_votado, pendientes, porcentaje
    """
    total = get_students_count()
    voted = get_votes_count_by_activity(activity_id)
    pending = total - voted
    percentage = (voted / total * 100) if total > 0 else 0
    
    return {
        'total_alumnos': total,
        'han_votado': voted,
        'pendientes': pending,
        'porcentaje': round(percentage, 1)
    }


def get_pending_students_list(activity_id: int) -> pd.DataFrame:
    """
    Obtiene la lista de estudiantes que no han votado.
    
    Args:
        activity_id: ID de la actividad
    
    Returns:
        DataFrame con grupo y nombre de estudiantes pendientes
    """
    pending = get_students_pending_vote(activity_id)
    
    if not pending:
        return pd.DataFrame()
    
    data = [{'grupo': s.group_name, 'nombre': s.full_name} for s in pending]
    df = pd.DataFrame(data)
    df = df.sort_values(['grupo', 'nombre']).reset_index(drop=True)
    
    return df


def export_ranking_csv(activity_id: int) -> str:
    """
    Genera el contenido CSV del ranking final.
    
    Args:
        activity_id: ID de la actividad
    
    Returns:
        Contenido CSV como string
    """
    df = get_ranking_results(activity_id)
    if df.empty:
        return ""
    
    return df.to_csv(index=False)


def get_heatmap_data(activity_id: int) -> Tuple[List[List[int]], List[str], List[str]]:
    """
    Obtiene los datos para el heatmap de posiciones.
    
    Returns:
        Tupla (matriz_valores, etiquetas_videos, etiquetas_posiciones)
    """
    dist_df = get_rank_distribution(activity_id)
    
    if dist_df.empty:
        return [], [], []
    
    # Extraer datos
    videos = dist_df['video'].tolist()
    position_cols = [col for col in dist_df.columns if col.startswith('Pos')]
    
    matrix = []
    for _, row in dist_df.iterrows():
        matrix.append([row[col] for col in position_cols])
    
    return matrix, videos, position_cols
