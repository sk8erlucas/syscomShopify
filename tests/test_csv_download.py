import os
import sys
import requests
import pandas as pd
from dotenv import load_dotenv

# Agregar el directorio padre al path para importar el módulo principal
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from csv_to_shopify import CSVToShopifyImporter

# Cargar variables de entorno
load_dotenv()

def test_csv_download():
    """Test para verificar que el CSV se descarga correctamente"""
    print("=== Test de Descarga de CSV ===")
    
    try:
        # Crear instancia del importador
        importer = CSVToShopifyImporter()
        
        print(f"URL del CSV: {importer.csv_url}")
        
        if not importer.csv_url:
            print("❌ Error: URL del CSV no configurada en .env")
            return False
        
        # Probar la descarga
        print("Descargando CSV...")
        csv_filename = importer.download_csv()
        
        # Verificar que el archivo se creó
        if not os.path.exists(csv_filename):
            print(f"❌ Error: El archivo {csv_filename} no se creó")
            return False
        
        # Verificar el tamaño del archivo
        file_size = os.path.getsize(csv_filename)
        print(f"✅ CSV descargado exitosamente")
        print(f"Archivo: {csv_filename}")
        print(f"Tamaño: {file_size:,} bytes ({file_size/1024:.2f} KB)")
        
        # Intentar parsear el CSV
        print("\nProbando parseo del CSV...")
        df = importer.parse_csv(csv_filename)
        
        print(f"✅ CSV parseado exitosamente")
        print(f"Filas: {len(df):,}")
        print(f"Columnas: {len(df.columns)}")
        
        # Mostrar las primeras columnas
        print(f"\nPrimeras 5 columnas: {list(df.columns[:5])}")
        
        # Verificar columnas importantes
        required_columns = ['nombre', 'precio_bruto', 'referencia', 'marca', 'categoria_principal']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"⚠️  Advertencia: Faltan columnas importantes: {missing_columns}")
        else:
            print("✅ Todas las columnas importantes están presentes")
        
        # Mostrar estadísticas básicas
        print(f"\nEstadísticas básicas:")
        print(f"- Productos con nombre: {df['nombre'].notna().sum():,}")
        print(f"- Productos con precio: {df['precio_bruto'].notna().sum():,}")
        print(f"- Productos con stock: {df['stock_disponible'].notna().sum():,}")
        
        # Mostrar algunos productos de ejemplo
        print(f"\nEjemplos de productos (primeros 3):")
        for i, row in df.head(3).iterrows():
            nombre = row.get('nombre', 'Sin nombre')
            precio = row.get('precio_bruto', 'Sin precio')
            marca = row.get('marca', 'Sin marca')
            print(f"  {i+1}. {nombre} - {precio}€ - {marca}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        print("Posibles causas:")
        print("- Sin conexión a internet")
        print("- URL del CSV no válida")
        print("- Servidor no disponible")
        return False
        
    except pd.errors.EmptyDataError:
        print("❌ Error: El CSV está vacío")
        return False
        
    except pd.errors.ParserError as e:
        print(f"❌ Error parseando CSV: {e}")
        print("El formato del CSV puede haber cambiado")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_csv_data_quality():
    """Test para verificar la calidad de los datos del CSV"""
    print("\n=== Test de Calidad de Datos ===")
    
    try:
        importer = CSVToShopifyImporter()
        
        # Descargar y parsear CSV si no existe
        csv_filename = 'productos_ociostock.csv'
        if not os.path.exists(csv_filename):
            print("Descargando CSV para análisis...")
            csv_filename = importer.download_csv()
        
        df = importer.parse_csv(csv_filename)
        
        print(f"Analizando calidad de {len(df):,} productos...")
        
        # Análisis de completitud
        print(f"\nCompletitud de datos:")
        important_fields = {
            'nombre': 'Nombre del producto',
            'precio_bruto': 'Precio',
            'referencia': 'SKU/Referencia',
            'marca': 'Marca',
            'categoria_principal': 'Categoría',
            'stock_disponible': 'Stock',
            'descripcion': 'Descripción'
        }
        
        for field, description in important_fields.items():
            if field in df.columns:
                complete = df[field].notna().sum()
                percentage = (complete / len(df)) * 100
                print(f"  {description}: {complete:,}/{len(df):,} ({percentage:.1f}%)")
            else:
                print(f"  {description}: ❌ Campo no encontrado")
        
        # Análisis de precios
        if 'precio_bruto' in df.columns:
            precios_validos = pd.to_numeric(df['precio_bruto'], errors='coerce').notna()
            precio_min = pd.to_numeric(df['precio_bruto'], errors='coerce').min()
            precio_max = pd.to_numeric(df['precio_bruto'], errors='coerce').max()
            precio_promedio = pd.to_numeric(df['precio_bruto'], errors='coerce').mean()
            
            print(f"\nAnálisis de precios:")
            print(f"  Precios válidos: {precios_validos.sum():,}/{len(df):,}")
            print(f"  Rango: {precio_min:.2f}€ - {precio_max:.2f}€")
            print(f"  Promedio: {precio_promedio:.2f}€")
        
        # Análisis de imágenes
        if 'csv_imagenes' in df.columns:
            productos_con_imagenes = df['csv_imagenes'].notna().sum()
            print(f"\nImágenes:")
            print(f"  Productos con imágenes: {productos_con_imagenes:,}/{len(df):,}")
        
        # Análisis de categorías
        if 'categoria_principal' in df.columns:
            categorias = df['categoria_principal'].value_counts()
            print(f"\nTop 5 categorías:")
            for categoria, count in categorias.head().items():
                print(f"  {categoria}: {count:,} productos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en análisis de calidad: {e}")
        return False

def main():
    """Función principal del test"""
    print("🧪 Ejecutando tests del importador CSV\n")
    
    # Test 1: Descarga del CSV
    success1 = test_csv_download()
    
    # Test 2: Calidad de datos
    success2 = test_csv_data_quality()
    
    # Resumen
    print(f"\n{'='*50}")
    print("RESUMEN DE TESTS:")
    print(f"✅ Descarga CSV: {'PASÓ' if success1 else 'FALLÓ'}")
    print(f"✅ Calidad datos: {'PASÓ' if success2 else 'FALLÓ'}")
    
    if success1 and success2:
        print("\n🎉 Todos los tests pasaron exitosamente!")
        print("El CSV se puede descargar y procesar correctamente.")
    else:
        print("\n⚠️  Algunos tests fallaron. Revisa la configuración.")

if __name__ == "__main__":
    main()
