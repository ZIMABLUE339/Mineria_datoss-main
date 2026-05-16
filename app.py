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
    df = pd.read_csv('data/ods_data.csv')
    df.columns = df.columns.str.strip()
    print(f"✓ Dataset cargado: {df.shape[0]} registros, {df.shape[1]} columnas")
    print(f"Columnas disponibles: {list(df.columns)}")
except Exception as e:
    print(f"Error al cargar datos: {e}")
    df = None

# ==================== CONFIGURACIÓN DE COLUMNAS ====================

COUNTRY_COLUMN = 'País'
YEAR_COLUMN    = 'Año'

# ==================== FUNCIONES AUXILIARES ====================

def get_unique_values(column):
    """Obtener valores únicos de una columna, ordenados"""
    if df is None or column not in df.columns:
        return []
    values = df[column].dropna().unique()
    return sorted([str(v) for v in values])


def filter_data(country=None, year=None, indicator=None):
    """Filtrar datos según criterios especificados (SEMMA - Selección/Exploración)"""
    filtered = df.copy()

    if year:
        try:
            year_str = str(int(year))
            filtered = filtered[
                filtered[YEAR_COLUMN].astype(str).str.strip() == year_str
            ]
        except:
            pass

    if country:
        filtered = filtered[
            filtered[COUNTRY_COLUMN].astype(str).str.contains(country, case=False, na=False)
        ]

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
        row_data = {'country': row[first_col], 'values': {}}
        for col in filtered_df.columns[1:]:
            try:
                value = float(row[col]) if pd.notna(row[col]) else None
                row_data['values'][col] = value
            except:
                pass
        data.append(row_data)
    return data


def aggregate_indicator_values(filtered_df):
    """Calcular promedio de valores numéricos por indicador"""
    if filtered_df.empty:
        return {}
    numeric_cols = [col for col in filtered_df.columns if col not in {COUNTRY_COLUMN, YEAR_COLUMN}]
    aggregated = {}
    for col in numeric_cols:
        series = pd.to_numeric(filtered_df[col], errors='coerce')
        aggregated[col] = float(series.mean()) if not series.dropna().empty else None
    return aggregated


# ==================== RUTAS FLASK ====================

# ── NUEVA RUTA: HOME ──────────────────────────────────────────
@app.route('/')
def home():
    """Página de inicio: explica el sistema ODS Explorer"""
    return render_template('home.html')


# ── DASHBOARD ─────────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    """Dashboard principal con filtros y visualizaciones"""
    if df is None:
        return "Error: No se pudo cargar el dataset", 500

    countries  = get_unique_values(COUNTRY_COLUMN)
    years      = get_unique_values(YEAR_COLUMN)
    indicators = [col for col in df.columns if col not in {COUNTRY_COLUMN, YEAR_COLUMN}]

    return render_template(
        'dashboard.html',
        countries=countries,
        indicators=indicators,
        years=years
    )


# ── API: FILTROS ───────────────────────────────────────────────
@app.route('/api/filters', methods=['GET'])
def get_filters():
    """Opciones disponibles para filtros"""
    if df is None:
        return jsonify({'error': 'Dataset not loaded'}), 500

    countries  = get_unique_values(COUNTRY_COLUMN)
    years      = get_unique_values(YEAR_COLUMN)
    indicators = [col for col in df.columns if col not in {COUNTRY_COLUMN, YEAR_COLUMN}]

    return jsonify({
        'countries':        countries,
        'years':            years,
        'indicators':       indicators,
        'total_countries':  len(countries),
        'total_indicators': len(indicators)
    })


# ── API: DATOS ─────────────────────────────────────────────────
@app.route('/api/data', methods=['GET', 'POST'])
def get_data():
    """Datos filtrados por país, año e indicador"""
    country   = request.args.get('country')
    year      = request.args.get('year')
    indicator = request.args.get('indicator')

    filtered = filter_data(country, year, indicator)

    # Fallback con promedio si no hay datos para el año
    if filtered.empty and year:
        fallback = filter_data(country, None, indicator)
        if not fallback.empty:
            return jsonify({
                'success': True,
                'rows': len(fallback),
                'data': [{
                    'country': country or 'Resultado',
                    'values': aggregate_indicator_values(fallback),
                    'note': f'No hay datos para {year}. Se usó promedio general.'
                }],
                'note': f'No hay datos para el año {year}; se calculó un promedio.'
            })

    if filtered.empty:
        return jsonify({'success': False, 'message': 'Sin datos para los filtros aplicados', 'data': []})

    chart_data = prepare_chart_data(filtered)

    def has_values(row):
        return any(v is not None for k, v in row['values'].items() if k != YEAR_COLUMN)

    if chart_data and not any(has_values(r) for r in chart_data) and year:
        fallback = filter_data(country, None, indicator)
        if not fallback.empty:
            return jsonify({
                'success': True,
                'rows': len(fallback),
                'data': [{
                    'country': country or 'Resultado',
                    'values': aggregate_indicator_values(fallback),
                    'note': f'No hay valores para {year}. Se usó promedio general.'
                }],
                'note': f'Sin datos para el año {year}; se calculó un promedio.'
            })
        return jsonify({'success': False, 'message': 'Sin datos disponibles', 'data': []})

    return jsonify({'success': True, 'rows': len(filtered), 'data': chart_data})


# ── API: COMPARAR ──────────────────────────────────────────────
@app.route('/api/compare', methods=['POST'])
def compare_data():
    """Comparar dos países en un indicador"""
    data      = request.get_json()
    country1  = data.get('country1')
    country2  = data.get('country2')
    year      = data.get('year')
    indicator = data.get('indicator')

    if not all([country1, country2, indicator]):
        return jsonify({'error': 'Parámetros insuficientes'}), 400

    def build_comparison(country):
        exact      = filter_data(country, year, indicator) if year else filter_data(country, None, indicator)
        chart_data = prepare_chart_data(exact)

        def has_non_year(row):
            return any(v is not None for k, v in row['values'].items() if k != YEAR_COLUMN)

        if (exact.empty or (chart_data and not any(has_non_year(r) for r in chart_data))) and year:
            fallback = filter_data(country, None, indicator)
            if not fallback.empty:
                return [{'country': f'{country} (promedio)', 'values': aggregate_indicator_values(fallback)}]
            return []
        return chart_data

    return jsonify({
        'country1': {'name': country1, 'data': build_comparison(country1)},
        'country2': {'name': country2, 'data': build_comparison(country2)},
    })


# ── API: ESTADÍSTICAS ──────────────────────────────────────────
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Resumen estadístico del dataset"""
    if df is None:
        return jsonify({'error': 'Dataset not loaded'}), 500

    return jsonify({
        'total_records':           len(df),
        'total_indicators':        len([c for c in df.columns if c not in {COUNTRY_COLUMN, YEAR_COLUMN}]),
        'countries':               len(df[COUNTRY_COLUMN].unique()),
        'missing_data_percentage': (df.isna().sum().sum() / (df.shape[0] * df.shape[1]) * 100)
    })



# ── API: RANKING TOP/BOTTOM ────────────────────────────────────
@app.route('/api/ranking', methods=['GET'])
def get_ranking():
    """
    Ranking de países por indicador y año.
    Parámetros:
      - indicator: nombre exacto de la columna (ej: 'PIB Total')
      - year: año específico (ej: '2020'). Si se omite, promedia todos los años.
      - n: cuántos países mostrar (default 10)
    """
    if df is None:
        return jsonify({'error': 'Dataset not loaded'}), 500

    indicator = request.args.get('indicator', '').strip()
    year      = request.args.get('year', '').strip()
    n         = min(int(request.args.get('n', 10)), 50)

    if not indicator:
        return jsonify({'error': 'indicator es requerido'}), 400

    # Verificar que la columna existe
    if indicator not in df.columns:
        # Intentar match parcial
        matches = [c for c in df.columns if indicator.lower() in c.lower()
                   and c not in {COUNTRY_COLUMN, YEAR_COLUMN, 'Grupo regional'}]
        if not matches:
            return jsonify({'error': f'Indicador "{indicator}" no encontrado'}), 404
        indicator = matches[0]

    # Filtrar por año si se especifica
    subset = df.copy()
    if year:
        try:
            yr = str(int(year))
            subset = subset[subset[YEAR_COLUMN].astype(str).str.strip() == yr]
        except Exception:
            pass

    if subset.empty:
        return jsonify({'top': [], 'bottom': [], 'total': 0,
                        'indicator': indicator, 'year': year or 'todos'})

    # Extraer país + indicador, convertir a numérico
    work = subset[[COUNTRY_COLUMN, indicator]].copy()
    work[indicator] = pd.to_numeric(work[indicator], errors='coerce')
    work = work.dropna(subset=[indicator])

    if work.empty:
        return jsonify({'top': [], 'bottom': [], 'total': 0,
                        'indicator': indicator, 'year': year or 'todos'})

    # Si hay múltiples filas por país (varios años), promediar
    work = work.groupby(COUNTRY_COLUMN, as_index=False)[indicator].mean()

    total = len(work)
    sorted_desc = work.sort_values(indicator, ascending=False)
    sorted_asc  = work.sort_values(indicator, ascending=True)

    def to_list(df_slice):
        return [
            {'country': str(r[COUNTRY_COLUMN]), 'value': round(float(r[indicator]), 4)}
            for _, r in df_slice.head(n).iterrows()
        ]

    return jsonify({
        'top':       to_list(sorted_desc),
        'bottom':    to_list(sorted_asc),
        'total':     total,
        'indicator': indicator,
        'year':      year if year else 'todos',
    })


# ── PÁGINAS ADICIONALES ───────────────────────────────────────

@app.route('/multidimensional')
def multidimensional():
    """Página Modelo Multidimensional"""
    return render_template('multidimensional.html')


@app.route('/orange')
def orange():
    """Página Orange Data Mining"""
    return render_template('orange.html')


@app.route('/spark')
def spark():
    """Página Apache Spark"""
    return render_template('spark.html')

# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def not_found(error):
    try:    return render_template('404.html'), 404
    except: return "404 - Página no encontrada", 404

@app.errorhandler(500)
def server_error(error):
    try:    return render_template('500.html'), 500
    except: return "500 - Error del servidor", 500


# ==================== PUNTO DE ENTRADA ====================

if __name__ == '__main__':
    print("\n" + "="*55)
    print("  ODS Explorer — Flask App")
    print("="*55)
    print(f"  Inicio:    {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Dataset:   {df.shape if df is not None else 'No cargado'}")
    print(f"  Home:      http://localhost:5000/")
    print(f"  Dashboard: http://localhost:5000/dashboard")
    print("="*55 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)