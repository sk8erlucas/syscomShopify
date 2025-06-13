import os
import sys
from dotenv import load_dotenv

# Agregar el directorio padre al path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Importar todos los tests
from test_connection import test_shopify_connection
from test_csv_download import test_csv_download, test_csv_data_quality
from test_functions import test_xml_parsing, test_image_processing, test_data_extraction

# Cargar variables de entorno
load_dotenv()

def run_all_tests():
    """Ejecuta todos los tests disponibles"""
    print("🚀 EJECUTANDO SUITE COMPLETA DE TESTS")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: Conexión Shopify
    print("\n1️⃣  TEST DE CONEXIÓN SHOPIFY")
    print("-" * 40)
    try:
        test_results['shopify_connection'] = test_shopify_connection()
    except Exception as e:
        print(f"❌ Error en test de conexión: {e}")
        test_results['shopify_connection'] = False
    
    # Test 2: Descarga CSV
    print("\n2️⃣  TEST DE DESCARGA CSV")
    print("-" * 40)
    try:
        test_results['csv_download'] = test_csv_download()
    except Exception as e:
        print(f"❌ Error en test de descarga: {e}")
        test_results['csv_download'] = False
    
    # Test 3: Calidad de datos CSV
    print("\n3️⃣  TEST DE CALIDAD DE DATOS")
    print("-" * 40)
    try:
        test_results['csv_quality'] = test_csv_data_quality()
    except Exception as e:
        print(f"❌ Error en test de calidad: {e}")
        test_results['csv_quality'] = False
    
    # Test 4: Parsing XML
    print("\n4️⃣  TEST DE PARSING XML")
    print("-" * 40)
    try:
        test_results['xml_parsing'] = test_xml_parsing()
    except Exception as e:
        print(f"❌ Error en test XML: {e}")
        test_results['xml_parsing'] = False
    
    # Test 5: Procesamiento de imágenes
    print("\n5️⃣  TEST DE PROCESAMIENTO DE IMÁGENES")
    print("-" * 40)
    try:
        test_results['image_processing'] = test_image_processing()
    except Exception as e:
        print(f"❌ Error en test de imágenes: {e}")
        test_results['image_processing'] = False
    
    # Test 6: Extracción de datos
    print("\n6️⃣  TEST DE EXTRACCIÓN DE DATOS")
    print("-" * 40)
    try:
        test_results['data_extraction'] = test_data_extraction()
    except Exception as e:
        print(f"❌ Error en test de extracción: {e}")
        test_results['data_extraction'] = False
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL DE TESTS")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        test_display = test_name.replace('_', ' ').title()
        print(f"{test_display:.<40} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"TESTS PASADOS: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ¡EXCELENTE! Todos los tests pasaron")
        print("✅ El sistema está listo para usar")
    elif passed >= total * 0.5:
        print("\n⚠️  La mayoría de tests pasaron")
        print("🔧 Revisa los tests que fallaron antes de continuar")
    else:
        print("\n🚨 Muchos tests fallaron")
        print("🛠️  Revisa la configuración antes de usar el sistema")
    
    return test_results

def run_basic_tests():
    """Ejecuta solo los tests básicos (sin Shopify)"""
    print("🧪 EJECUTANDO TESTS BÁSICOS (SIN SHOPIFY)")
    print("=" * 50)
    
    test_results = {}
    
    # Test 1: Descarga CSV
    print("\n1️⃣  TEST DE DESCARGA CSV")
    print("-" * 30)
    try:
        test_results['csv_download'] = test_csv_download()
    except Exception as e:
        print(f"❌ Error: {e}")
        test_results['csv_download'] = False
    
    # Test 2: Funciones del sistema
    print("\n2️⃣  TEST DE FUNCIONES")
    print("-" * 30)
    try:
        xml_ok = test_xml_parsing()
        img_ok = test_image_processing()
        data_ok = test_data_extraction()
        test_results['functions'] = xml_ok and img_ok and data_ok
    except Exception as e:
        print(f"❌ Error: {e}")
        test_results['functions'] = False
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN TESTS BÁSICOS")
    print("=" * 50)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        test_display = test_name.replace('_', ' ').title()
        print(f"{test_display:.<30} {status}")
    
    print(f"\nRESULTADO: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡Perfecto! El sistema básico funciona")
    else:
        print("⚠️  Hay problemas que resolver")

def main():
    """Función principal del runner de tests"""
    print("🧪 SUITE DE TESTS - IMPORTADOR CSV A SHOPIFY")
    print("=" * 60)
    print("1. Ejecutar todos los tests (incluye Shopify)")
    print("2. Ejecutar tests básicos (sin Shopify)")
    print("3. Solo test de descarga CSV")
    print("4. Solo test de conexión Shopify")
    
    choice = input("\nSelecciona una opción (1-4): ").strip()
    
    if choice == "1":
        run_all_tests()
    elif choice == "2":
        run_basic_tests()
    elif choice == "3":
        print("\n🔍 EJECUTANDO SOLO TEST DE CSV")
        print("-" * 40)
        test_csv_download()
        test_csv_data_quality()
    elif choice == "4":
        print("\n🔍 EJECUTANDO SOLO TEST DE SHOPIFY")
        print("-" * 40)
        test_shopify_connection()
    else:
        print("❌ Opción no válida")

if __name__ == "__main__":
    main()
