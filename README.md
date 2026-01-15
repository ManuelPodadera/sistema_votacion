# 🎬 Sistema de Votación de Vídeos

Aplicación web desarrollada con Streamlit para permitir a los alumnos votar y ordenar vídeos, con panel de administración completo.

## 📋 Características

- ✅ **Votación por ranking**: Los alumnos ordenan vídeos de mejor a peor
- ✅ **Un voto por alumno y actividad**: Control de unicidad
- ✅ **Autenticación por whitelist**: Basada en CSV de alumnos
- ✅ **Panel de administración**: Crear actividades, gestionar alumnos/vídeos, ver resultados
- ✅ **Visualización de resultados**: Gráficos con Borda count, heatmaps, participación
- ✅ **Exportación de datos**: CSV de rankings y votos detallados
- ✅ **Persistencia en SQLite**: Base de datos local autocontenida

## 🚀 Instalación

### 1. Requisitos previos
- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### 2. Instalar dependencias

```bash
cd video_ranking_streamlit
pip install -r requirements.txt
```

### 3. Configurar la contraseña de administrador

Edita el archivo `.streamlit/secrets.toml`:

```toml
ADMIN_PASSWORD = "tu_contraseña_segura"
```

### 4. Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

## 📁 Estructura del proyecto

```
video_ranking_streamlit/
├─ app.py                         # Aplicación principal
├─ requirements.txt               # Dependencias
├─ README.md                      # Este archivo
├─ .streamlit/
│  └─ secrets.toml               # Contraseña admin (NO subir a Git)
├─ data/
│  └─ app.db                     # Base de datos SQLite (se crea automáticamente)
├─ src/
│  ├─ __init__.py
│  ├─ db.py                      # Conexión y esquema SQLite
│  ├─ models.py                  # Dataclasses
│  ├─ repo.py                    # CRUD de entidades
│  ├─ auth.py                    # Autenticación
│  ├─ voting.py                  # Lógica de votación
│  ├─ scoring.py                 # Borda count y estadísticas
│  ├─ charts.py                  # Gráficos Plotly
│  └─ utils.py                   # Utilidades (hashing, normalización)
└─ assets/
   └─ templates/
      ├─ alumnos_template.csv    # Plantilla CSV de alumnos
      └─ videos_template.csv     # Plantilla CSV de vídeos
```

## 👤 Roles y uso

### Rol Alumno

1. Selecciona tu **Grupo** del dropdown
2. Selecciona tu **Nombre** 
3. Introduce el **PIN de la actividad** (proporcionado por el profesor)
4. Ordena los vídeos de mejor a peor usando los botones ⬆️⬇️
5. Confirma y envía tu voto

### Rol Administrador

1. Introduce la contraseña de admin
2. Accede a las pestañas:
   - **Actividades**: Crear, abrir/cerrar, duplicar, eliminar
   - **Alumnos**: Importar CSV con whitelist
   - **Vídeos**: Añadir manualmente o importar CSV
   - **Resultados**: Ver ranking, gráficos, exportar
   - **Participación**: Ver quién ha votado y pendientes

## 📊 Formato de los CSV

### CSV de Alumnos

```csv
Grupo,Nombre ALUMNO
"Grupo A","IGNACIO GONZÁLEZ PERIS"
"Grupo A","SAMUEL RODRÍGUEZ CABALLERO"
"Grupo B","ALBERTO ÁGUILA PRIETO"
```

O sin comillas:
```csv
Grupo,Nombre ALUMNO
Grupo A,María Pérez García
Grupo A,Carlos López Martín
Grupo B,Ana Sánchez Ruiz
```

### CSV de Vídeos

```csv
Grupo,Título,URL
A,Video del Grupo A,https://www.youtube.com/watch?v=xxxxx
B,Video del Grupo B,https://www.youtube.com/watch?v=yyyyy
```

## 🔢 Método de puntuación: Borda Count

Si hay **N** vídeos:
- Posición 1 (mejor) → N-1 puntos
- Posición 2 → N-2 puntos
- ...
- Posición N (peor) → 0 puntos

El ranking final se calcula sumando los puntos de todos los votos.

## 🔐 Seguridad

- La contraseña de admin se almacena en `secrets.toml` (no hardcodeada)
- Los PINs de actividad se guardan hasheados (SHA-256 con salt)
- Un alumno solo puede votar una vez por actividad

## ⚠️ Consideraciones de despliegue

### Local / Servidor propio
- La base de datos SQLite persiste en `data/app.db`
- Ideal para uso en clase

### Streamlit Community Cloud
- El filesystem puede no ser persistente tras reinicios
- Para uso permanente, considera:
  - Servidor propio (VM, PC)
  - Migrar a PostgreSQL
  - Almacenamiento externo

## 🛠️ Solución de problemas

### "No hay alumnos registrados"
- El admin debe importar el CSV de alumnos primero

### "PIN incorrecto"
- Verifica que el PIN coincide exactamente con el configurado

### "Ya has votado en esta actividad"
- Cada alumno solo puede votar una vez por actividad
- Si necesitas permitir revotación, el admin debe gestionar la base de datos

### Los vídeos no se reproducen
- Verifica que las URLs son válidas
- YouTube, Vimeo y otros servicios compatibles con `st.video()`

## 📝 Licencia

Desarrollado para uso educativo - Universidad Loyola, Máster 2025-26
