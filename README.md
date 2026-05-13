# Dashboard ODS - Indicadores de Desarrollo Sostenible

Un dashboard interactivo para explorar, filtrar y comparar indicadores económicos y sociales de diferentes países usando datos del Banco Mundial.

**Desarrollado con Flask, Pandas, Bootstrap y Chart.js**

## Características

- **Filtros Dinámicos**: Buscar por país, indicador y año
- **Visualización Interactiva**: Gráficos en tiempo real con Chart.js
- **Comparación de Países**: Análisis comparativo entre naciones
- **Estadísticas Rápidas**: KPIs principales del dataset
- **Interfaz Responsiva**: Funciona en desktop, tablet y móvil
- **Diseño Moderno**: Tonos azul claro y gris claro
- **API RESTful**: Endpoints para integración externa
- **Metodología SEMMA**: Aplicada en toda la arquitectura

## Inicio Rápido

### Requisitos Previos
- Python 3.10+
- pip (gestor de paquetes de Python)
- Git

### Instalación Local

```bash
# 1. Clonar el repositorio
git clone https://github.com/tuusuario/proyecto-ods.git
cd proyecto-ods

# 2. Crear ambiente virtual
python -m venv .venv

# 3. Activar ambiente virtual
# En Windows:
.venv\Scripts\activate

# En macOS/Linux:
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Ejecutar la aplicación
python app.py

# 6. Abrir en el navegador
# Ir a: http://localhost:5000
```

## Estructura del Proyecto

```
proyecto-ods/
├── app.py                    # Backend Flask
├── requirements.txt          # Dependencias
├── README.md                # Este archivo
├── DOCUMENTACION_TECNICA.md # Documentación detallada
├── .gitignore              # Archivos a ignorar
├── .env.example            # Variables de entorno ejemplo
├── data/
│   └── ods_data.csv        # Dataset con indicadores
└── templates/
    ├── dashboard.html      # Frontend principal
    ├── 404.html           # Error 404
    └── 500.html           # Error 500
```

## Configuración

### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```
FLASK_ENV=development
FLASK_DEBUG=True
DATA_PATH=data/ods_data.csv
```

## API Endpoints

### GET `/` 
Renderiza el dashboard principal

### GET `/api/filters`
Obtiene opciones disponibles para filtros
```json
{
  "countries": ["Colombia", "Brasil", ...],
  "indicators": ["PIB 2020", "Alfabetización 2021", ...],
  "total_countries": 195,
  "total_indicators": 45
}
```

### GET `/api/data`
Obtiene datos filtrados
```
/api/data?country=Colombia&indicator=PIB&year=2020
```

### POST `/api/compare`
Compara indicadores entre dos países
```json
{
  "country1": "Colombia",
  "country2": "Brasil",
  "indicator": "PIB 2020"
}
```

### GET `/api/statistics`
Retorna estadísticas del dataset
```json
{
  "total_records": 1500,
  "total_indicators": 45,
  "countries": 195,
  "missing_data_percentage": 12.5
}
```

## Personalización

### Cambiar Colores
Editar en `templates/dashboard.html`:
```css
:root {
    --color-primary: #E3F2FD;
    --color-accent: #64B5F6;
    /* ... otros colores ... */
}
```

### Añadir Nuevo Indicador
1. Actualizar CSV con nueva columna
2. Recargar la aplicación
3. El indicador aparecerá automáticamente en los filtros

## Despliegue en Render

### Pasos:

1. **Push a GitHub**
```bash
git add .
git commit -m "Deploy a Render"
git push origin main
```

2. **Crear Web Service en Render**
   - Ir a https://render.com
   - Nuevo "Web Service"
   - Conectar repositorio
   - Configurar:
     - Build: `pip install -r requirements.txt`
     - Start: `gunicorn app:app`

3. **Variables de Entorno**
   - `FLASK_ENV=production`
   - `PYTHONUNBUFFERED=1`

4. **Deploy**
   - El despliegue es automático cuando haces push a `main`

## Metodología SEMMA

Este proyecto aplica la metodología SEMMA para análisis de datos:

- **S**elección: Filtros dinámicos
- **E**xploración: Estadísticas y tablas
- **M**odelado: Transformación de datos con Pandas
- **V**isualización: Gráficos con Chart.js
- **E**valuación: Comparación y análisis

Ver `DOCUMENTACION_TECNICA.md` para detalles completos.

## Testing

### Pruebas Unitarias (Opcional)
```bash
pip install pytest
pytest tests/
```

### Pruebas Manuales
1. Aplicar cada filtro individualmente
2. Combinar múltiples filtros
3. Comparar países diferentes
4. Verificar responsividad en móvil

## Problemas Comunes

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError` | Activar venv y instalar dependencias |
| Datos no cargan | Verificar que CSV exista en `data/` |
| CSS no se carga | Refrescar con Ctrl+F5 |
| Gráficos vacíos | Revisar datos del filtro aplicado |

## Documentación Completa

Ver [DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md) para:
- Arquitectura detallada
- Explicación de cada función
- Guía paso a paso de desarrollo
- Consideraciones de seguridad
- Troubleshooting avanzado

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request


