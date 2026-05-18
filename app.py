"""
Dashboard ODS - Flask Application
Metodología SEMMA: Selección, Exploración, Modelado, Visualización, Evaluación
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import os
from datetime import datetime

app = Flask(__name__)

# ==================== FASE 1: SELECCIÓN Y CARGA DE DATOS ====================

# Ruta absoluta al CSV — funciona tanto en local como en Render/Gunicorn
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CSV_PATH  = os.path.join(BASE_DIR, 'data', 'ods_data.csv')

try:
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    print(f"✓ Dataset cargado: {df.shape[0]} registros, {df.shape[1]} columnas")
    print(f"✓ Ruta CSV: {CSV_PATH}")
    print(f"Columnas disponibles: {list(df.columns)}")
except Exception as e:
    print(f"✗ Error al cargar datos: {e}")
    print(f"  Ruta intentada: {CSV_PATH}")
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



# ── API: INTERPRETACIÓN AUTOMÁTICA ────────────────────────────
@app.route('/api/interpretation', methods=['GET'])
def get_interpretation():
    """
    Genera análisis automático de un país + indicador + año.
    Calcula posición global, tendencia histórica, comparación
    regional y detección de atípicos. Devuelve texto listo para mostrar.
    """
    if df is None:
        return jsonify({'error': 'Dataset not loaded'}), 500

    country   = request.args.get('country', '').strip()
    indicator = request.args.get('indicator', '').strip()
    year      = request.args.get('year', '').strip()

    if not country or not indicator:
        return jsonify({'error': 'country e indicator son requeridos'}), 400

    # Verificar que la columna existe
    if indicator not in df.columns:
        matches = [c for c in df.columns if indicator.lower() in c.lower()
                   and c not in {COUNTRY_COLUMN, YEAR_COLUMN, 'Grupo regional'}]
        if not matches:
            return jsonify({'error': f'Indicador no encontrado'}), 404
        indicator = matches[0]

    # ── 1. Valor de referencia del país ──────────────────────────
    country_all = df[df[COUNTRY_COLUMN].astype(str).str.contains(country, case=False, na=False)].copy()
    if country_all.empty:
        return jsonify({'error': f'País "{country}" no encontrado'}), 404

    country_all[indicator] = pd.to_numeric(country_all[indicator], errors='coerce')

    if year:
        yr_str = str(int(year))
        country_year = country_all[country_all[YEAR_COLUMN].astype(str).str.strip() == yr_str]
    else:
        country_year = country_all

    ref_value = country_year[indicator].dropna().mean()
    if pd.isna(ref_value):
        ref_value = country_all[indicator].dropna().mean()

    if pd.isna(ref_value):
        return jsonify({'error': 'Sin datos numéricos para ese filtro'}), 404

    insights = []
    conclusion_parts = []

    # ── 2. Posición global (percentil) ───────────────────────────
    if year:
        global_slice = df[df[YEAR_COLUMN].astype(str).str.strip() == yr_str].copy()
    else:
        global_slice = df.copy()

    global_slice[indicator] = pd.to_numeric(global_slice[indicator], errors='coerce')
    global_vals = global_slice.groupby(COUNTRY_COLUMN)[indicator].mean().dropna()
    total_countries = len(global_vals)

    if total_countries > 0:
        rank = int((global_vals > ref_value).sum()) + 1
        percentile = round((1 - rank / total_countries) * 100)
        global_avg = global_vals.mean()
        vs_global = ((ref_value - global_avg) / global_avg * 100) if global_avg != 0 else 0

        if percentile >= 75:
            pos_label = 'por encima del promedio mundial'
            pos_tag = 'up'
        elif percentile >= 40:
            pos_label = 'cerca del promedio mundial'
            pos_tag = 'neutral'
        else:
            pos_label = 'por debajo del promedio mundial'
            pos_tag = 'down'

        insights.append({
            'type': 'position',
            'title': 'Posición global',
            'text': f'{country} ocupa el puesto {rank} de {total_countries} países para "{indicator}"{(" en " + year) if year else ""}, ubicándose en el percentil {percentile} — {pos_label}.',
            'tag': pos_label,
            'tag_type': pos_tag
        })
        conclusion_parts.append(f'ocupa el puesto {rank} de {total_countries} países (percentil {percentile})')

    # ── 3. Tendencia histórica ────────────────────────────────────
    history = country_all[[YEAR_COLUMN, indicator]].dropna().copy()
    history[YEAR_COLUMN] = pd.to_numeric(history[YEAR_COLUMN], errors='coerce')
    history = history.dropna().sort_values(YEAR_COLUMN)

    if len(history) >= 3:
        first_val = history[indicator].iloc[0]
        last_val  = history[indicator].iloc[-1]
        first_yr  = int(history[YEAR_COLUMN].iloc[0])
        last_yr   = int(history[YEAR_COLUMN].iloc[-1])
        pct_change = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0

        # Detectar año de caída / pico máximo
        min_idx = history[indicator].idxmin()
        max_idx = history[indicator].idxmax()
        min_yr  = int(history.loc[min_idx, YEAR_COLUMN])
        max_yr  = int(history.loc[max_idx, YEAR_COLUMN])

        trend_dir = 'crecimiento' if pct_change > 0 else 'caída'
        trend_tag = 'up' if pct_change > 0 else 'down'
        sign      = '+' if pct_change >= 0 else ''

        trend_text = (f'Entre {first_yr} y {last_yr} el indicador tuvo un cambio de '
                      f'{sign}{pct_change:.1f}%. '
                      f'El valor máximo se registró en {max_yr} y el mínimo en {min_yr}.')

        insights.append({
            'type': 'trend',
            'title': 'Tendencia histórica',
            'text': trend_text,
            'tag': f'Tendencia: {trend_dir}',
            'tag_type': trend_tag,
            'extra_tag': f'Mínimo: {min_yr}',
            'extra_tag_type': 'down' if min_yr == (int(year) if year else last_yr) else 'neutral'
        })
        conclusion_parts.append(f'con una variación de {sign}{pct_change:.1f}% entre {first_yr} y {last_yr}')

    # ── 4. Comparación regional ───────────────────────────────────
    REGION_COL = 'Grupo regional'
    if REGION_COL in df.columns:
        country_region = country_all[REGION_COL].dropna().mode()
        if not country_region.empty:
            region_name = country_region.iloc[0]
            if year:
                regional_df = df[
                    (df[REGION_COL] == region_name) &
                    (df[YEAR_COLUMN].astype(str).str.strip() == yr_str)
                ].copy()
            else:
                regional_df = df[df[REGION_COL] == region_name].copy()

            regional_df[indicator] = pd.to_numeric(regional_df[indicator], errors='coerce')
            regional_avg = regional_df[indicator].mean()

            if not pd.isna(regional_avg) and regional_avg != 0:
                vs_region = ((ref_value - regional_avg) / regional_avg * 100)
                direction = 'supera' if vs_region > 0 else 'está por debajo de'
                sign_r    = '+' if vs_region > 0 else ''
                r_tag     = 'up' if vs_region > 0 else 'down'

                insights.append({
                    'type': 'regional',
                    'title': 'Comparación regional',
                    'text': (f'Dentro de {region_name}, {country} {direction} el promedio '
                             f'regional ({sign_r}{vs_region:.1f}%).'),
                    'tag': f'{region_name}',
                    'tag_type': 'neutral'
                })
                conclusion_parts.append(f'{direction} el promedio de {region_name} en un {abs(vs_region):.1f}%')

    # ── 5. Detección de atípico ───────────────────────────────────
    if len(history) >= 3:
        std_val  = history[indicator].std()
        mean_val = history[indicator].mean()
        z_score  = abs(ref_value - mean_val) / std_val if std_val > 0 else 0

        if z_score > 1.5:
            label = 'máximo histórico' if ref_value > mean_val else 'mínimo histórico'
            insights.append({
                'type': 'outlier',
                'title': 'Dato atípico detectado',
                'text': (f'El valor {"de " + year if year else "actual"} se desvía '
                         f'{z_score:.1f} desviaciones estándar de la media histórica de {country}, '
                         f'clasificándolo como {label} estadísticamente relevante.'),
                'tag': label.capitalize(),
                'tag_type': 'down' if 'mínimo' in label else 'up'
            })
            conclusion_parts.append(f'registrando un {label} estadístico')

    # ── 6. Construir conclusión ───────────────────────────────────
    income_map = {
        'H': 'ingreso alto', 'UM': 'ingreso medio-alto',
        'LM': 'ingreso medio-bajo', 'L': 'ingreso bajo'
    }
    # Inferir nivel de ingreso por región
    income_note = ''
    if 'Grupo regional' in df.columns and not country_all.empty:
        reg = country_all['Grupo regional'].dropna().mode()
        if not reg.empty:
            r = reg.iloc[0].lower()
            if any(x in r for x in ['europe', 'north america', 'europa', 'norteamérica', 'oceania']):
                income_note = 'economía desarrollada'
            elif any(x in r for x in ['latin', 'asia', 'africa', 'middle']):
                income_note = 'economía en desarrollo'

    if conclusion_parts:
        conclusion = (f'{country} {", ".join(conclusion_parts[:3])}. '
                      f'{"Es una " + income_note + "." if income_note else ""} '
                      f'Estos datos corresponden al indicador "{indicator}" '
                      f'{"del año " + year if year else "en el período histórico disponible"}.')
    else:
        conclusion = f'No hay suficientes datos para generar una conclusión completa sobre {country}.'

    return jsonify({
        'country':   country,
        'indicator': indicator,
        'year':      year or 'todos',
        'value':     round(ref_value, 4),
        'insights':  insights,
        'conclusion': conclusion.strip()
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