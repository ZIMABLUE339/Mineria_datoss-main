"""
Script para descargar datos ODS del Google Sheets
"""

import urllib.request
import os
from pathlib import Path

def download_ods_data():
    """Descarga el archivo CSV desde Google Sheets"""
    
    # Crear carpeta de datos si no existe
    Path('data').mkdir(exist_ok=True)
    
    # URL del Google Sheets (exportado como CSV)
    sheet_id = '1wkkgqcA-ruldAVnp5_FOUymfi1yiOH8r'
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'
    
    output_file = 'data/ods_data.csv'
    
    print("=" * 60)
    print("📊 Descargando datos ODS del Banco Mundial")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Guardando en: {output_file}")
    print()
    
    try:
        # Descargar archivo
        print("⏳ Descargando... (esto puede tomar unos segundos)")
        urllib.request.urlretrieve(url, output_file)
        
        # Verificar descarga
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ Descarga completada exitosamente")
            print(f"   Tamaño del archivo: {file_size / 1024:.2f} KB")
            
            # Mostrar preview
            import pandas as pd
            df = pd.read_csv(output_file)
            print(f"\n📈 Estadísticas del dataset:")
            print(f"   - Registros: {len(df):,}")
            print(f"   - Columnas: {len(df.columns)}")
            print(f"   - Primeras columnas: {', '.join(df.columns[:5])}")
            print("\n✨ Datos listos para usar en el dashboard")
            return True
        else:
            print("❌ Error: No se pudo guardar el archivo")
            return False
            
    except urllib.error.URLError as e:
        print(f"❌ Error de conexión: {e}")
        print("   Por favor, verifica tu conexión a internet")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == '__main__':
    success = download_ods_data()
    exit(0 if success else 1)
