"""
Dashboard ODS - Flask Application
Metodología SEMMA: Selección, Exploración, Modelado, Visualización, Evaluación
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import os
from datetime import datetime
from sqlalchemy import create_engine, text as sa_text
import urllib

app = Flask(__name__)

# ==================== FASE 1: SELECCIÓN Y CARGA DE DATOS ====================

# Ruta absoluta al CSV — funciona tanto en local como en Render/Gunicorn
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_csv1    = os.path.join(BASE_DIR, 'data', 'ODS.csv')
_csv2    = os.path.join(BASE_DIR, 'data', 'ods_data.csv')
CSV_PATH = _csv1 if os.path.exists(_csv1) else _csv2

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

# ── HOME ──────────────────────────────────────────────────────
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
    """Ranking de países por indicador y año."""
    if df is None:
        return jsonify({'error': 'Dataset not loaded'}), 500

    indicator = request.args.get('indicator', '').strip()
    year      = request.args.get('year', '').strip()
    n         = min(int(request.args.get('n', 10)), 50)

    if not indicator:
        return jsonify({'error': 'indicator es requerido'}), 400

    if indicator not in df.columns:
        matches = [c for c in df.columns if indicator.lower() in c.lower()
                   and c not in {COUNTRY_COLUMN, YEAR_COLUMN, 'Grupo regional'}]
        if not matches:
            return jsonify({'error': f'Indicador "{indicator}" no encontrado'}), 404
        indicator = matches[0]

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

    work = subset[[COUNTRY_COLUMN, indicator]].copy()
    work[indicator] = pd.to_numeric(work[indicator], errors='coerce')
    work = work.dropna(subset=[indicator])

    if work.empty:
        return jsonify({'top': [], 'bottom': [], 'total': 0,
                        'indicator': indicator, 'year': year or 'todos'})

    work = work.groupby(COUNTRY_COLUMN, as_index=False)[indicator].mean()
    total       = len(work)
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
    """Genera análisis automático de un país + indicador + año."""
    if df is None:
        return jsonify({'error': 'Dataset not loaded'}), 500

    country   = request.args.get('country', '').strip()
    indicator = request.args.get('indicator', '').strip()
    year      = request.args.get('year', '').strip()

    if not country or not indicator:
        return jsonify({'error': 'country e indicator son requeridos'}), 400

    if indicator not in df.columns:
        matches = [c for c in df.columns if indicator.lower() in c.lower()
                   and c not in {COUNTRY_COLUMN, YEAR_COLUMN, 'Grupo regional'}]
        if not matches:
            return jsonify({'error': f'Indicador no encontrado'}), 404
        indicator = matches[0]

    country_all = df[df[COUNTRY_COLUMN].astype(str).str.contains(country, case=False, na=False)].copy()
    if country_all.empty:
        return jsonify({'error': f'País "{country}" no encontrado'}), 404

    country_all[indicator] = pd.to_numeric(country_all[indicator], errors='coerce')

    if year:
        yr_str       = str(int(year))
        country_year = country_all[country_all[YEAR_COLUMN].astype(str).str.strip() == yr_str]
    else:
        country_year = country_all

    ref_value = country_year[indicator].dropna().mean()
    if pd.isna(ref_value):
        ref_value = country_all[indicator].dropna().mean()
    if pd.isna(ref_value):
        return jsonify({'error': 'Sin datos numéricos para ese filtro'}), 404

    insights         = []
    conclusion_parts = []

    # Posición global
    if year:
        global_slice = df[df[YEAR_COLUMN].astype(str).str.strip() == yr_str].copy()
    else:
        global_slice = df.copy()

    global_slice[indicator] = pd.to_numeric(global_slice[indicator], errors='coerce')
    global_vals     = global_slice.groupby(COUNTRY_COLUMN)[indicator].mean().dropna()
    total_countries = len(global_vals)

    if total_countries > 0:
        rank       = int((global_vals > ref_value).sum()) + 1
        percentile = round((1 - rank / total_countries) * 100)
        global_avg = global_vals.mean()

        if percentile >= 75:
            pos_label, pos_tag = 'por encima del promedio mundial', 'up'
        elif percentile >= 40:
            pos_label, pos_tag = 'cerca del promedio mundial', 'neutral'
        else:
            pos_label, pos_tag = 'por debajo del promedio mundial', 'down'

        insights.append({
            'type': 'position', 'title': 'Posición global',
            'text': f'{country} ocupa el puesto {rank} de {total_countries} países para "{indicator}"{(" en " + year) if year else ""}, ubicándose en el percentil {percentile} — {pos_label}.',
            'tag': pos_label, 'tag_type': pos_tag
        })
        conclusion_parts.append(f'ocupa el puesto {rank} de {total_countries} países (percentil {percentile})')

    # Tendencia histórica
    history           = country_all[[YEAR_COLUMN, indicator]].dropna().copy()
    history[YEAR_COLUMN] = pd.to_numeric(history[YEAR_COLUMN], errors='coerce')
    history           = history.dropna().sort_values(YEAR_COLUMN)

    if len(history) >= 3:
        first_val  = history[indicator].iloc[0]
        last_val   = history[indicator].iloc[-1]
        first_yr   = int(history[YEAR_COLUMN].iloc[0])
        last_yr    = int(history[YEAR_COLUMN].iloc[-1])
        pct_change = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
        min_yr     = int(history.loc[history[indicator].idxmin(), YEAR_COLUMN])
        max_yr     = int(history.loc[history[indicator].idxmax(), YEAR_COLUMN])
        trend_dir  = 'crecimiento' if pct_change > 0 else 'caída'
        sign       = '+' if pct_change >= 0 else ''

        insights.append({
            'type': 'trend', 'title': 'Tendencia histórica',
            'text': f'Entre {first_yr} y {last_yr} el indicador tuvo un cambio de {sign}{pct_change:.1f}%. El valor máximo se registró en {max_yr} y el mínimo en {min_yr}.',
            'tag': f'Tendencia: {trend_dir}',
            'tag_type': 'up' if pct_change > 0 else 'down',
            'extra_tag': f'Mínimo: {min_yr}',
            'extra_tag_type': 'down' if min_yr == (int(year) if year else last_yr) else 'neutral'
        })
        conclusion_parts.append(f'con una variación de {sign}{pct_change:.1f}% entre {first_yr} y {last_yr}')

    # Comparación regional
    REGION_COL = 'Grupo regional'
    if REGION_COL in df.columns:
        country_region = country_all[REGION_COL].dropna().mode()
        if not country_region.empty:
            region_name = country_region.iloc[0]
            if year:
                regional_df = df[(df[REGION_COL] == region_name) &
                                 (df[YEAR_COLUMN].astype(str).str.strip() == yr_str)].copy()
            else:
                regional_df = df[df[REGION_COL] == region_name].copy()

            regional_df[indicator] = pd.to_numeric(regional_df[indicator], errors='coerce')
            regional_avg = regional_df[indicator].mean()

            if not pd.isna(regional_avg) and regional_avg != 0:
                vs_region = ((ref_value - regional_avg) / regional_avg * 100)
                direction = 'supera' if vs_region > 0 else 'está por debajo de'
                sign_r    = '+' if vs_region > 0 else ''

                insights.append({
                    'type': 'regional', 'title': 'Comparación regional',
                    'text': f'Dentro de {region_name}, {country} {direction} el promedio regional ({sign_r}{vs_region:.1f}%).',
                    'tag': region_name, 'tag_type': 'neutral'
                })
                conclusion_parts.append(f'{direction} el promedio de {region_name} en un {abs(vs_region):.1f}%')

    # Detección de atípico
    if len(history) >= 3:
        std_val  = history[indicator].std()
        mean_val = history[indicator].mean()
        z_score  = abs(ref_value - mean_val) / std_val if std_val > 0 else 0

        if z_score > 1.5:
            label = 'máximo histórico' if ref_value > mean_val else 'mínimo histórico'
            insights.append({
                'type': 'outlier', 'title': 'Dato atípico detectado',
                'text': f'El valor {"de " + year if year else "actual"} se desvía {z_score:.1f} desviaciones estándar de la media histórica de {country}, clasificándolo como {label} estadísticamente relevante.',
                'tag': label.capitalize(),
                'tag_type': 'down' if 'mínimo' in label else 'up'
            })
            conclusion_parts.append(f'registrando un {label} estadístico')

    # Conclusión
    income_note = ''
    if 'Grupo regional' in df.columns and not country_all.empty:
        reg = country_all['Grupo regional'].dropna().mode()
        if not reg.empty:
            r = reg.iloc[0].lower()
            if any(x in r for x in ['europe', 'north america', 'europa', 'norteamérica', 'oceania']):
                income_note = 'economía desarrollada'
            elif any(x in r for x in ['latin', 'asia', 'africa', 'middle']):
                income_note = 'economía en desarrollo'

    conclusion = (
        f'{country} {", ".join(conclusion_parts[:3])}. '
        f'{"Es una " + income_note + "." if income_note else ""} '
        f'Estos datos corresponden al indicador "{indicator}" '
        f'{"del año " + year if year else "en el período histórico disponible"}.'
        if conclusion_parts else
        f'No hay suficientes datos para generar una conclusión completa sobre {country}.'
    )

    return jsonify({
        'country': country, 'indicator': indicator,
        'year': year or 'todos', 'value': round(ref_value, 4),
        'insights': insights, 'conclusion': conclusion.strip()
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


# ==================== NIVEL 2 — MODELO MULTIDIMENSIONAL ====================
# Conexión SQL Server local + fallback pandas para Render
# ===========================================================================

try:
    _params_multi = urllib.parse.quote_plus(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=DESKTOP-MKH47I3\\SQLEXPRESS;"
        "DATABASE=ODS_Multidimensional;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    engine_multi = create_engine(
        f"mssql+pyodbc:///?odbc_connect={_params_multi}",
        fast_executemany=True,
        pool_pre_ping=True
    )
    with engine_multi.connect() as _c:
        _c.execute(sa_text("SELECT 1"))
    _multi_db_ok = True
    print("✓ Nivel 2: SQL Server conectado.")
except Exception as _e:
    _multi_db_ok = False
    print(f"⚠ Nivel 2: Sin SQL Server, usando pandas. ({_e})")


def run_olap(sql: str, params: dict = None):
    """Ejecutar consulta OLAP contra SQL Server."""
    with engine_multi.connect() as conn:
        result = conn.execute(sa_text(sql), params or {})
        keys = result.keys()
        return [dict(zip(keys, row)) for row in result.fetchall()]


def _load_df_multi():
    """Carga el CSV para el fallback pandas (Render)."""
    _p1 = os.path.join(BASE_DIR, 'data', 'ODS.csv')
    _p2 = os.path.join(BASE_DIR, 'data', 'ods_data.csv')
    path = _p1 if os.path.exists(_p1) else (_p2 if os.path.exists(_p2) else None)
    if not path:
        return None
    _df = pd.read_csv(path, sep=',', encoding='utf-8-sig', dtype=str)
    _df.columns = _df.columns.str.strip()
    _df['Año'] = pd.to_numeric(_df['Año'], errors='coerce')
    _SKIP = {'Año', 'Grupo regional', 'País', 'Coordenadas', 'Código ISO2', 'Afiliación'}
    for col in [c for c in _df.columns if c not in _SKIP]:
        _df[col] = pd.to_numeric(
            _df[col].str.replace(',', '.', regex=False), errors='coerce'
        )
    return _df.dropna(subset=['Año', 'País'])


_df_multi = None if _multi_db_ok else _load_df_multi()

_CATS = {
    'PIB Total': 'Economico', 'Tasa de crecimiento del PIB': 'Economico', 'PIB per cápita': 'Economico',
    'Tasa de alfabetización juvenil': 'Educativo', 'Tasa de alfabetización de adultos': 'Educativo',
    'Matriculación en primaria': 'Educativo', 'Matriculación en secundaria': 'Educativo',
    'Matriculación en escuelas terciarias': 'Educativo',
    'Población activa Mujer': 'Laboral', 'Población activa Hombres': 'Laboral',
    'Población activa Total': 'Laboral', 'Tasa de desempleo': 'Laboral',
    'Esperanza de vida': 'Social',
    'Población de 0 a 14 años': 'Demografico', 'Población de 15 a 64 años': 'Demografico',
    'Población mayor de 65 años': 'Demografico', 'Población Total': 'Demografico',
    'Población femenina': 'Demografico', 'Población masculina': 'Demografico',
}


@app.route('/api/olap/meta')
def olap_meta():
    if _multi_db_ok:
        regiones    = run_olap("SELECT nombre_region FROM dim_region ORDER BY nombre_region")
        indicadores = run_olap("SELECT nombre, categoria FROM dim_indicador ORDER BY categoria, nombre")
        anios       = run_olap("SELECT id_tiempo AS anio FROM dim_tiempo ORDER BY id_tiempo")
        return jsonify({
            'success': True,
            'regiones':    [r['nombre_region'] for r in regiones],
            'indicadores': indicadores,
            'anios':       [a['anio'] for a in anios],
        })
    _SKIP    = {'Año', 'Grupo regional', 'País', 'Coordenadas', 'Código ISO2', 'Afiliación'}
    ind_cols = [c for c in _df_multi.columns if c not in _SKIP]
    return jsonify({
        'success':    True,
        'regiones':   sorted(_df_multi['Grupo regional'].dropna().unique().tolist()),
        'indicadores':[{'nombre': c, 'categoria': _CATS.get(c, 'N/A')} for c in ind_cols],
        'anios':      sorted(_df_multi['Año'].dropna().astype(int).unique().tolist()),
    })


@app.route('/api/olap/rollup')
def olap_rollup():
    if _multi_db_ok:
        sql = """
        SELECT r.nombre_region AS region, t.decada,
               ROUND(AVG(f.valor),2) AS pib_promedio, COUNT(f.valor) AS n_obs
        FROM fact_indicadores f
        JOIN dim_tiempo t    ON f.id_tiempo    = t.id_tiempo
        JOIN dim_pais p      ON f.id_pais      = p.id_pais
        JOIN dim_region r    ON p.id_region    = r.id_region
        JOIN dim_indicador i ON f.id_indicador = i.id_indicador
        WHERE i.nombre = 'PIB per cápita' AND f.valor IS NOT NULL
        GROUP BY r.nombre_region, t.decada
        ORDER BY r.nombre_region, t.decada
        """
        return jsonify({'success': True, 'data': run_olap(sql)})
    tmp = _df_multi[['Grupo regional', 'Año', 'PIB per cápita']].dropna().copy()
    tmp['decada'] = ((tmp['Año'] // 10) * 10).astype(str) + 's'
    g = tmp.groupby(['Grupo regional', 'decada'])['PIB per cápita'].agg(
        pib_promedio='mean', n_obs='count').reset_index()
    g['pib_promedio'] = g['pib_promedio'].round(2)
    return jsonify({'success': True, 'data': g.rename(columns={'Grupo regional': 'region'}).to_dict(orient='records')})


@app.route('/api/olap/drilldown')
def olap_drilldown():
    region = request.args.get('region', 'Latin America and the Caribbean')
    anio   = request.args.get('year', '2020')
    if _multi_db_ok:
        sql = """
        SELECT p.nombre_pais AS pais, r.nombre_region AS region,
               t.id_tiempo AS anio, ROUND(f.valor,2) AS esperanza_vida
        FROM fact_indicadores f
        JOIN dim_tiempo t    ON f.id_tiempo    = t.id_tiempo
        JOIN dim_pais p      ON f.id_pais      = p.id_pais
        JOIN dim_region r    ON p.id_region    = r.id_region
        JOIN dim_indicador i ON f.id_indicador = i.id_indicador
        WHERE i.nombre = 'Esperanza de vida'
          AND r.nombre_region = :region AND t.id_tiempo = :anio AND f.valor IS NOT NULL
        ORDER BY f.valor DESC
        """
        data = run_olap(sql, {'region': region, 'anio': int(anio)})
    else:
        tmp = _df_multi[
            (_df_multi['Grupo regional'] == region) & (_df_multi['Año'] == int(anio))
        ][['País', 'Grupo regional', 'Año', 'Esperanza de vida']].dropna()
        tmp = tmp.rename(columns={
            'País': 'pais', 'Grupo regional': 'region',
            'Año': 'anio', 'Esperanza de vida': 'esperanza_vida'
        }).sort_values('esperanza_vida', ascending=False)
        data = tmp.to_dict(orient='records')
    return jsonify({'success': True, 'data': data, 'region': region, 'year': anio})


@app.route('/api/olap/slice')
def olap_slice():
    indicador = request.args.get('indicador', 'Tasa de desempleo')
    region    = request.args.get('region', 'Latin America and the Caribbean')
    if _multi_db_ok:
        sql = """
        SELECT t.id_tiempo AS anio, ROUND(AVG(f.valor),2) AS valor_promedio
        FROM fact_indicadores f
        JOIN dim_tiempo t    ON f.id_tiempo    = t.id_tiempo
        JOIN dim_pais p      ON f.id_pais      = p.id_pais
        JOIN dim_region r    ON p.id_region    = r.id_region
        JOIN dim_indicador i ON f.id_indicador = i.id_indicador
        WHERE i.nombre = :indicador AND r.nombre_region = :region AND f.valor IS NOT NULL
        GROUP BY t.id_tiempo ORDER BY t.id_tiempo
        """
        data = run_olap(sql, {'indicador': indicador, 'region': region})
    else:
        tmp  = _df_multi[_df_multi['Grupo regional'] == region][['Año', indicador]].dropna()
        g    = tmp.groupby('Año')[indicador].mean().round(2).reset_index()
        g.columns = ['anio', 'valor_promedio']
        data = g.to_dict(orient='records')
    return jsonify({'success': True, 'data': data, 'indicador': indicador, 'region': region})


@app.route('/api/olap/dice')
def olap_dice():
    anio_ini  = int(request.args.get('year_from', 2000))
    anio_fin  = int(request.args.get('year_to',   2020))
    categoria = request.args.get('categoria', 'Economico')
    if _multi_db_ok:
        sql = """
        SELECT r.nombre_region AS region, i.nombre AS indicador,
               i.categoria, t.decada, ROUND(AVG(f.valor),2) AS valor_promedio
        FROM fact_indicadores f
        JOIN dim_tiempo t    ON f.id_tiempo    = t.id_tiempo
        JOIN dim_pais p      ON f.id_pais      = p.id_pais
        JOIN dim_region r    ON p.id_region    = r.id_region
        JOIN dim_indicador i ON f.id_indicador = i.id_indicador
        WHERE t.id_tiempo BETWEEN :yi AND :yf AND i.categoria = :cat AND f.valor IS NOT NULL
        GROUP BY r.nombre_region, i.nombre, i.categoria, t.decada
        ORDER BY r.nombre_region, i.nombre, t.decada
        """
        data = run_olap(sql, {'yi': anio_ini, 'yf': anio_fin, 'cat': categoria})
    else:
        cols_cat = [c for c, cat in _CATS.items() if cat == categoria and c in _df_multi.columns]
        tmp      = _df_multi[(_df_multi['Año'] >= anio_ini) & (_df_multi['Año'] <= anio_fin)].copy()
        tmp['decada'] = ((tmp['Año'] // 10) * 10).astype(str) + 's'
        rows = []
        for col in cols_cat:
            g = tmp.groupby(['Grupo regional', 'decada'])[col].mean().round(2).reset_index()
            g.columns = ['region', 'decada', 'valor_promedio']
            g['indicador'] = col
            g['categoria'] = categoria
            rows.append(g)
        data = pd.concat(rows).to_dict(orient='records') if rows else []
    return jsonify({'success': True, 'data': data})


@app.route('/api/olap/ranking')
def olap_ranking():
    indicador = request.args.get('indicador', 'PIB per cápita')
    anio      = int(request.args.get('year', 2020))
    top_n     = int(request.args.get('top', 15))
    if _multi_db_ok:
        sql = f"""
        SELECT TOP ({top_n})
            RANK() OVER (ORDER BY f.valor DESC) AS ranking,
            p.nombre_pais AS pais, r.nombre_region AS region,
            ROUND(f.valor,2) AS valor, t.id_tiempo AS anio
        FROM fact_indicadores f
        JOIN dim_tiempo t    ON f.id_tiempo    = t.id_tiempo
        JOIN dim_pais p      ON f.id_pais      = p.id_pais
        JOIN dim_region r    ON p.id_region    = r.id_region
        JOIN dim_indicador i ON f.id_indicador = i.id_indicador
        WHERE i.nombre = :indicador AND t.id_tiempo = :anio AND f.valor IS NOT NULL
        ORDER BY f.valor DESC
        """
        data = run_olap(sql, {'indicador': indicador, 'anio': anio})
    else:
        tmp = _df_multi[_df_multi['Año'] == anio][
            ['País', 'Grupo regional', indicador]
        ].dropna().sort_values(indicador, ascending=False).head(top_n).copy()
        tmp['ranking'] = range(1, len(tmp) + 1)
        tmp['valor']   = tmp[indicador].round(2)
        tmp['anio']    = anio
        tmp = tmp.rename(columns={'País': 'pais', 'Grupo regional': 'region'})
        data = tmp[['ranking', 'pais', 'region', 'valor', 'anio']].to_dict(orient='records')
    return jsonify({'success': True, 'data': data, 'indicador': indicador})


@app.route('/api/olap/tendencia')
def olap_tendencia():
    indicador = request.args.get('indicador', 'Esperanza de vida')
    if _multi_db_ok:
        sql = """
        SELECT t.decada, ROUND(AVG(f.valor),2) AS promedio,
               ROUND(STDEV(f.valor),2) AS desviacion_std, COUNT(f.valor) AS n_obs
        FROM fact_indicadores f
        JOIN dim_tiempo t    ON f.id_tiempo    = t.id_tiempo
        JOIN dim_indicador i ON f.id_indicador = i.id_indicador
        WHERE i.nombre = :indicador AND f.valor IS NOT NULL
        GROUP BY t.decada ORDER BY t.decada
        """
        data = run_olap(sql, {'indicador': indicador})
    else:
        tmp = _df_multi[['Año', indicador]].dropna().copy()
        tmp['decada'] = ((tmp['Año'] // 10) * 10).astype(str) + 's'
        g = tmp.groupby('decada')[indicador].agg(
            promedio='mean', desviacion_std='std', n_obs='count').round(2).reset_index()
        data = g.to_dict(orient='records')
    return jsonify({'success': True, 'data': data, 'indicador': indicador})


# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def not_found(error):
    try:    return render_template('404.html'), 404
    except: return "404 - Página no encontrada", 404


@app.errorhandler(500)
def server_error(error):
    try:    return render_template('500.html'), 500
    except: return "500 - Error del servidor", 500



# ==================== NIVEL 3 — MINERÍA DE DATOS (ORANGE) ====================
 
@app.route('/api/mineria/clusters', methods=['GET'])
def get_clusters():
    """Devuelve los datos clusterizados exportados desde Orange Data Mining"""
    try:
        # Ruta al archivo exportado desde Orange
        cluster_path = os.path.join(BASE_DIR, 'data', 'ods_clusters.csv')
       
        if not os.path.exists(cluster_path):
            return jsonify({'success': False, 'error': 'Archivo ods_clusters.csv no encontrado en la carpeta data/'}), 404
 
        # Leer el CSV generado por Orange
        df_clusters = pd.read_csv(cluster_path, encoding='utf-8-sig')
 
        # Variables exactas que usamos en la gráfica de Orange
        col_pais = 'País'
        col_x = 'Población Total'
        col_y = 'Tasa de crecimiento del PIB'
        col_cluster = 'Cluster'
 
        # Limpiamos nombres de columnas por si Orange agregó espacios
        df_clusters.columns = df_clusters.columns.str.strip()
 
        # Extraemos solo las columnas necesarias y eliminamos nulos
        df_plot = df_clusters[[col_pais, col_x, col_y, col_cluster]].dropna()
        # Convertimos a formato diccionario para JSON
        data = df_plot.to_dict(orient='records')
       
        return jsonify({'success': True, 'data': data})
 
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PUNTO DE ENTRADA ====================

if __name__ == '__main__':
    print("\n" + "=" * 55)
    print("  ODS Explorer — Flask App")
    print("=" * 55)
    print(f"  Inicio:    {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Dataset:   {df.shape if df is not None else 'No cargado'}")
    print(f"  Home:      http://localhost:5000/")
    print(f"  Dashboard: http://localhost:5000/dashboard")
    print(f"  Nivel 2:   http://localhost:5000/multidimensional")
    print("=" * 55 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
