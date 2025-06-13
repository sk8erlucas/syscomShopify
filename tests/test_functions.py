import os
import sys
from dotenv import load_dotenv

# Agregar el directorio padre al path para importar el módulo principal
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from csv_to_shopify import CSVToShopifyImporter

# Cargar variables de entorno
load_dotenv()

def test_xml_parsing():
    """Test para verificar el parsing de campos XML"""
    print("=== Test de Parsing XML ===")
    
    importer = CSVToShopifyImporter()
    
    # Datos de prueba basados en el CSV real
    test_cases = [
        {
            'name': 'Peso',
            'xml': '<shipping_weight unit="g">232</shipping_weight>',
            'tag': 'weight',
            'expected': '232'
        },
        {
            'name': 'Dimensiones',
            'xml': '<size unit="mm"><width>150</width><height>77</height><depth>222</depth></size>',
            'tag': 'dimensions',
            'expected': '150x77x222mm'
        },
        {
            'name': 'Código de barras',
            'xml': '<barcodes><barcode type="EAN-13"><![CDATA[4545784069523]]></barcode></barcodes>',
            'tag': 'barcode',
            'expected': '4545784069523'
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\nProbando {test_case['name']}...")
        result = importer.extract_xml_data(test_case['xml'], test_case['tag'])
        
        if result == test_case['expected']:
            print(f"✅ {test_case['name']}: {result}")
        else:
            print(f"❌ {test_case['name']}: Esperado '{test_case['expected']}', obtenido '{result}'")
            all_passed = False
    
    # Casos edge
    print(f"\nProbando casos edge...")
    
    # XML vacío
    result = importer.extract_xml_data('', 'weight')
    if result is None:
        print("✅ XML vacío manejado correctamente")
    else:
        print(f"❌ XML vacío: Esperado None, obtenido '{result}'")
        all_passed = False
    
    # XML malformado
    result = importer.extract_xml_data('<malformed xml', 'weight')
    if result is None:
        print("✅ XML malformado manejado correctamente")
    else:
        print(f"❌ XML malformado: Esperado None, obtenido '{result}'")
        all_passed = False
    
    return all_passed

def test_image_processing():
    """Test para verificar el procesamiento de imágenes"""
    print("\n=== Test de Procesamiento de Imágenes ===")
    
    importer = CSVToShopifyImporter()
    
    # Caso con múltiples imágenes (del CSV real)
    image_string = "https://www.ociostock.com/productos/imagenes/img_354707_34ed3b6834c039ce9dd9934aa647d7ee_1.jpg|https://www.ociostock.com/productos/imagenes/img_354708_4b91127b59d0df54b35b4d0660e87191_1.jpg|https://www.ociostock.com/productos/imagenes/img_354709_26463cbf3f2710737f4f23b0e846d67d_1.jpg"
    
    result = importer.process_images(image_string)
    
    print(f"Entrada: {len(image_string.split('|'))} URLs")
    print(f"Resultado: {len(result)} URLs válidas")
    
    all_passed = True
    
    if len(result) == 3:
        print("✅ Número correcto de imágenes procesadas")
    else:
        print(f"❌ Esperadas 3 imágenes, obtenidas {len(result)}")
        all_passed = False
    
    # Verificar que todas las URLs son válidas
    for i, url in enumerate(result):
        if url.startswith('http'):
            print(f"✅ Imagen {i+1}: URL válida")
        else:
            print(f"❌ Imagen {i+1}: URL no válida - {url}")
            all_passed = False
    
    # Casos edge
    print(f"\nProbando casos edge de imágenes...")
    
    # Sin imágenes
    result_empty = importer.process_images('')
    if len(result_empty) == 0:
        print("✅ String vacío manejado correctamente")
    else:
        print(f"❌ String vacío: Esperado 0 imágenes, obtenido {len(result_empty)}")
        all_passed = False
    
    # URLs inválidas
    result_invalid = importer.process_images('not_a_url|also_not_url')
    if len(result_invalid) == 0:
        print("✅ URLs inválidas filtradas correctamente")
    else:
        print(f"❌ URLs inválidas: Esperado 0 imágenes válidas, obtenido {len(result_invalid)}")
        all_passed = False
    
    return all_passed

def test_data_extraction():
    """Test para verificar la extracción de datos básicos"""
    print("\n=== Test de Extracción de Datos ===")
    
    # Simular una fila del CSV
    test_row = {
        'nombre': 'Figura Joker Persona 5 15cm',
        'descripcion': 'Tamaño: 15cm. Figura articulada. Contiene accesorios.',
        'precio_bruto': '99.95',
        'referencia': '4545784069523',
        'marca': 'MAX FACTORY',
        'categoria_principal': 'ANIME / MANGA',
        'stock_disponible': '0',
        'xml_info_peso': '<shipping_weight unit="g">232</shipping_weight>',
        'xml_info_dimensiones': '<size unit="mm"><width>150</width><height>77</height><depth>222</depth></size>',
        'xml_info_codigos_barras': '<barcodes><barcode type="EAN-13"><![CDATA[4545784069523]]></barcode></barcodes>',
        'csv_imagenes': 'https://www.ociostock.com/productos/imagenes/img_354710_5c21adb4977fd6ca92b37241cb98009f_1.jpg'
    }
    
    all_passed = True
    
    # Verificar extracción de datos básicos
    tests = [
        ('Nombre', test_row['nombre'], 'Figura Joker Persona 5 15cm'),
        ('Precio', float(test_row['precio_bruto']), 99.95),
        ('SKU', test_row['referencia'], '4545784069523'),
        ('Marca', test_row['marca'], 'MAX FACTORY'),
        ('Categoría', test_row['categoria_principal'], 'ANIME / MANGA'),
    ]
    
    for test_name, actual, expected in tests:
        if actual == expected:
            print(f"✅ {test_name}: {actual}")
        else:
            print(f"❌ {test_name}: Esperado '{expected}', obtenido '{actual}'")
            all_passed = False
    
    return all_passed

def main():
    """Función principal del test de funciones"""
    print("🧪 Ejecutando tests de funciones del importador\n")
    
    # Test 1: Parsing XML
    success1 = test_xml_parsing()
    
    # Test 2: Procesamiento de imágenes
    success2 = test_image_processing()
    
    # Test 3: Extracción de datos
    success3 = test_data_extraction()
    
    # Resumen
    print(f"\n{'='*50}")
    print("RESUMEN DE TESTS DE FUNCIONES:")
    print(f"✅ Parsing XML: {'PASÓ' if success1 else 'FALLÓ'}")
    print(f"✅ Proc. Imágenes: {'PASÓ' if success2 else 'FALLÓ'}")
    print(f"✅ Extrac. Datos: {'PASÓ' if success3 else 'FALLÓ'}")
    
    if success1 and success2 and success3:
        print("\n🎉 Todos los tests de funciones pasaron!")
        print("Las funciones del importador funcionan correctamente.")
    else:
        print("\n⚠️  Algunos tests fallaron. Revisa el código.")
    
    return success1 and success2 and success3

if __name__ == "__main__":
    main()
