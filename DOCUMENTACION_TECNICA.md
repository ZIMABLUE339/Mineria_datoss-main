# Documentación Técnica — ODS Explorer

**Versión:** 2.0.0 · **Última actualización:** 2026-05-16

---

## 📋 Resumen Ejecutivo

**ODS Explorer** es una plataforma web multi-página para explorar, filtrar, comparar y visualizar los Indicadores de Desarrollo Sostenible del Banco Mundial. El sistema está construido sobre **Flask + Pandas** en el backend y **Tailwind CSS + Chart.js** en el frontend, aplicando la metodología **SEMMA** en toda su arquitectura.

La versión 2.0 incorpora una navegación global unificada de 5 módulos, un dashboard enriquecido con ranking, radar, clasificación por ingreso y comparación avanzada, y páginas preparadas para los módulos de Modelo Multidimensional, Orange y Apache Spark.

---

## 🎯 Objetivos del Proyecto

1. ✅ Plataforma web multi-página con navegación global unificada
2. ✅ Dashboard interactivo con filtros requeridos y validación
3. ✅ Visualizaciones múltiples: barras, línea, radar, ranking, distribución de ingreso
4. ✅ Comparación de dos países con año independiente y banderas
5. ✅ Ranking global top/bottom por indicador y año con filtros propios
6. ✅ Clasificación de países por nivel de ingreso (Banco Mundial)
7. ✅ Páginas base para Modelo Multidimensional, Orange y Spark
8. ✅ Despliegue automático en Render con CI/CD desde GitHub

---

## 🏗️ Arquitectura del Proyecto

### Estructura de carpetas

```
proyecto-ods/
├── app.py                       # Backend Flask — lógica principal
├── requirements.txt             # Dependencias Python
├── render.yaml                  # Configuración despliegue Render
├── .gitignore
├── .env.example
├── data/
│   └── ods_data.csv             # Dataset ODS — 13.000+ registros, 21 columnas
├── templates/
│   ├── home.html                # Página de inicio — explica el sistema
│   ├── dashboard.html           # Dashboard principal — 79KB, 1.470+ líneas
│   ├── multidimensional.html    # Módulo Modelo Multidimensional (base)
│   ├── orange.html              # Módulo Orange Data Mining (base)
│   ├── spark.html               # Módulo Apache Spark (base)
│   ├── 404.html                 # Error 404
│   └── 500.html                 # Error 500
└── static/
    └── css/                     # (sin uso activo — estilos migrados a Tailwind CDN)
```

### Stack tecnológico

**Backend:**
- Python 3.10+
- Flask 3.1.x — framework web, rutas y API REST
- Pandas 3.x — procesamiento, filtrado y agregación del dataset
- Gunicorn 26.x — servidor WSGI para producción

**Frontend:**
- Tailwind CSS (CDN) — sistema de diseño utilitario, reemplaza Bootstrap
- Chart.js 4.x — gráficos de barras, línea, radar y comparación
- JavaScript Vanilla (ES2020+) — sin frameworks de frontend
- Google Fonts: Inter + JetBrains Mono

**Dataset:**
- Fuente: Banco Mundial / Google Sheets ODS
- Formato: CSV, ~13.100 filas × 21 columnas
- Columnas clave: `Año`, `Grupo regional`, `País` + 18 indicadores numéricos
- Indicadores: PIB Total, PIB per cápita, Tasa de crecimiento, Esperanza de vida, Tasa de desempleo, Alfabetización (juvenil y adultos), Matrículas (primaria, secundaria, terciaria), Población activa, totales de población por tramo de edad, entre otros

**Infraestructura:**
- GitHub — versionamiento y control de cambios
- Render — hosting con CI/CD automático al hacer push a `main`

---

## 📊 Dataset — Estructura del CSV

```
Año | Grupo regional | País | PIB Total | Tasa de crecimiento del PIB |
PIB per cápita | Tasa de alfabetización juvenil | Tasa de alfabetización de adultos |
Matriculación en primaria | Matriculación en secundaria | Matriculación en escuelas terciarias |
Población activa Mujer | Población activa Hombres | Población activa Total |
Tasa de desempleo | Esperanza de vida | Población de 0 a 14 años |
Población de 15 a 64 años | Población mayor de 65 años | Población Total |
Población femenina y masculina
```

- `Año` — año del registro (1960–2024, cobertura irregular por país)
- `País` — 202 países únicos
- Las 18 columnas restantes son indicadores numéricos directamente consultables

---

## 🔀 Rutas Flask

| Método | Ruta | Función | Descripción |
|--------|------|---------|-------------|
| GET | `/` | `home()` | Página de inicio |
| GET | `/dashboard` | `dashboard()` | Dashboard principal con filtros |
| GET | `/multidimensional` | `multidimensional()` | Módulo multidimensional (base) |
| GET | `/orange` | `orange()` | Módulo Orange (base) |
| GET | `/spark` | `spark()` | Módulo Spark (base) |
| GET | `/api/filters` | `get_filters()` | Países, años e indicadores disponibles |
| GET | `/api/data` | `get_data()` | Datos filtrados por país, indicador, año |
| POST | `/api/compare` | `compare_data()` | Comparación entre dos países |
| GET | `/api/statistics` | `get_statistics()` | KPIs del dataset completo |
| GET | `/api/ranking` | `get_ranking()` | Top/Bottom N países por indicador y año |

---

## 💻 Fase 1: Preparación del entorno

### 1.1 Configuración inicial

```bash
# Clonar el repositorio
git clone https://github.com/ZIMABLUE339/Mineria_datoss-main.git
cd Mineria_datoss-main

# Crear ambiente virtual
python -m venv .venv

# Activar (Windows)
.venv\Scripts\activate

# Activar (macOS/Linux)
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 1.2 Dependencias principales

```
flask
pandas
gunicorn
```

### 1.3 Ejecutar localmente

```bash
python app.py
# Home:      http://localhost:5000/
# Dashboard: http://localhost:5000/dashboard
```

---

## 📈 Fase 2: Preparación de datos (SEMMA — Selección)

### 2.1 Obtención del dataset

1. Acceder a: https://docs.google.com/spreadsheets/d/1wkkgqcA-ruldAVnp5_FOUymfi1yiOH8r/
2. Descargar como CSV
3. Guardar en `data/ods_data.csv`

### 2.2 Carga y limpieza en app.py

```python
df = pd.read_csv('data/ods_data.csv')
df.columns = df.columns.str.strip()   # Elimina espacios en nombres de columna
```

Las columnas clave están definidas como constantes:

```python
COUNTRY_COLUMN = 'País'
YEAR_COLUMN    = 'Año'
```

---

## 🔧 Fase 3: Backend (app.py)

### 3.1 Funciones auxiliares

#### `get_unique_values(column)`
Retorna los valores únicos ordenados de una columna. Se usa para poblar los dropdowns de país y año.

```python
def get_unique_values(column):
    values = df[column].dropna().unique()
    return sorted([str(v) for v in values])
```

#### `filter_data(country, year, indicator)`
Filtra el DataFrame por país (búsqueda parcial, sin distinción de mayúsculas), año exacto e indicador (selección de columnas). Es el núcleo de la fase de Selección SEMMA.

```python
def filter_data(country=None, year=None, indicator=None):
    filtered = df.copy()
    if year:
        filtered = filtered[filtered[YEAR_COLUMN].astype(str).str.strip() == str(int(year))]
    if country:
        filtered = filtered[filtered[COUNTRY_COLUMN].astype(str).str.contains(country, case=False, na=False)]
    if indicator:
        cols = [COUNTRY_COLUMN, YEAR_COLUMN] + [c for c in filtered.columns
                if indicator.lower() in c.lower() and c not in {COUNTRY_COLUMN, YEAR_COLUMN}]
        if len(cols) > 2:
            filtered = filtered[cols]
    return filtered
```

#### `prepare_chart_data(filtered_df)`
Serializa el DataFrame filtrado al formato JSON que consume el frontend:
```json
[{ "country": "Colombia", "values": { "PIB Total": 314000000000.0, ... } }]
```

#### `aggregate_indicator_values(filtered_df)`
Calcula el promedio de cada indicador numérico. Se usa como fallback cuando no hay datos para el año solicitado.

### 3.2 Endpoint `/api/data`

Parámetros GET: `country`, `year`, `indicator`

Lógica de fallback: si no hay datos para el año especificado, devuelve el promedio histórico con una nota informativa en el campo `note`.

### 3.3 Endpoint `/api/compare`

Parámetros POST (JSON): `country1`, `country2`, `indicator`, `year` (opcional)

Devuelve:
```json
{
  "country1": { "name": "Colombia", "data": [...] },
  "country2": { "name": "Brasil",   "data": [...] }
}
```

### 3.4 Endpoint `/api/ranking` *(nuevo en v2.0)*

Parámetros GET: `indicator` (requerido), `year` (opcional), `n` (default 10, máx 50)

Lógica:
1. Verifica que la columna exista en el DataFrame
2. Filtra por año si se especifica
3. Convierte la columna a numérico, elimina nulos
4. Si hay múltiples filas por país (varios años), calcula el promedio con `groupby`
5. Ordena descendente para `top` y ascendente para `bottom`

```python
work = work.groupby(COUNTRY_COLUMN, as_index=False)[indicator].mean()
sorted_desc = work.sort_values(indicator, ascending=False)
sorted_asc  = work.sort_values(indicator, ascending=True)
```

Respuesta:
```json
{
  "top":       [{"country": "United States", "value": 25462700000000.0}, ...],
  "bottom":    [{"country": "Tuvalu", "value": 63000000.0}, ...],
  "total":     187,
  "indicator": "PIB Total",
  "year":      "2022"
}
```

---

## 🎨 Fase 4: Frontend

### 4.1 Navegación global

Todos los templates comparten el mismo nav con 5 módulos:

| Ícono | Label | Ruta | Estado |
|-------|-------|------|--------|
| 🏠 | Inicio | `/` | ✅ Activo |
| 📊 | Dashboard | `/dashboard` | ✅ Activo |
| 🧊 | Modelo Multidimensional | `/multidimensional` | 🔜 Base |
| 🍊 | Orange | `/orange` | 🔜 Base |
| ⚡ | Spark | `/spark` | 🔜 Base |

La página activa se resalta con clase `active-page` (fondo azul translúcido). El nav es scrollable horizontalmente en móvil sin barra de scroll visible (`.scrollbar-hide`).

### 4.2 Sistema de diseño — Tailwind CSS

El sistema reemplaza Bootstrap por Tailwind CSS vía CDN. Los colores base son:

```javascript
tailwind.config = {
  theme: {
    extend: {
      colors: {
        ocean: {
          400: '#3b9ef8', 500: '#1480eb', 600: '#0a64cc',
          700: '#0b4ea5', 900: '#123970', 950: '#0a1e3d',
        }
      }
    }
  }
}
```

Fondo de la aplicación: `#0b1120` (slate-950 oscuro)  
Superficie de cards: `#0f172a` (slate-900)  
Tipografía primaria: Inter · Monoespaciado: JetBrains Mono

### 4.3 Página Home (`home.html`)

Secciones:
- **Hero** — título animado con orbs de fondo, stats de 195 países / 45+ indicadores / 1.5K registros
- **¿Qué es?** — feature cards con las 4 capacidades principales
- **Metodología SEMMA** — los 5 pasos explicados con código de ejemplo
- **Stack técnico** — cards de Backend, Frontend y Datos con badges de tecnología
- **API Endpoints** — tabla de los 5 endpoints con método y descripción
- **CTA** — botón hacia el dashboard

### 4.4 Dashboard (`dashboard.html`)

#### Sidebar (escritorio, fijo izquierdo 288px)

**Sección Filtros de búsqueda:**
- País *(requerido)* — select con 202 países
- Indicador *(requerido)* — select con 18 columnas del CSV
- Nivel de ingreso *(opcional)* — Alto / Medio-alto / Medio-bajo / Bajo
- Año *(opcional)* — todos los años del dataset
- Botones: **Consultar** / **Limpiar**

Validación: si País o Indicador están vacíos al presionar Consultar, el select se resalta en rojo con mensaje de error.

**Sección Comparar países:**
- País 1 — select
- País 2 — select
- Indicador — select
- Año *(propio, independiente del filtro principal)*
- Botón: **Comparar**

#### Área principal

1. **KPI Cards** (4): Registros, Indicadores, Países, % Datos faltantes
2. **Tarjeta del país seleccionado** — bandera emoji, nombre, indicador, valor numérico con badge de nivel de ingreso (Banco Mundial)
3. **Estado vacío** — guía para el usuario antes de la primera consulta
4. **Gráficos** (2 columnas):
   - Barras — comparación de registros
   - Línea — distribución de valores
5. **Radar + Clasificación por ingreso** (2 columnas):
   - Radar — perfil normalizado (0–100) de hasta 8 indicadores del país seleccionado
   - Distribución — barras de progreso por nivel de ingreso (Banco Mundial) sobre los países del resultado
6. **Tabla de datos** — con bandera, indicador, valor abreviado y badge OK/N/D
7. **Ranking global** — panel con filtros propios (indicador, año, N) y tabs Top/Bottom
8. **Comparación de países** — cards con banderas + gráfico de barras agrupadas

#### Formateo de números

La función `formatNum()` abrevia automáticamente:

| Valor raw | Mostrado |
|-----------|----------|
| 25,462,700,000,000 | 25.46 B |
| 314,000,000,000 | 314 MM |
| 4,500,000 | 4.5 M |
| 85,300 | 85.3 K |
| 76.8 | 76.8 |

Aplica en: eje Y de gráficos, tooltips, tabla, tarjeta de país y ranking.

#### Clasificación por ingreso

Mapa estático de ~200 países (inglés y español) contra los 4 niveles del Banco Mundial:

| Código | Label | Color |
|--------|-------|-------|
| `H` | Ingreso alto | 🟢 Verde esmeralda |
| `UM` | Ingreso medio-alto | 🔵 Azul cielo |
| `LM` | Ingreso medio-bajo | 🟡 Ámbar |
| `L` | Ingreso bajo | 🔴 Rosa/rojo |
| `UN` | Sin clasificar | ⚪ Gris |

Función: `getIncome(countryName)` con match exacto y fallback parcial.

#### Ranking global — lógica frontend

- `loadRanking(indicator, year)` — pre-llena los selects propios del ranking con los valores de la búsqueda principal. **No ejecuta fetch automáticamente.**
- `refreshRanking()` — lee los selectores del ranking y llama `_doRankingFetch()`
- `_doRankingFetch(indicator, year, n)` — hace el fetch a `/api/ranking`, muestra loading state, maneja errores
- `renderRankingList(type)` — dibuja las filas con número de posición, medalla (top 3), bandera, nombre, dot de ingreso, barra proporcional y valor abreviado
- El país seleccionado en el filtro principal se resalta con borde azul lateral en el ranking

### 4.5 Módulos base (multidimensional, orange, spark)

Cada uno tiene:
- Nav global con su ítem activo marcado
- Pantalla "En construcción" con icono, badge de estado y descripción del módulo
- Grid de 6 bullets describiendo las funcionalidades futuras
- Botones para volver al Dashboard o al Inicio

---

## 🔁 Metodología SEMMA — Implementación por módulo

| Fase | Qué hace | Dónde |
|------|----------|-------|
| **S**elección | Filtros por país, indicador, año y nivel de ingreso | `filter_data()`, sidebar del dashboard |
| **E**xploración | Estadísticas del dataset, % faltantes, tabla de datos | `/api/statistics`, KPI cards |
| **M**odelado | Transformación a JSON, agregación de promedios, normalización para radar | `prepare_chart_data()`, `aggregate_indicator_values()`, `renderRadar()` |
| **V**isualización | Barras, línea, radar, ranking, distribución de ingreso | Chart.js, `renderCharts()`, `renderRankingList()`, `renderIncomeDistribution()` |
| **A**nálisis | Comparación de dos países, ranking global, clasificación por ingreso | `/api/compare`, `/api/ranking`, `INCOME` map |

---

## 🧪 Fase 5: Pruebas locales

### 5.1 Ejecución

```bash
python app.py
```

Salida esperada:
```
✓ Dataset cargado: 13131 registros, 21 columnas
  Home:      http://localhost:5000/
  Dashboard: http://localhost:5000/dashboard
```

### 5.2 Checklist funcional

- ✅ Home carga con stats correctos (195 países, 45+ indicadores)
- ✅ Nav muestra 5 módulos, activo resaltado en cada página
- ✅ Dashboard: validación bloquea consulta sin país e indicador
- ✅ Tarjeta de país muestra bandera y badge de ingreso
- ✅ Gráfico radar aparece con datos normalizados
- ✅ Ranking: filtros propios funcionan independientemente del filtro principal
- ✅ Comparación: año propio no afecta los filtros del dashboard
- ✅ Valores grandes aparecen abreviados (B, MM, M, K)
- ✅ Limpiar resetea todos los componentes
- ✅ Páginas /multidimensional, /orange, /spark responden sin error

### 5.3 Pruebas de responsividad

- ✅ Desktop (1920×1080) — sidebar fijo, 2 columnas de gráficos
- ✅ Tablet (768px) — sidebar oculto, filtros en acordeón
- ✅ Mobile (375px) — nav scrollable, layout 1 columna

---

## 🚀 Fase 6: Despliegue en Render

### 6.1 Configuración

El archivo `render.yaml` ya está configurado. Los pasos son:

1. Push a `main` en GitHub
2. Render detecta el cambio y ejecuta:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `gunicorn app:app`

### 6.2 Variables de entorno en Render

```
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

### 6.3 Consideración de rendimiento

El servidor Flask corre con `threaded=True` para evitar bloqueos cuando múltiples peticiones llegan simultáneamente (por ejemplo, al cargar estadísticas y filtros al mismo tiempo en el dashboard).

```python
app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
```

---

## 🐛 Troubleshooting

| Problema | Causa probable | Solución |
|----------|---------------|----------|
| `ModuleNotFoundError: pandas` | venv no activado | `source .venv/bin/activate` + `pip install -r requirements.txt` |
| Dashboard cuelga al abrir | Fetch automático sin filtros sobre todo el dataset | Ya corregido: no hay `loadData()` automático en el init |
| `/dashboard` devuelve 404 | Usando `app.py` del repo original | Reemplazar con el `app.py` actualizado (v2.0) |
| Gráfico radar vacío | El indicador seleccionado solo tiene 1 columna de valores | Normal: el radar necesita 2+ ejes. Seleccionar indicador con más columnas |
| Ranking no muestra datos | Indicador con nombre diferente al exacto del CSV | Usar el nombre exacto de la columna (ej: `PIB Total`, no `pib total`) |
| Valores en eje Y ilegibles | Números muy grandes (PIB en dólares) | Ya corregido: `formatAxis()` abrevia automáticamente |
| Bandera muestra 🌐 | País no está en el mapa de FLAGS | El mapa cubre ~200 países; para agregar uno, editar el objeto `FLAGS` en dashboard.html |

---

## 📚 Referencias

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pandas Documentation](https://pandas.pydata.org/)
- [Chart.js Documentation](https://www.chartjs.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Render Deployment Guide](https://render.com/docs)
- [Banco Mundial — Clasificación por ingreso](https://datahelpdesk.worldbank.org/knowledgebase/articles/906519)
- [Dataset ODS — Google Sheets](https://docs.google.com/spreadsheets/d/1wkkgqcA-ruldAVnp5_FOUymfi1yiOH8r/)

---

## 📝 Changelog

### v2.0.0 (2026-05-16)
- ✅ Navegación global unificada con 5 módulos en todas las páginas
- ✅ Página Home nueva — explica el sistema, metodología y API
- ✅ Migración de Bootstrap → Tailwind CSS
- ✅ Filtros requeridos en dashboard (País + Indicador obligatorios)
- ✅ Tarjeta de país con bandera emoji y badge de nivel de ingreso
- ✅ Gráfico radar normalizado por país
- ✅ Clasificación por ingreso Banco Mundial (sidebar + distribución + dots)
- ✅ Ranking global con filtros propios (indicador, año, N), tabs Top/Bottom, barras proporcionales
- ✅ Endpoint `/api/ranking` nuevo — agrupa por país, filtra por año, ordena
- ✅ Comparación de países: selects en lugar de inputs de texto, año propio independiente
- ✅ Formateo automático de números grandes (B, MM, M, K) en todos los componentes
- ✅ `threaded=True` en Flask para evitar bloqueos en desarrollo
- ✅ Páginas base para Modelo Multidimensional, Orange y Spark con rutas activas
- ✅ Endpoint `/api/ranking` corregido para trabajar con estructura real del CSV

### v1.0.0 (2026-05-12)
- ✅ Implementación inicial del dashboard con Flask + Bootstrap
- ✅ Filtros dinámicos por país e indicador
- ✅ Visualización con Chart.js (barras y línea)
- ✅ Comparación entre países
- ✅ Despliegue en Render
- ✅ Documentación técnica inicial

---

**GitHub:** https://github.com/ZIMABLUE339/Mineria_datoss-main
