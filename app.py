"""
Aplicación principal de Sistema de Votación de Vídeos.
Universidad Loyola - Máster 2025-26

Ejecutar con: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from io import StringIO

# Importar módulos propios
from src.db import init_database
from src.auth import (
    login_admin, logout_admin, is_admin_logged_in,
    login_student, logout_student, is_student_logged_in,
    get_current_student_id, get_current_activity_id
)
from src.repo import (
    get_all_students, get_groups, get_students_by_group,
    import_students_from_df, get_students_count, delete_all_students,
    get_all_activities, get_open_activities, get_activity_by_id,
    create_activity, update_activity, update_activity_status,
    delete_activity, duplicate_activity,
    get_videos_by_activity, get_video_by_id,
    create_video, update_video, delete_video, import_videos_from_df,
    has_student_voted, get_votes_count_by_activity,
    get_detailed_votes_for_export
)
from src.models import ActivityStatus
from src.voting import (
    initialize_video_order, get_current_video_order,
    move_video_up, move_video_down, get_rankings_from_order,
    submit_vote
)
from src.scoring import (
    get_ranking_results, get_rank_distribution, get_rank_statistics,
    get_participation_stats, get_pending_students_list, export_ranking_csv
)
from src.charts import (
    create_borda_bar_chart, create_rank_heatmap,
    create_participation_gauge, create_participation_pie,
    create_rank_distribution_bars
)
from src.utils import format_datetime_display

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Votación de Vídeos",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar base de datos
init_database()


def main():
    """Función principal de la aplicación."""
    
    # Sidebar para navegación
    st.sidebar.title("🎬 Sistema de Votación")
    st.sidebar.markdown("---")
    
    # Selector de modo
    if is_admin_logged_in():
        mode = "Admin"
        st.sidebar.success("✅ Sesión de Administrador")
        if st.sidebar.button("🚪 Cerrar sesión Admin"):
            logout_admin()
            st.rerun()
    elif is_student_logged_in():
        mode = "Alumno"
        st.sidebar.success(f"✅ {st.session_state.get('student_name', 'Alumno')}")
        if st.sidebar.button("🚪 Cerrar sesión"):
            logout_student()
            st.rerun()
    else:
        mode = st.sidebar.radio(
            "Selecciona tu rol:",
            ["Alumno", "Admin"],
            index=0
        )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Universidad Loyola - Máster 2025-26")
    
    # Renderizar según el modo
    if mode == "Admin":
        render_admin_section()
    else:
        render_student_section()


# =============================================================================
# SECCIÓN DE ESTUDIANTE
# =============================================================================

def render_student_section():
    """Renderiza la sección de estudiante."""
    
    if not is_student_logged_in():
        render_student_login()
    else:
        if st.session_state.get('vote_submitted', False):
            render_vote_confirmation()
        else:
            render_voting_interface()


def render_student_login():
    """Renderiza la pantalla de login de estudiante."""
    
    st.title("🎓 Portal del Alumno")
    st.markdown("---")
    
    # Obtener actividades abiertas
    open_activities = get_open_activities()
    
    if not open_activities:
        st.warning("⚠️ No hay actividades abiertas para votar en este momento.")
        st.info("Por favor, espera a que el profesor abra una actividad de votación.")
        return
    
    # Selección de actividad
    if len(open_activities) == 1:
        selected_activity = open_activities[0]
        st.info(f"📋 Actividad: **{selected_activity.title}**")
    else:
        activity_options = {a.title: a for a in open_activities}
        selected_title = st.selectbox(
            "Selecciona la actividad:",
            options=list(activity_options.keys())
        )
        selected_activity = activity_options[selected_title]
    
    if selected_activity.description:
        st.markdown(f"*{selected_activity.description}*")
    
    st.markdown("---")
    st.subheader("🔐 Identificación")
    
    # Obtener grupos
    groups = get_groups()
    
    if not groups:
        st.error("❌ No hay alumnos registrados en el sistema.")
        st.info("El profesor debe importar la lista de alumnos.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_group = st.selectbox(
            "Tu grupo:",
            options=groups,
            index=0
        )
    
    # Filtrar estudiantes por grupo
    students_in_group = get_students_by_group(selected_group)
    student_names = [s.full_name for s in students_in_group]
    
    with col2:
        selected_name = st.selectbox(
            "Tu nombre:",
            options=student_names,
            index=0 if student_names else None
        )
    
    # PIN de acceso
    pin = st.text_input(
        "PIN de la actividad:",
        type="password",
        placeholder="Introduce el PIN proporcionado por el profesor"
    )
    
    # Botón de login
    if st.button("🚀 Acceder a la votación", type="primary", use_container_width=True):
        if not selected_name:
            st.error("Por favor, selecciona tu nombre")
        elif not pin:
            st.error("Por favor, introduce el PIN de la actividad")
        else:
            success, error = login_student(
                selected_group, 
                selected_name, 
                selected_activity.id, 
                pin
            )
            
            if success:
                st.success("✅ ¡Bienvenido/a!")
                st.rerun()
            else:
                st.error(f"❌ {error}")


def render_voting_interface():
    """Renderiza la interfaz de votación."""
    
    activity_id = get_current_activity_id()
    student_id = get_current_student_id()
    
    activity = get_activity_by_id(activity_id)
    if not activity:
        st.error("Actividad no encontrada")
        logout_student()
        st.rerun()
        return
    
    # Verificar que la actividad sigue abierta
    if activity.status != ActivityStatus.OPEN:
        st.warning("⚠️ La actividad ha sido cerrada.")
        logout_student()
        st.rerun()
        return
    
    # Verificar si ya votó (por si acaso)
    if has_student_voted(activity_id, student_id):
        st.session_state['vote_submitted'] = True
        st.rerun()
        return
    
    st.title(f"🎬 {activity.title}")
    st.markdown(f"**Alumno:** {st.session_state.get('student_name')} | **Grupo:** {st.session_state.get('student_group')}")
    st.markdown("---")
    
    # Inicializar orden de vídeos
    initialize_video_order(activity_id)
    
    videos = get_videos_by_activity(activity_id)
    if not videos:
        st.warning("No hay vídeos disponibles para esta actividad.")
        return
    
    video_dict = {v.id: v for v in videos}
    current_order = get_current_video_order()
    
    st.subheader("📊 Ordena los vídeos de MEJOR a PEOR")
    st.info("🔼 Usa los botones para mover los vídeos. El vídeo en la posición 1 es el MEJOR.")
    
    # Mostrar vídeos ordenados
    for idx, video_id in enumerate(current_order):
        video = video_dict.get(video_id)
        if not video:
            continue
        
        position = idx + 1
        
        with st.container():
            col_pos, col_content, col_buttons = st.columns([1, 8, 2])
            
            with col_pos:
                if position == 1:
                    st.markdown(f"### 🥇 {position}")
                elif position == 2:
                    st.markdown(f"### 🥈 {position}")
                elif position == 3:
                    st.markdown(f"### 🥉 {position}")
                else:
                    st.markdown(f"### {position}")
            
            with col_content:
                with st.expander(f"**{video.title}** - Grupo {video.group_name}", expanded=False):
                    st.video(video.video_url)
            
            with col_buttons:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if idx > 0:
                        if st.button("⬆️", key=f"up_{video_id}", help="Subir (mejor posición)"):
                            move_video_up(video_id)
                            st.rerun()
                with btn_col2:
                    if idx < len(current_order) - 1:
                        if st.button("⬇️", key=f"down_{video_id}", help="Bajar (peor posición)"):
                            move_video_down(video_id)
                            st.rerun()
        
        st.markdown("---")
    
    # Botón de enviar
    st.markdown("### 📤 Enviar votación")
    
    # Mostrar resumen
    with st.expander("📋 Resumen de tu ranking", expanded=True):
        for idx, video_id in enumerate(current_order):
            video = video_dict.get(video_id)
            if video:
                st.write(f"**{idx + 1}.** {video.title} (Grupo {video.group_name})")
    
    st.warning("⚠️ **Una vez enviado el voto, no podrás modificarlo.**")
    
    if st.button("✅ CONFIRMAR Y ENVIAR VOTO", type="primary", use_container_width=True):
        rankings = get_rankings_from_order()
        success, message = submit_vote(activity_id, student_id, rankings)
        
        if success:
            st.session_state['vote_submitted'] = True
            st.success(message)
            st.rerun()
        else:
            st.error(f"❌ {message}")


def render_vote_confirmation():
    """Renderiza la confirmación de voto enviado."""
    
    st.title("✅ ¡Voto Registrado!")
    st.balloons()
    
    st.success("Tu voto ha sido registrado correctamente.")
    
    st.markdown("---")
    st.markdown(f"""
    ### Detalles:
    - **Alumno:** {st.session_state.get('student_name')}
    - **Grupo:** {st.session_state.get('student_group')}
    """)
    
    st.info("Gracias por participar. Puedes cerrar esta ventana.")
    
    if st.button("🔄 Volver al inicio"):
        logout_student()
        st.rerun()


# =============================================================================
# SECCIÓN DE ADMINISTRADOR
# =============================================================================

def render_admin_section():
    """Renderiza la sección de administrador."""
    
    if not is_admin_logged_in():
        render_admin_login()
    else:
        render_admin_dashboard()


def render_admin_login():
    """Renderiza la pantalla de login de administrador."""
    
    st.title("🔐 Acceso de Administrador")
    st.markdown("---")
    
    password = st.text_input(
        "Contraseña de administrador:",
        type="password"
    )
    
    if st.button("Acceder", type="primary"):
        if login_admin(password):
            st.success("✅ Acceso concedido")
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")


def render_admin_dashboard():
    """Renderiza el panel de administración."""
    
    st.title("⚙️ Panel de Administración")
    st.markdown("---")
    
    # Tabs de administración
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Actividades",
        "👥 Alumnos",
        "🎥 Vídeos",
        "📊 Resultados",
        "📈 Participación"
    ])
    
    with tab1:
        render_activities_management()
    
    with tab2:
        render_students_management()
    
    with tab3:
        render_videos_management()
    
    with tab4:
        render_results_view()
    
    with tab5:
        render_participation_view()


def render_activities_management():
    """Renderiza la gestión de actividades."""
    
    st.subheader("📋 Gestión de Actividades")
    
    # Formulario para crear actividad
    with st.expander("➕ Crear nueva actividad", expanded=False):
        with st.form("new_activity_form"):
            title = st.text_input("Título de la actividad*")
            description = st.text_area("Descripción (opcional)")
            pin = st.text_input("PIN de acceso*", placeholder="Ej: LOYOLA-2026")
            
            submitted = st.form_submit_button("Crear actividad", type="primary")
            
            if submitted:
                if not title:
                    st.error("El título es obligatorio")
                elif not pin:
                    st.error("El PIN es obligatorio")
                else:
                    activity_id = create_activity(title, description, pin)
                    st.success(f"✅ Actividad creada (ID: {activity_id})")
                    st.rerun()
    
    st.markdown("---")
    
    # Lista de actividades
    activities = get_all_activities()
    
    if not activities:
        st.info("No hay actividades creadas.")
        return
    
    for activity in activities:
        status_emoji = {
            "DRAFT": "📝",
            "OPEN": "🟢",
            "CLOSED": "🔴"
        }.get(activity.status.value, "❓")
        
        with st.container():
            col1, col2, col3 = st.columns([4, 2, 3])
            
            with col1:
                st.markdown(f"### {status_emoji} {activity.title}")
                if activity.description:
                    st.caption(activity.description)
                st.caption(f"Creada: {format_datetime_display(activity.created_at)}")
            
            with col2:
                n_videos = len(get_videos_by_activity(activity.id))
                n_votes = get_votes_count_by_activity(activity.id)
                st.metric("Vídeos", n_videos)
                st.metric("Votos", n_votes)
            
            with col3:
                # Botones de acción según estado
                if activity.status == ActivityStatus.DRAFT:
                    if st.button("🟢 Abrir votación", key=f"open_{activity.id}"):
                        update_activity_status(activity.id, ActivityStatus.OPEN)
                        st.success("Actividad abierta")
                        st.rerun()
                elif activity.status == ActivityStatus.OPEN:
                    if st.button("🔴 Cerrar votación", key=f"close_{activity.id}"):
                        update_activity_status(activity.id, ActivityStatus.CLOSED)
                        st.success("Actividad cerrada")
                        st.rerun()
                else:  # CLOSED
                    if st.button("🔄 Reabrir", key=f"reopen_{activity.id}"):
                        update_activity_status(activity.id, ActivityStatus.OPEN)
                        st.rerun()
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("📋 Duplicar", key=f"dup_{activity.id}"):
                        new_id = duplicate_activity(activity.id)
                        st.success(f"Actividad duplicada (ID: {new_id})")
                        st.rerun()
                with col_b:
                    if st.button("🗑️ Eliminar", key=f"del_{activity.id}"):
                        if n_votes > 0:
                            st.warning("⚠️ Esta actividad tiene votos. Confirma la eliminación.")
                            if st.button("⚠️ CONFIRMAR ELIMINACIÓN", key=f"confirm_del_{activity.id}"):
                                delete_activity(activity.id)
                                st.rerun()
                        else:
                            delete_activity(activity.id)
                            st.rerun()
        
        st.markdown("---")


def render_students_management():
    """Renderiza la gestión de alumnos."""
    
    st.subheader("👥 Gestión de Alumnos (Whitelist)")
    
    # Estadísticas
    total_students = get_students_count()
    groups = get_groups()
    
    col1, col2 = st.columns(2)
    col1.metric("Total alumnos", total_students)
    col2.metric("Grupos", len(groups))
    
    st.markdown("---")
    
    # Importación de CSV
    st.markdown("### 📤 Importar alumnos desde CSV")
    
    st.info("""
    **Formato del CSV:**
    - El archivo debe tener columnas `Grupo` y `Nombre ALUMNO` (o similares)
    - Puedes usar comillas para los valores
    - Se normalizarán los espacios automáticamente
    """)
    
    uploaded_file = st.file_uploader(
        "Selecciona el archivo CSV",
        type=['csv'],
        key="students_csv"
    )
    
    if uploaded_file is not None:
        try:
            # Intentar diferentes encodings
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='latin-1')
            
            st.markdown("**Vista previa:**")
            st.dataframe(df.head(10))
            
            # Detectar columnas
            cols = df.columns.tolist()
            
            col1, col2 = st.columns(2)
            with col1:
                group_col = st.selectbox(
                    "Columna del Grupo:",
                    options=cols,
                    index=0
                )
            with col2:
                name_col = st.selectbox(
                    "Columna del Nombre:",
                    options=cols,
                    index=min(1, len(cols)-1)
                )
            
            if st.button("📥 Importar alumnos", type="primary"):
                inserted, updated = import_students_from_df(df, group_col, name_col)
                st.success(f"✅ Importación completada: {inserted} nuevos, {updated} actualizados")
                st.rerun()
        
        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")
    
    st.markdown("---")
    
    # Lista de alumnos
    st.markdown("### 📋 Alumnos registrados")
    
    students = get_all_students()
    
    if students:
        df_students = pd.DataFrame([
            {"Grupo": s.group_name, "Nombre": s.full_name}
            for s in students
        ])
        
        # Filtro por grupo
        selected_group = st.selectbox(
            "Filtrar por grupo:",
            options=["Todos"] + groups
        )
        
        if selected_group != "Todos":
            df_students = df_students[df_students["Grupo"] == selected_group]
        
        st.dataframe(df_students, use_container_width=True)
        
        # Botón para descargar
        csv = df_students.to_csv(index=False)
        st.download_button(
            "📥 Descargar lista actual",
            data=csv,
            file_name="alumnos_exportados.csv",
            mime="text/csv"
        )
    else:
        st.info("No hay alumnos registrados.")


def render_videos_management():
    """Renderiza la gestión de vídeos."""
    
    st.subheader("🎥 Gestión de Vídeos")
    
    # Selector de actividad
    activities = get_all_activities()
    
    if not activities:
        st.warning("Primero debes crear una actividad.")
        return
    
    activity_options = {f"{a.title} ({a.status.value})": a for a in activities}
    selected_title = st.selectbox(
        "Selecciona la actividad:",
        options=list(activity_options.keys())
    )
    selected_activity = activity_options[selected_title]
    
    # Mostrar número de vídeos actuales
    current_videos = get_videos_by_activity(selected_activity.id)
    st.info(f"📊 Esta actividad tiene actualmente **{len(current_videos)} vídeos**")
    
    st.markdown("---")
    
    # ==========================================
    # IMPORTACIÓN MASIVA CSV (DESTACADA)
    # ==========================================
    st.markdown("### 📤 Importar vídeos desde CSV (Recomendado)")
    
    st.success("""
    **📋 Formato del CSV de vídeos:**
    
    El archivo debe tener 3 columnas (los nombres pueden variar):
    - **Grupo**: Nombre del grupo (ej: "Grupo A", "A", "GRUPO A")
    - **Título**: Título descriptivo del vídeo
    - **URL**: Enlace al vídeo (YouTube, Vimeo, etc.)
    
    **Ejemplo:**
    ```
    Grupo,Título,URL
    Grupo A,Presentación del Proyecto,https://www.youtube.com/watch?v=xxxxx
    Grupo B,Demo de la Aplicación,https://www.youtube.com/watch?v=yyyyy
    ```
    """)
    
    # Botón para descargar plantilla
    plantilla_csv = """Grupo,Título,URL
Grupo A,Presentación del Proyecto - Equipo A,https://www.youtube.com/watch?v=XXXXXX
Grupo B,Demo de la Aplicación - Equipo B,https://www.youtube.com/watch?v=YYYYYY
Grupo C,Prototipo Final - Equipo C,https://www.youtube.com/watch?v=ZZZZZZ
"""
    st.download_button(
        "📥 Descargar plantilla CSV de ejemplo",
        data=plantilla_csv,
        file_name="plantilla_videos.csv",
        mime="text/csv",
        help="Descarga esta plantilla, rellénala con tus datos y súbela"
    )
    
    video_file = st.file_uploader(
        "📁 Selecciona el archivo CSV con los vídeos",
        type=['csv'],
        key="videos_csv",
        help="Sube un archivo CSV con las columnas: Grupo, Título, URL"
    )
    
    if video_file is not None:
        try:
            # Intentar diferentes encodings
            try:
                df_videos = pd.read_csv(video_file, encoding='utf-8')
            except:
                video_file.seek(0)
                df_videos = pd.read_csv(video_file, encoding='latin-1')
            
            st.markdown("**� Vista previa del archivo:**")
            st.dataframe(df_videos, use_container_width=True)
            
            st.markdown(f"**Total de filas:** {len(df_videos)}")
            
            # Detectar columnas automáticamente
            cols = df_videos.columns.tolist()
            
            # Intentar detectar columnas por nombre
            def find_column(keywords, columns):
                for kw in keywords:
                    for i, col in enumerate(columns):
                        if kw.lower() in col.lower():
                            return i
                return 0
            
            grupo_idx = find_column(['grupo', 'group'], cols)
            titulo_idx = find_column(['titulo', 'título', 'title', 'nombre', 'name'], cols)
            url_idx = find_column(['url', 'enlace', 'link', 'video'], cols)
            
            st.markdown("**🔧 Mapeo de columnas:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                vg_col = st.selectbox(
                    "📁 Columna GRUPO:", 
                    cols, 
                    index=grupo_idx, 
                    key="vg_col"
                )
            with col2:
                vt_col = st.selectbox(
                    "📝 Columna TÍTULO:", 
                    cols, 
                    index=min(titulo_idx, len(cols)-1), 
                    key="vt_col"
                )
            with col3:
                vu_col = st.selectbox(
                    "🔗 Columna URL:", 
                    cols, 
                    index=min(url_idx, len(cols)-1), 
                    key="vu_col"
                )
            
            # Mostrar preview del mapeo
            st.markdown("**� Preview con el mapeo seleccionado:**")
            preview_df = df_videos[[vg_col, vt_col, vu_col]].head(5).copy()
            preview_df.columns = ['Grupo', 'Título', 'URL']
            st.dataframe(preview_df, use_container_width=True)
            
            if st.button("✅ IMPORTAR VÍDEOS", type="primary", use_container_width=True):
                count = import_videos_from_df(selected_activity.id, df_videos, vg_col, vt_col, vu_col)
                st.success(f"✅ ¡{count} vídeos importados correctamente!")
                st.balloons()
                st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")
    
    st.markdown("---")
    
    # ==========================================
    # ALTA MANUAL (SECUNDARIA)
    # ==========================================
    with st.expander("➕ Añadir vídeo manualmente (uno a uno)", expanded=False):
        with st.form("new_video_form"):
            v_group = st.text_input("Grupo del vídeo*", placeholder="Ej: GRUPO A")
            v_title = st.text_input("Título del vídeo*", placeholder="Ej: Presentación del proyecto")
            v_url = st.text_input("URL del vídeo*", placeholder="https://www.youtube.com/watch?v=...")
            
            submitted = st.form_submit_button("Añadir vídeo", type="primary")
            
            if submitted:
                if not v_group or not v_title or not v_url:
                    st.error("Todos los campos son obligatorios")
                else:
                    create_video(selected_activity.id, v_group, v_title, v_url)
                    st.success("✅ Vídeo añadido")
                    st.rerun()
    
    st.markdown("---")
    
    # Lista de vídeos
    st.markdown("### 📋 Vídeos de la actividad")
    
    videos = get_videos_by_activity(selected_activity.id)
    
    if not videos:
        st.info("No hay vídeos en esta actividad.")
        return
    
    for video in videos:
        with st.container():
            col1, col2, col3 = st.columns([6, 2, 2])
            
            with col1:
                st.markdown(f"**{video.title}**")
                st.caption(f"Grupo: {video.group_name}")
                with st.expander("Ver vídeo", expanded=False):
                    st.video(video.video_url)
            
            with col2:
                st.text(video.video_url[:30] + "...")
            
            with col3:
                if st.button("🗑️", key=f"del_video_{video.id}", help="Eliminar vídeo"):
                    delete_video(video.id)
                    st.rerun()
        
        st.markdown("---")


def render_results_view():
    """Renderiza la vista de resultados."""
    
    st.subheader("📊 Resultados de Votación")
    
    # Selector de actividad
    activities = get_all_activities()
    
    if not activities:
        st.warning("No hay actividades.")
        return
    
    activity_options = {f"{a.title} ({a.status.value})": a for a in activities}
    selected_title = st.selectbox(
        "Selecciona la actividad:",
        options=list(activity_options.keys()),
        key="results_activity"
    )
    selected_activity = activity_options[selected_title]
    
    n_votes = get_votes_count_by_activity(selected_activity.id)
    
    if n_votes == 0:
        st.info("No hay votos registrados en esta actividad.")
        return
    
    st.metric("Total de votos", n_votes)
    st.markdown("---")
    
    # Ranking final
    st.markdown("### 🏆 Ranking Final (Borda Count)")
    
    ranking_df = get_ranking_results(selected_activity.id)
    
    if not ranking_df.empty:
        # Mostrar tabla
        display_df = ranking_df[['posicion', 'titulo', 'grupo', 'puntos_borda']].copy()
        display_df.columns = ['Posición', 'Vídeo', 'Grupo', 'Puntos Borda']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Gráfico de barras
        fig_bar = create_borda_bar_chart(selected_activity.id)
        if fig_bar:
            st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    
    # Heatmap de distribución
    st.markdown("### 🔥 Distribución de Posiciones")
    
    fig_heatmap = create_rank_heatmap(selected_activity.id)
    if fig_heatmap:
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Barras apiladas
    fig_stacked = create_rank_distribution_bars(selected_activity.id)
    if fig_stacked:
        st.plotly_chart(fig_stacked, use_container_width=True)
    
    st.markdown("---")
    
    # Estadísticas de dispersión
    st.markdown("### 📈 Estadísticas de Ranking")
    
    stats_df = get_rank_statistics(selected_activity.id)
    if not stats_df.empty:
        stats_df.columns = ['Vídeo', 'Media Rank', 'Desv. Estándar']
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Exportación
    st.markdown("### 💾 Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_ranking = export_ranking_csv(selected_activity.id)
        if csv_ranking:
            st.download_button(
                "📥 Descargar Ranking (CSV)",
                data=csv_ranking,
                file_name=f"ranking_{selected_activity.title}.csv",
                mime="text/csv"
            )
    
    with col2:
        detailed_df = get_detailed_votes_for_export(selected_activity.id)
        if not detailed_df.empty:
            csv_detailed = detailed_df.to_csv(index=False)
            st.download_button(
                "📥 Descargar Votos Detallados (CSV)",
                data=csv_detailed,
                file_name=f"votos_detallados_{selected_activity.title}.csv",
                mime="text/csv"
            )


def render_participation_view():
    """Renderiza la vista de participación."""
    
    st.subheader("📈 Participación")
    
    # Selector de actividad
    activities = get_all_activities()
    
    if not activities:
        st.warning("No hay actividades.")
        return
    
    activity_options = {f"{a.title} ({a.status.value})": a for a in activities}
    selected_title = st.selectbox(
        "Selecciona la actividad:",
        options=list(activity_options.keys()),
        key="participation_activity"
    )
    selected_activity = activity_options[selected_title]
    
    # Estadísticas de participación
    stats = get_participation_stats(selected_activity.id)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Alumnos", stats['total_alumnos'])
    col2.metric("Han Votado", stats['han_votado'])
    col3.metric("Pendientes", stats['pendientes'])
    col4.metric("Participación", f"{stats['porcentaje']}%")
    
    st.markdown("---")
    
    # Gráficos de participación
    col1, col2 = st.columns(2)
    
    with col1:
        fig_gauge = create_participation_gauge(selected_activity.id)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    with col2:
        fig_pie = create_participation_pie(selected_activity.id)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # Lista de pendientes
    st.markdown("### ⏳ Alumnos Pendientes de Votar")
    
    pending_df = get_pending_students_list(selected_activity.id)
    
    if not pending_df.empty:
        # Filtro por grupo
        groups = pending_df['grupo'].unique().tolist()
        selected_group = st.selectbox(
            "Filtrar por grupo:",
            options=["Todos"] + groups,
            key="pending_group_filter"
        )
        
        if selected_group != "Todos":
            pending_df = pending_df[pending_df['grupo'] == selected_group]
        
        st.dataframe(pending_df, use_container_width=True, hide_index=True)
        
        # Descargar lista
        csv_pending = pending_df.to_csv(index=False)
        st.download_button(
            "📥 Descargar lista de pendientes",
            data=csv_pending,
            file_name=f"pendientes_{selected_activity.title}.csv",
            mime="text/csv"
        )
    else:
        st.success("✅ ¡Todos los alumnos han votado!")


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    main()
