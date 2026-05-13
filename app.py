"""
Dashboard ODS - Flask Application
Metodología SEMMA: Selección, Exploración, Modelado, Visualización, Evaluación
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
from datetime import datetime

app = Flask(__name__)

# ==================== FASE 1: SELECCIÓN Y CARGA DE DATOS ====================
try:
    # Cargar el dataset CSV con los indicadores ODS
    df = pd.read_csv('data/ods_data.csv')
    
    # Limpiar espacios en blanco en los nombres de columnas
    df.columns = df.columns.str.strip()
    
    # Información del dataset
    print(f"✓ Dataset cargado: {df.shape[0]} registros, {df.shape[1]} columnas")
    print(f"Columnas disponibles: {list(df.columns)}")
    
except Exception as e:
    print(f"Error al cargar datos: {e}")
    df = None


# ==================== CONFIGURACIÓN DE COLUMNAS ====================
COUNTRY_COLUMN = 'País'
YEAR_COLUMN = 'Año'

# ==================== FUNCIONES AUXILIARES ====================
def get_unique_values(column):
    """Obtener valores únicos de una columna, ordenados"""
    if df is None or column not in df.columns:
        return []
    values = df[column].dropna().unique()
    return sorted([str(v) for v in values])


def filter_data(country=None, year=None, indicator=None):
    """
    Filtrar datos según criterios especificados
    Implementa la lógica de Selección y Exploración (SEMMA)
    """
    filtered = df.copy()
    
    # Aplicar filtro por año (filtra filas)
    if year:
        try:
            year_str = str(int(year))
            filtered = filtered[
                filtered[YEAR_COLUMN].astype(str).str.strip() == year_str
            ]
        except:
            pass
    
    # Aplicar filtro por país (filtra filas)
    if country:
        filtered = filtered[
            filtered[COUNTRY_COLUMN].astype(str).str.contains(country, case=False, na=False)
        ]
    
    # Aplicar filtro por indicador (selecciona columnas)
    if indicator:
        cols = [COUNTRY_COLUMN, YEAR_COLUMN] + [
            col for col in filtered.columns
            if indicator.lower() in col.lower() and col not in {COUNTRY_COLUMN, YEAR_COLUMN}
        ]
        if len(cols) > 2:
            filtered = filtered[cols]
    
    return filtered


def prepare_chart_data(filtered_df):
    """Preparar datos para gráficos"""
    if filtered_df.empty:
        return []
    
    data = []
    first_col = filtered_df.columns[0]
    
    for idx, row in filtered_df.iterrows():
        row_data = {
            'country': row[first_col],
            'values': {}
        }
        
        for col in filtered_df.columns[1:]:
            try:
                value = float(row[col]) if pd.notna(row[col]) else None
                row_data['values'][col] = value
            except:
                pass
        
        data.append(row_data)
    
    return data


def aggregate_indicator_values(filtered_df):
    """Calcular promedio de valores numéricos por indicador en un DataFrame."""
    if filtered_df.empty:
        return {}

    numeric_cols = [col for col in filtered_df.columns if col not in {COUNTRY_COLUMN, YEAR_COLUMN}]
    aggregated = {}

    for col in numeric_cols:
        series = pd.to_numeric(filtered_df[col], errors='coerce')
        if series.dropna().empty:
            aggregated[col] = None
        else:
            aggregated[col] = float(series.mean())

    return aggregated


# ==================== RUTAS FLASK ====================

@app.route('/')
def index():
    """Ruta principal: renderiza el dashboard"""
    if df is None:
        return "Error: No se pudo cargar el dataset", 500
    
    # Extraer opciones para los filtros
    countries = get_unique_values(COUNTRY_COLUMN)
    years = get_unique_values(YEAR_COLUMN)
    indicators = [col for col in df.columns if col not in {COUNTRY_COLUMN, YEAR_COLUMN}]
    
    return render_template(
        'dashboard.html',
        countries=countries,
        indicators=indicators,
        years=years
    )


@app.route('/api/data', methods=['GET', 'POST'])
def get_data():
    """
    API endpoint para obtener datos filtrados
    Soporta filtros: country, year, indicator
    """
    country = request.args.get('country')
    year = request.args.get('year')
    indicator = request.args.get('indicator')
    
    # Aplicar filtros
    filtered = filter_data(country, year, indicator)
    
    if filtered.empty and year:
        fallback = filter_data(country, None, indicator)
        if not fallback.empty:
            aggregated_values = aggregate_indicator_values(fallback)
            chart_data = [{
                'country': country or 'Resultado',
                'values': aggregated_values,
                'note': f'No se encontraron datos para el año {year}. Se calculó un promedio con los datos disponibles.'
            }]
            return jsonify({
                'success': True,
                'rows': len(fallback),
                'data': chart_data,
                'note': 'No hay datos para el año seleccionado; se usó un cálculo con la información disponible.'
            })
    
    if filtered.empty:
        return jsonify({
            'success': False,
            'message': 'No hay datos disponibles con los filtros especificados',
            'data': []
        })
    
    # Preparar datos para respuesta
    chart_data = prepare_chart_data(filtered)
    
    def chart_row_has_values(row):
        non_year_values = [
            value for key, value in row['values'].items()
            if key != YEAR_COLUMN
        ]
        return any(value is not None for value in non_year_values)

    all_null = chart_data and not any(chart_row_has_values(row) for row in chart_data)
    if all_null and year:
        fallback = filter_data(country, None, indicator)
        if not fallback.empty:
            aggregated_values = aggregate_indicator_values(fallback)
            chart_data = [{
                'country': country or 'Resultado',
                'values': aggregated_values,
                'note': f'No se encontraron valores para el año {year}. Se calculó un promedio con los datos disponibles.'
            }]
            return jsonify({
                'success': True,
                'rows': len(fallback),
                'data': chart_data,
                'note': 'No hay datos para el año seleccionado; se usó un cálculo con la información disponible.'
            })
        return jsonify({
            'success': False,
            'message': 'No hay datos disponibles con los filtros especificados',
            'data': []
        })
    
    return jsonify({
        'success': True,
        'rows': len(filtered),
        'data': chart_data
    })


@app.route('/api/filters', methods=['GET'])
def get_filters():
    """API endpoint para obtener opciones de filtros disponibles"""
    if df is None:
        return jsonify({'error': 'Dataset not loaded'}), 500
    
    countries = get_unique_values(COUNTRY_COLUMN)
    years = get_unique_values(YEAR_COLUMN)
    indicators = [col for col in df.columns if col not in {COUNTRY_COLUMN, YEAR_COLUMN}]
    
    return jsonify({
        'countries': countries,
        'years': years,
        'indicators': indicators,
        'total_countries': len(countries),
        'total_indicators': len(indicators)
    })


@app.route('/api/compare', methods=['POST'])
def compare_data():
    """
    API endpoint para comparar dos países/indicadores
    Útil para análisis comparativos (toma de decisiones)
    """
    data = request.get_json()
    country1 = data.get('country1')
    country2 = data.get('country2')
    year = data.get('year')
    indicator = data.get('indicator')
    
    if not all([country1, country2, indicator]):
        return jsonify({'error': 'Parámetros insuficientes'}), 400
    
    def build_comparison(country):
        exact = filter_data(country, year, indicator=indicator) if year else filter_data(country, None, indicator=indicator)
        chart_data = prepare_chart_data(exact)

        def has_non_year_values(row):
            return any(
                value is not None
                for key, value in row['values'].items()
                if key != YEAR_COLUMN
            )

        all_null = chart_data and not any(has_non_year_values(row) for row in chart_data)

        if (exact.empty or all_null) and year:
            fallback = filter_data(country, None, indicator=indicator)
            if not fallback.empty:
                return [{
                    'country': f'{country} (promedio)',
                    'values': aggregate_indicator_values(fallback),
                    'note': f'No se encontraron datos para el año {year}. Se calculó un promedio con los datos disponibles.'
                }]
            return []
        return chart_data
    
    comparison = {
        'country1': {
            'name': country1,
            'data': build_comparison(country1)
        },
        'country2': {
            'name': country2,
            'data': build_comparison(country2)
        }
    }
    
    return jsonify(comparison)


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    API endpoint para obtener estadísticas del dataset
    Resumen de datos para interpretación
    """
    if df is None:
        return jsonify({'error': 'Dataset not loaded'}), 500
    
    stats = {
        'total_records': len(df),
        'total_indicators': len([col for col in df.columns if col not in {COUNTRY_COLUMN, YEAR_COLUMN}]),
        'countries': len(df[COUNTRY_COLUMN].unique()),
        'missing_data_percentage': (df.isna().sum().sum() / (df.shape[0] * df.shape[1]) * 100)
    }
    
    return jsonify(stats)


# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def not_found(error):
    try:
        return render_template('404.html'), 404
    except:
        return "404 - Página no encontrada", 404


@app.errorhandler(500)
def server_error(error):
    try:
        return render_template('500.html'), 500
    except:
        return "500 - Error del servidor", 500


# ==================== PUNTO DE ENTRADA ====================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Dashboard ODS - Iniciando servidor Flask")
    print("="*50)
    print(f"Tiempo: {datetime.now()}")
    print(f"Dataset: {df.shape if df is not None else 'No cargado'}")
    print("Acceda a: http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
