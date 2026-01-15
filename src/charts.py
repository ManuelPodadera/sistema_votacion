"""
Módulo de gráficos.
Genera visualizaciones con Plotly.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional

from .scoring import (
    get_ranking_results,
    get_rank_distribution,
    get_heatmap_data,
    get_participation_stats
)


def create_borda_bar_chart(activity_id: int, title: str = "Ranking por Puntos Borda") -> Optional[go.Figure]:
    """
    Crea un gráfico de barras con los puntos Borda.
    
    Args:
        activity_id: ID de la actividad
        title: Título del gráfico
    
    Returns:
        Figura de Plotly o None si no hay datos
    """
    df = get_ranking_results(activity_id)
    
    if df.empty:
        return None
    
    # Crear etiqueta combinada
    df['etiqueta'] = df['titulo'] + ' (' + df['grupo'] + ')'
    
    fig = px.bar(
        df,
        x='etiqueta',
        y='puntos_borda',
        title=title,
        labels={'etiqueta': 'Vídeo', 'puntos_borda': 'Puntos Borda'},
        color='puntos_borda',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        showlegend=False,
        height=500
    )
    
    return fig


def create_rank_heatmap(activity_id: int, title: str = "Distribución de Posiciones") -> Optional[go.Figure]:
    """
    Crea un heatmap de distribución de posiciones.
    
    Args:
        activity_id: ID de la actividad
        title: Título del gráfico
    
    Returns:
        Figura de Plotly o None si no hay datos
    """
    matrix, videos, positions = get_heatmap_data(activity_id)
    
    if not matrix:
        return None
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=positions,
        y=videos,
        colorscale='YlOrRd',
        text=matrix,
        texttemplate='%{text}',
        textfont={"size": 12},
        hovertemplate='Vídeo: %{y}<br>Posición: %{x}<br>Votos: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Posición',
        yaxis_title='Vídeo',
        height=max(400, len(videos) * 40)
    )
    
    return fig


def create_participation_gauge(activity_id: int) -> go.Figure:
    """
    Crea un indicador de participación.
    
    Args:
        activity_id: ID de la actividad
    
    Returns:
        Figura de Plotly
    """
    stats = get_participation_stats(activity_id)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=stats['porcentaje'],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Participación (%)"},
        delta={'reference': 100},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"},
                {'range': [80, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    fig.update_layout(height=300)
    
    return fig


def create_participation_pie(activity_id: int) -> go.Figure:
    """
    Crea un gráfico de tarta de participación.
    
    Args:
        activity_id: ID de la actividad
    
    Returns:
        Figura de Plotly
    """
    stats = get_participation_stats(activity_id)
    
    fig = go.Figure(data=[go.Pie(
        labels=['Han votado', 'Pendientes'],
        values=[stats['han_votado'], stats['pendientes']],
        hole=.4,
        marker_colors=['#28a745', '#dc3545']
    )])
    
    fig.update_layout(
        title="Estado de Votación",
        height=350
    )
    
    return fig


def create_rank_distribution_bars(activity_id: int) -> Optional[go.Figure]:
    """
    Crea un gráfico de barras apiladas con la distribución de posiciones.
    
    Args:
        activity_id: ID de la actividad
    
    Returns:
        Figura de Plotly o None si no hay datos
    """
    df = get_rank_distribution(activity_id)
    
    if df.empty:
        return None
    
    position_cols = [col for col in df.columns if col.startswith('Pos')]
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3[:len(position_cols)]
    
    for i, col in enumerate(position_cols):
        fig.add_trace(go.Bar(
            name=col,
            x=df['video'],
            y=df[col],
            marker_color=colors[i % len(colors)]
        ))
    
    fig.update_layout(
        barmode='stack',
        title='Distribución de Votos por Posición',
        xaxis_title='Vídeo',
        yaxis_title='Número de Votos',
        xaxis_tickangle=-45,
        height=500,
        legend_title='Posición'
    )
    
    return fig
