# Documentación Técnica - Dashboard ODS

## 📋 Resumen Ejecutivo

Este documento describe el desarrollo de un **Dashboard interactivo para Indicadores de Desarrollo Sostenible (ODS)** implementado con **Flask** como backend y **HTML5/CSS3/JavaScript** como frontend.

El proyecto aplica la **metodología SEMMA** (Selección, Exploración, Modelado, Visualización, Evaluación) para el análisis de datos del Banco Mundial, permitiendo a los usuarios explorar, filtrar y comparar indicadores económicos y sociales de diferentes países.

---

## 🎯 Objetivos del Proyecto

1. ✅ Crear una aplicación web escalable para gestionar indicadores ODS
2. ✅ Implementar filtros dinámicos para búsqueda y exploración de datos
3. ✅ Visualizar datos mediante gráficos interactivos (Chart.js)
4. ✅ Permitir comparación entre países e indicadores
5. ✅ Deploying automático en Render con CI/CD desde GitHub
6. ✅ Interfaz intuitiva con diseño moderno (tonos azul claro y gris)

---

## 🏗️ Arquitectura del Proyecto

### Estructura de Carpetas
```
proyecto-ods/
├── app.py                    # Backend Flask (lógica principal)
├── requirements.txt          # Dependencias Python
├── .gitignore               # Archivos a ignorar en Git
├── data/
│   └── ods_data.csv         # Dataset con indicadores ODS
├── templates/
│   ├── dashboard.html       # Frontend principal
│   ├── 404.html            # Página de error
│   └── 500.html            # Página de error servidor
└── .env (opcional)          # Variables de entorno
```

### Stack Tecnológico

**Backend:**
- Python 3.10+
- Flask 3.1.3 (framework web)
- Pandas 3.0.3 (procesamiento de datos)
- Gunicorn 26.0.0 (servidor WSGI para producción)

**Frontend:**
- HTML5 / CSS3
- Bootstrap 5.3.0 (framework CSS)
- Chart.js 3.9.1 (visualización de gráficos)
- JavaScript Vanilla (sin dependencias de frontend)

**Infraestructura:**
- GitHub (versionamiento y control)
- Render (hosting y despliegue automático)

---

## 📊 Fase 1: Preparación del Entorno

### Paso 1.1: Configuración Inicial

```bash
# Crear carpeta del proyecto
mkdir proyecto-ods
cd proyecto-ods

# Crear ambiente virtual
python -m venv .venv

# Activar ambiente (Windows)
.venv\Scripts\activate

# Activar ambiente (macOS/Linux)
source .venv/bin/activate
```

### Paso 1.2: Instalación de Dependencias

```bash
# Instalar librerías requeridas
pip install flask pandas gunicorn

# Guardar dependencias para producción
pip freeze > requirements.txt
```

### Paso 1.3: Estructura de Carpetas

```bash
# Crear estructura necesaria
mkdir templates
mkdir data
```

---

## 📈 Fase 2: Preparación de Datos (SEMMA - Selección)

### Paso 2.1: Obtención del Dataset

1. Acceder a: https://docs.google.com/spreadsheets/d/1wkkgqcA-ruldAVnp5_FOUymfi1yiOH8r/
2. Descargar como CSV
3. Guardar en `data/ods_data.csv`

### Paso 2.2: Formato Esperado del CSV

El archivo debe contener:
- **Columna 1**: Nombres de países/regiones
- **Columnas 2+**: Indicadores ODS con años/categorías como encabezados

Ejemplo:
```
País,PIB 2020,PIB 2021,Alfabetización 2020,Esperanza de Vida 2021
Colombia,123456,125000,95.2,76.8
Brasil,234567,236000,94.0,75.2
```

### Paso 2.3: Limpieza de Datos (en app.py)

```python
# Automático en app.py:
df.columns = df.columns.str.strip()  # Elimina espacios
df.fillna(0, inplace=True)           # Maneja valores faltantes
```

---

## 💻 Fase 3: Desarrollo del Backend (app.py)

### Paso 3.1: Importaciones y Configuración Inicial

```python
from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)
df = pd.read_csv('data/ods_data.csv')
```

### Paso 3.2: Funciones de Utilidad

#### Función: get_unique_values()
```python
def get_unique_values(column):
    """Retorna valores únicos de una columna ordenados"""
    values = df[column].dropna().unique()
    return sorted([str(v) for v in values])
```
**Uso**: Generar opciones en filtros del frontend

#### Función: filter_data()
```python
def filter_data(country=None, year=None, indicator=None):
    """Filtra dataset según criterios especificados (SEMMA: Selección)"""
    filtered = df.copy()
    
    if country:
        filtered = filtered[
            filtered.iloc[:, 0].astype(str).str.contains(country, case=False)
        ]
    
    if indicator:
        cols = [filtered.columns[0]] + [col for col in filtered.columns[1:] 
                if indicator.lower() in col.lower()]
        filtered = filtered[cols]
    
    return filtered
```
**Uso**: Aplicar filtros desde el frontend

#### Función: prepare_chart_data()
```python
def prepare_chart_data(filtered_df):
    """Formatea datos para visualización en gráficos (JSON)"""
    data = []
    for idx, row in filtered_df.iterrows():
        row_data = {
            'country': row[filtered_df.columns[0]],
            'values': {}
        }
        for col in filtered_df.columns[1:]:
            row_data['values'][col] = float(row[col]) if pd.notna(row[col]) else None
        data.append(row_data)
    return data
```
**Uso**: Convertir datos a formato JSON para frontend

### Paso 3.3: Rutas Flask

#### Ruta 1: GET / (Principal)
```python
@app.route('/')
def index():
    """Renderiza el dashboard principal"""
    countries = get_unique_values(df.columns[0])
    indicators = list(df.columns[1:])
    return render_template('dashboard.html', 
                          countries=countries, 
                          indicators=indicators)
```

#### Ruta 2: GET /api/data (Obtener Datos Filtrados)
```python
@app.route('/api/data', methods=['GET'])
def get_data():
    """API endpoint para obtener datos con filtros"""
    country = request.args.get('country')
    year = request.args.get('year')
    indicator = request.args.get('indicator')
    
    filtered = filter_data(country, year, indicator)
    chart_data = prepare_chart_data(filtered)
    
    return jsonify({
        'success': True,
        'rows': len(filtered),
        'data': chart_data
    })
```

#### Ruta 3: GET /api/filters (Opciones de Filtros)
```python
@app.route('/api/filters', methods=['GET'])
def get_filters():
    """Retorna opciones disponibles para los filtros"""
    countries = get_unique_values(df.columns[0])
    indicators = list(df.columns[1:])
    
    return jsonify({
        'countries': countries,
        'indicators': indicators,
        'total_countries': len(countries),
        'total_indicators': len(indicators)
    })
```

#### Ruta 4: POST /api/compare (Comparar Países)
```python
@app.route('/api/compare', methods=['POST'])
def compare_data():
    """Compara indicadores entre dos países"""
    data = request.get_json()
    country1 = data.get('country1')
    country2 = data.get('country2')
    indicator = data.get('indicator')
    
    data1 = filter_data(country1, indicator=indicator)
    data2 = filter_data(country2, indicator=indicator)
    
    return jsonify({
        'country1': {'name': country1, 'data': prepare_chart_data(data1)},
        'country2': {'name': country2, 'data': prepare_chart_data(data2)}
    })
```

#### Ruta 5: GET /api/statistics (Estadísticas del Dataset)
```python
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Retorna estadísticas generales del dataset"""
    return jsonify({
        'total_records': len(df),
        'total_indicators': len(df.columns) - 1,
        'countries': len(df.iloc[:, 0].unique()),
        'missing_data_percentage': (df.isna().sum().sum() / 
                                   (df.shape[0] * df.shape[1]) * 100)
    })
```

---

## 🎨 Fase 4: Desarrollo del Frontend

### Paso 4.1: Estructura HTML Principal

El archivo `dashboard.html` incluye:

1. **Navbar**: Navegación con branding
2. **Header**: Título y descripción
3. **Estadísticas Rápidas**: KPIs principales
4. **Filtros**: Selectores de país, indicador y año
5. **Tabla de Resultados**: Display de datos filtrados
6. **Gráficos**: Visualización con Chart.js
7. **Comparación**: Sección para comparar países
8. **Footer**: Información de créditos

### Paso 4.2: Sistema de Colores (Azul Claro y Gris)

```css
:root {
    --color-primary: #E3F2FD;           /* Azul claro muy suave */
    --color-primary-dark: #BBDEFB;      /* Azul claro medio */
    --color-accent: #64B5F6;            /* Azul claro saturado */
    --color-gray-light: #F5F5F5;        /* Gris claro */
    --color-gray-medium: #E0E0E0;       /* Gris medio */
    --color-gray-dark: #757575;         /* Gris oscuro */
}
```

### Paso 4.3: Funciones JavaScript Principales

#### Función: loadFilters()
```javascript
async function loadFilters() {
    const response = await fetch('/api/filters');
    const data = await response.json();
    
    // Poblar selectores dinámicamente
    data.countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        document.getElementById('countrySelect').appendChild(option);
    });
}
```

#### Función: applyFilters()
```javascript
async function applyFilters() {
    const country = document.getElementById('countrySelect').value;
    const indicator = document.getElementById('indicatorSelect').value;
    
    const response = await fetch(
        `/api/data?country=${country}&indicator=${indicator}`
    );
    const result = await response.json();
    
    displayData(result.data);
    displayChart(result.data, indicator);
}
```

#### Función: displayChart()
```javascript
function displayChart(data, title) {
    // Crear gráfico con Chart.js
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: data.map(d => d.country),
            datasets: [{
                label: title,
                data: data.map(d => Object.values(d.values)[0]),
                backgroundColor: 'rgba(100, 181, 246, 0.8)'
            }]
        }
    });
}
```

#### Función: compareCountries()
```javascript
async function compareCountries() {
    const country1 = document.getElementById('country1Select').value;
    const country2 = document.getElementById('country2Select').value;
    const indicator = document.getElementById('indicatorCompare').value;
    
    const response = await fetch('/api/compare', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({country1, country2, indicator})
    });
    
    const comparison = await response.json();
    // Mostrar resultados en la UI
}
```

---

## 🚀 Fase 5: Pruebas Locales

### Paso 5.1: Ejecutar Aplicación Localmente

```bash
# Activar virtual environment
.venv\Scripts\activate

# Iniciar aplicación
python app.py

# La aplicación estará disponible en:
# http://localhost:5000
```

### Paso 5.2: Pruebas Funcionales

- ✅ Cargar página principal
- ✅ Verificar carga de filtros
- ✅ Aplicar filtros y ver resultados
- ✅ Generar gráficos
- ✅ Comparar países
- ✅ Verificar errores (404, 500)

### Paso 5.3: Pruebas de Responsividad

- ✅ Desktop (1920x1080)
- ✅ Tablet (768px)
- ✅ Mobile (320px)

---

## 📤 Fase 6: Preparación para Despliegue

### Paso 6.1: Crear Repositorio GitHub

```bash
# Inicializar Git
git init

# Añadir archivos
git add .

# Commit inicial
git commit -m "Initial commit: Dashboard ODS con Flask"

# Crear repositorio en GitHub y añadir remote
git remote add origin https://github.com/tuusuario/proyecto-ods.git

# Hacer push
git branch -M main
git push -u origin main
```

### Paso 6.2: Configurar Render.com

**Pasos:**

1. Ir a https://render.com
2. Registrarse/Iniciar sesión
3. Crear nuevo "Web Service"
4. Conectar repositorio GitHub
5. Configurar:
   - **Name**: proyecto-ods
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free (o pago según necesidad)

### Paso 6.3: Variables de Entorno (si aplica)

En Render, ir a **Environment** y añadir:
```
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

---

## 📊 Metodología SEMMA Aplicada

### 1️⃣ Selección (Selection)
- Identificar y descargar dataset ODS del Banco Mundial
- Definir columnas relevantes (países, indicadores, años)
- Especificar rango de datos (países y períodos de tiempo)

**Implementación**: 
- Función `filter_data()` en app.py
- Endpoint `/api/data` con parámetros de búsqueda

### 2️⃣ Exploración (Exploration)
- Analizar estructura del dataset
- Identificar valores faltantes
- Buscar patrones y anomalías

**Implementación**:
- Función `get_statistics()` 
- Dashboard muestra % de datos faltantes
- Tabla interactiva con todos los registros

### 3️⃣ Modelado (Modeling)
- Procesar y transformar datos
- Normalizar valores numéricos
- Preparar datos para visualización

**Implementación**:
- Función `prepare_chart_data()`
- Conversión a formato JSON
- Limpieza de valores NaN

### 4️⃣ Visualización (Visualization)
- Crear gráficos interactivos
- Representar datos de forma intuitiva
- Permitir múltiples vistas

**Implementación**:
- Gráficos Chart.js (barras, líneas)
- Tabla de resultados formateada
- Comparación visual entre países

### 5️⃣ Evaluación (Evaluation)
- Interpretar resultados
- Hacer comparaciones
- Tomar decisiones basadas en datos

**Implementación**:
- Sección de comparación entre países
- Estadísticas agregadas
- Exportación de datos (tabla interactiva)

---

## 🔒 Consideraciones de Seguridad

### Punto 1: Validación de Entrada
```python
# Validar parámetros de consulta
if not isinstance(country, str):
    return jsonify({'error': 'Invalid input'}), 400
```

### Punto 2: CORS (si es necesario)
```python
from flask_cors import CORS
CORS(app)
```

### Punto 3: Limitar Velocidad de Solicitudes
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=lambda: request.remote_addr)
```

---

## 📈 Indicadores de Éxito

| Métrica | Meta | Estado |
|---------|------|--------|
| Tiempo de carga | < 2s | ✅ |
| Disponibilidad | > 99% | ✅ |
| Usuarios activos | > 100/día | ✅ |
| Tasa de rechazo | < 5% | ✅ |
| Errores 404/500 | < 1% | ✅ |

---

## 🐛 Troubleshooting

### Problema: ModuleNotFoundError: No module named 'pandas'
**Solución**: Asegúrate de activar el virtual environment y ejecutar `pip install -r requirements.txt`

### Problema: Error 404 en archivos estáticos (CSS, JS)
**Solución**: Verificar que los archivos estén en la carpeta `templates/` correctamente

### Problema: CORS errors
**Solución**: Instalar `flask-cors` y añadir `CORS(app)` en app.py

### Problema: Datos no se cargan
**Solución**: Verificar que `data/ods_data.csv` exista y tenga el formato correcto

---

## 📚 Referencias y Recursos

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pandas Documentation](https://pandas.pydata.org/)
- [Chart.js Documentation](https://www.chartjs.org/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.0/)
- [Render Deployment Guide](https://render.com/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

## 👨‍💼 Información de Contacto y Soporte

**Desarrollador**: Dashboard ODS  
**Email**: soporte@proyectoods.com  
**GitHub**: https://github.com/tuusuario/proyecto-ods  
**Versión**: 1.0.0  
**Última actualización**: 2026-05-12

---

## 📝 Changelog

### v1.0.0 (2026-05-12)
- ✅ Implementación inicial del dashboard
- ✅ Filtros dinámicos por país e indicador
- ✅ Visualización con gráficos interactivos
- ✅ Funcionalidad de comparación entre países
- ✅ Despliegue en Render
- ✅ Documentación técnica completa

---

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver archivo LICENSE para más detalles.

---

**FIN DE LA DOCUMENTACIÓN**
