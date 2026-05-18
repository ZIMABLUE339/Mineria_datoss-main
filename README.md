# ODS Explorer — Dashboard de Indicadores de Desarrollo Sostenible

Plataforma web multi-página para explorar, filtrar, comparar y visualizar los indicadores ODS del Banco Mundial. Construida con **Flask + Pandas + Tailwind CSS + Chart.js**, aplicando la metodología **SEMMA**.

---

## Estructura del proyecto

```
proyecto-ods/
├── app.py                    # Backend Flask — rutas y API
├── requirements.txt
├── render.yaml               # Configuración Render
├── data/
│   └── ods_data.csv          # Dataset ODS (13.000+ registros, 21 columnas)
└── templates/
    ├── home.html             # Página de inicio
    ├── dashboard.html        # Dashboard principal
    ├── multidimensional.html # Módulo Modelo Multidimensional
    ├── orange.html           # Módulo Orange Data Mining
    ├── spark.html            # Módulo Apache Spark
    ├── 404.html
    └── 500.html
```

---

## Dataset

| Campo | Detalle |
|-------|---------|
| Fuente | Banco Mundial vía Google Sheets |
| Filas | ~13.100 registros |
| Columnas | 21 (Año, Grupo regional, País + 18 indicadores) |
| Países | 202 |
| Rango años | 1960 – 2024 (cobertura irregular) |
| Indicadores | PIB Total, PIB per cápita, Tasa de crecimiento, Esperanza de vida, Tasa de desempleo, Alfabetización juvenil y adultos, Matrículas (primaria/secundaria/terciaria), Población activa, totales de población |

---

## Páginas y módulos

| Ruta | Módulo | Estado |
|------|--------|--------|
| `/` | Home — explica el sistema | ✅ Activo |
| `/dashboard` | Dashboard de indicadores | ✅ Activo |
| `/multidimensional` | Modelo Multidimensional (PCA, clustering) | 🔜 En construcción |
| `/orange` | Orange Data Mining (flujos visuales) | 🔜 En construcción |
| `/spark` | Apache Spark (procesamiento distribuido) | 🔜 En construcción |

---

## API REST

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/filters` | Países, años e indicadores disponibles |
| GET | `/api/data` | Datos filtrados por país, indicador y año |
| POST | `/api/compare` | Comparación entre dos países |
| GET | `/api/statistics` | KPIs del dataset (total registros, países, % faltantes) |
| GET | `/api/ranking` | Top/Bottom N países por indicador y año |

### Ejemplos

```
GET /api/data?country=Colombia&indicator=PIB Total&year=2022

GET /api/ranking?indicator=Esperanza de vida&year=2020&n=10

POST /api/compare
{ "country1": "Colombia", "country2": "Brasil", "indicator": "PIB Total", "year": "2022" }
```

---

## Características del dashboard

- **Filtros requeridos** — País e Indicador obligatorios; validación visual con borde rojo
- **Filtro por nivel de ingreso** — Banco Mundial (Alto / Medio-alto / Medio-bajo / Bajo)
- **Tarjeta de país** — bandera emoji, badge de nivel de ingreso, valor con formato abreviado
- **Gráficos múltiples** — Barras, Línea, Radar (normalizado 0–100), Distribución de ingreso
- **Ranking global** — Top/Bottom 10 con filtros propios (indicador, año, N independientes)
- **Comparación** — 2 países con año propio, banderas y gráfico agrupado
- **Formato automático** — valores grandes abreviados: `25.46 B`, `314 MM`, `4.5 M`

---

## Stack tecnológico

**Backend:** Python 3.10+ · Flask · Pandas · Gunicorn

**Frontend:** Tailwind CSS (CDN) · Chart.js · JavaScript Vanilla · Inter + JetBrains Mono

**Infraestructura:** GitHub · Render (CI/CD automático)

---

## Despliegue en Render

1. Push a `main` en GitHub
2. Render ejecuta automáticamente:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `gunicorn app:app`
3. Variables de entorno: `FLASK_ENV=production` · `PYTHONUNBUFFERED=1`

---

## Metodología SEMMA

| Fase | Implementación |
|------|---------------|
| **S**elección | `filter_data()` — filtra por país, año e indicador |
| **E**xploración | `/api/statistics` — KPIs y % de datos faltantes |
| **M**odelado | `prepare_chart_data()` · `aggregate_indicator_values()` · normalización radar |
| **V**isualización | Chart.js: barras, línea, radar, ranking, distribución de ingreso |
| **A**nálisis | `/api/compare` · `/api/ranking` · clasificación por ingreso Banco Mundial |

---

## Changelog

### v2.0.0 — 2026-05-16
- Navegación global con 5 módulos en todas las páginas
- Migración Bootstrap → Tailwind CSS
- Nuevas páginas: Home, Multidimensional, Orange, Spark
- Dashboard enriquecido: radar, ranking con filtros propios, clasificación por ingreso
- Endpoint `/api/ranking` nuevo y corregido para la estructura real del CSV
- Formato automático de números grandes en todos los componentes
- Comparación con selects, año independiente y banderas

### v1.0.0 — 2026-05-12
- Dashboard inicial con Flask + Bootstrap + Chart.js
- Filtros por país, indicador y año
- Comparación de países
- Despliegue en Render