#!/usr/bin/env python3
"""
Script para corregir encoding y verificar gestión de stock en Shopify
Versión mejorada que maneja caracteres especiales y verifica ubicaciones
"""

import os
import sys
import csv
import json
import logging
import html
import unicodedata
import re
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
import shopify

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_encoding_stock.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Cargar variables de entorno
load_dotenv()

class EncodingAndStockFixer:
    def __init__(self):
        """Inicializar el corrector de encoding y stock"""
        self.shop_name = os.getenv('SHOPIFY_SHOP_NAME')
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        
        if self.shop_name and self.access_token:
            self._setup_shopify_api()
        else:
            logging.error("❌ Configuración de Shopify faltante en .env")
            sys.exit(1)
            
    def _setup_shopify_api(self):
        """Configurar la API de Shopify"""
        try:
            shopify.ShopifyResource.set_site(f"https://{self.shop_name}/admin/api/2025-04")
            shopify.ShopifyResource.set_headers({"X-Shopify-Access-Token": self.access_token})
            logging.info("✅ API de Shopify configurada correctamente")
        except Exception as e:
            logging.error(f"❌ Error configurando API de Shopify: {e}")
            sys.exit(1)
    
    def fix_encoding_issues(self, texto: str) -> str:
        """
        Corregir problemas comunes de encoding UTF-8
        """
        if not texto:
            return texto
              # Tabla de correcciones comunes para problemas UTF-8
        correcciones = {
            # Caracteres acentuados minúsculas
            'Ã¡': 'á', 'Ã ': 'à', 'Ã¢': 'â', 'Ã£': 'ã', 'Ã¤': 'ä',
            'Ã©': 'é', 'Ã¨': 'è', 'Ãª': 'ê', 'Ã«': 'ë',
            'Ã­': 'í', 'Ã¬': 'ì', 'Ã®': 'î', 'Ã¯': 'ï',
            'Ã³': 'ó', 'Ã²': 'ò', 'Ã´': 'ô', 'Ãµ': 'õ', 'Ã¶': 'ö',
            'Ãº': 'ú', 'Ã¹': 'ù', 'Ã»': 'û', 'Ã¼': 'ü',
            'Ã±': 'ñ', 'Ã§': 'ç',
            
            # Mayúsculas acentuadas
            'Ã\x81': 'Á', 'Ã\x80': 'À', 'Ã\x82': 'Â', 'Ã\x83': 'Ã', 'Ã\x84': 'Ä',
            'Ã\x89': 'É', 'Ã\x88': 'È', 'Ã\x8a': 'Ê', 'Ã\x8b': 'Ë',
            'Ã\x8d': 'Í', 'Ã\x8c': 'Ì', 'Ã\x8e': 'Î', 'Ã\x8f': 'Ï',
            'Ã\x93': 'Ó', 'Ã\x92': 'Ò', 'Ã\x94': 'Ô', 'Ã\x95': 'Õ', 'Ã\x96': 'Ö',
            'Ã\x9a': 'Ú', 'Ã\x99': 'Ù', 'Ã\x9b': 'Û', 'Ã\x9c': 'Ü',
            'Ã\x91': 'Ñ', 'Ã\x87': 'Ç',
            
            # Otros caracteres especiales
            'â€™': "'", 'â€œ': '"', 'â€\x9d': '"', 'â€"': '–', 'â€"': '—',
            'â€¢': '•', 'â€¦': '…', 'Â°': '°', 'Â®': '®', 'Â©': '©',
            'â„¢': '™', 'Â±': '±', 'Â´': '´', 'Â¨': '¨', 'Â¸': '¸',
            
            # Espacios problemáticos
            'Â ': ' ', 'Âº': 'º', 'ÂªÂº': 'º',
            
            # Correcciones específicas comunes
            'Ã³n': 'ón', 'Ã±o': 'ño', 'Ã©s': 'és', 'Ã¡s': 'ás'
        }
        
        # Aplicar correcciones
        texto_corregido = texto
        for incorrecto, correcto in correcciones.items():
            texto_corregido = texto_corregido.replace(incorrecto, correcto)
        
        # Limpiar caracteres de control y espacios extra
        texto_corregido = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', texto_corregido)
        texto_corregido = re.sub(r'\s+', ' ', texto_corregido).strip()
        
        return texto_corregido
    
    def get_shop_info(self) -> Dict:
        """Obtener información detallada de la tienda"""
        try:
            shop = shopify.Shop.current()
            shop_info = {
                'id': shop.id,
                'name': shop.name,
                'domain': shop.domain,
                'email': shop.email,
                'timezone': shop.timezone,
                'currency': shop.currency,
                'country': shop.country,
                'created_at': shop.created_at
            }
            
            logging.info(f"🏪 Información de la tienda:")
            logging.info(f"   ID: {shop_info['id']}")
            logging.info(f"   Nombre: {shop_info['name']}")
            logging.info(f"   Dominio: {shop_info['domain']}")
            logging.info(f"   País: {shop_info['country']}")
            logging.info(f"   Moneda: {shop_info['currency']}")
            
            return shop_info
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo información de la tienda: {e}")
            return {}
    
    def get_locations_info(self) -> List[Dict]:
        """Obtener información detallada de todas las ubicaciones"""
        try:
            locations = shopify.Location.find()
            locations_info = []
            
            logging.info(f"📍 Ubicaciones encontradas: {len(locations)}")
            
            for loc in locations:
                location_data = {
                    'id': loc.id,
                    'name': loc.name,
                    'address1': getattr(loc, 'address1', ''),
                    'city': getattr(loc, 'city', ''),
                    'country': getattr(loc, 'country_code', ''),
                    'active': getattr(loc, 'active', True),
                    'legacy': getattr(loc, 'legacy', False)
                }
                locations_info.append(location_data)
                
                logging.info(f"   📍 {location_data['name']} (ID: {location_data['id']})")
                logging.info(f"      Dirección: {location_data['address1']}, {location_data['city']}")
                logging.info(f"      Activa: {location_data['active']}")
                
            return locations_info
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo ubicaciones: {e}")
            return []
    
    def test_inventory_permissions(self, location_id: int) -> bool:
        """Probar permisos de inventario en una ubicación específica"""
        try:
            logging.info(f"🧪 Probando permisos de inventario en ubicación {location_id}...")
            
            # Intentar leer niveles de inventario
            inventory_levels = shopify.InventoryLevel.find(location_ids=location_id, limit=5)
            
            if inventory_levels:
                logging.info(f"✅ Permisos de lectura de inventario: OK")
                logging.info(f"   Encontrados {len(inventory_levels)} elementos de inventario")
                
                # Mostrar algunos ejemplos
                for inv in inventory_levels[:3]:
                    logging.info(f"   📦 Item ID: {inv.inventory_item_id} - Disponible: {inv.available}")
                
                return True
            else:
                logging.warning("⚠️ No se encontraron elementos de inventario")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error probando permisos de inventario: {e}")
            return False
    
    def fix_csv_encoding(self, archivo_entrada: str, archivo_salida: str = None) -> str:
        """Corregir encoding de un archivo CSV"""
        if not archivo_salida:
            base_name = os.path.splitext(archivo_entrada)[0]
            archivo_salida = f"{base_name}_fixed.csv"
        
        try:
            # Detectar encoding del archivo original
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-8-sig']
            
            contenido_original = None
            encoding_usado = None
            
            for encoding in encodings_to_try:
                try:
                    with open(archivo_entrada, 'r', encoding=encoding) as f:
                        contenido_original = f.read()
                        encoding_usado = encoding
                        break
                except UnicodeDecodeError:
                    continue
            
            if not contenido_original:
                logging.error(f"❌ No se pudo leer el archivo {archivo_entrada}")
                return None
            
            logging.info(f"📖 Archivo leído con encoding: {encoding_usado}")
            
            # Procesar CSV línea por línea
            lineas_procesadas = []
            lineas = contenido_original.split('\n')
            
            for i, linea in enumerate(lineas):
                if linea.strip():
                    linea_corregida = self.fix_encoding_issues(linea)
                    lineas_procesadas.append(linea_corregida)
                    
                    # Mostrar progreso cada 1000 líneas
                    if i > 0 and i % 1000 == 0:
                        logging.info(f"🔄 Procesadas {i:,} líneas...")
            
            # Guardar archivo corregido
            with open(archivo_salida, 'w', encoding='utf-8', newline='') as f:
                f.write('\n'.join(lineas_procesadas))
            
            logging.info(f"✅ Archivo corregido guardado: {archivo_salida}")
            logging.info(f"📊 Líneas procesadas: {len(lineas_procesadas):,}")
            
            return archivo_salida
            
        except Exception as e:
            logging.error(f"❌ Error corrigiendo encoding del CSV: {e}")
            return None
    
    def create_stock_management_script(self) -> str:
        """Crear script para gestión de stock"""
        script_content = '''#!/usr/bin/env python3
"""
Script para gestión de stock en Shopify
Generado automáticamente
"""

import os
import logging
from dotenv import load_dotenv
import shopify

load_dotenv()

class StockManager:
    def __init__(self):
        self.shop_name = os.getenv('SHOPIFY_SHOP_NAME')
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        self.location_id = None  # Se configurará automáticamente
        
        if self.shop_name and self.access_token:
            shopify.ShopifyResource.set_site(f"https://{self.shop_name}/admin/api/2025-04")
            shopify.ShopifyResource.set_headers({"X-Shopify-Access-Token": self.access_token})
            self._find_main_location()
    
    def _find_main_location(self):
        """Encontrar la ubicación principal"""
        try:
            locations = shopify.Location.find()
            if locations:
                # Buscar OTANCAHUI primero, luego usar la primera disponible
                for loc in locations:
                    if "OTANCAHUI" in loc.name.upper():
                        self.location_id = loc.id
                        self.location_name = loc.name
                        print(f"📍 Usando ubicación: {self.location_name} (ID: {self.location_id})")
                        return
                
                # Si no encuentra OTANCAHUI, usar la primera
                self.location_id = locations[0].id
                self.location_name = locations[0].name
                print(f"📍 Usando ubicación: {self.location_name} (ID: {self.location_id})")
        except Exception as e:
            print(f"❌ Error encontrando ubicación: {e}")
    
    def update_stock(self, sku: str, cantidad: int) -> bool:
        """Actualizar stock de un producto por SKU"""
        try:
            # Buscar producto por SKU
            variants = shopify.Variant.find(sku=sku)
            if not variants:
                print(f"❌ No se encontró producto con SKU: {sku}")
                return False
            
            variant = variants[0]
            inventory_item_id = variant.inventory_item_id
            
            # Actualizar inventario
            inventory_level = shopify.InventoryLevel()
            result = inventory_level.set(
                location_id=self.location_id,
                inventory_item_id=inventory_item_id,
                available=cantidad
            )
            
            if result:
                print(f"✅ Stock actualizado: {sku} -> {cantidad} unidades")
                return True
            else:
                print(f"❌ Error actualizando stock: {sku}")
                return False
                
        except Exception as e:
            print(f"❌ Error actualizando stock para {sku}: {e}")
            return False
    
    def bulk_update_from_csv(self, csv_file: str):
        """Actualizar stock masivo desde CSV"""
        import csv
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    sku = row.get('Variant SKU', '').strip()
                    stock = row.get('Variant Inventory Qty', '0')
                    
                    try:
                        stock = int(float(stock))
                        if stock > 0 and sku:
                            self.update_stock(sku, stock)
                    except (ValueError, TypeError):
                        continue
                        
        except Exception as e:
            print(f"❌ Error en actualización masiva: {e}")

if __name__ == "__main__":
    manager = StockManager()
    
    # Ejemplo de uso:
    # manager.update_stock("SKU123", 50)
    # manager.bulk_update_from_csv("productos_fixed.csv")
'''
        
        script_filename = "stock_manager.py"
        with open(script_filename, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logging.info(f"✅ Script de gestión de stock creado: {script_filename}")
        return script_filename
    
    def run_complete_analysis(self):
        """Ejecutar análisis completo de la configuración"""
        print("\n" + "="*60)
        print("🔧 ANÁLISIS Y CORRECCIÓN DE ENCODING Y STOCK")
        print("="*60)
        
        # 1. Información de la tienda
        print("\n1️⃣ INFORMACIÓN DE LA TIENDA")
        shop_info = self.get_shop_info()
        
        # 2. Información de ubicaciones
        print("\n2️⃣ UBICACIONES DISPONIBLES")
        locations = self.get_locations_info()
        
        # 3. Probar permisos de inventario
        print("\n3️⃣ PROBANDO PERMISOS DE INVENTARIO")
        if locations:
            main_location = locations[0]  # Usar la primera ubicación
            has_inventory_perms = self.test_inventory_permissions(main_location['id'])
            
            if has_inventory_perms:
                print("✅ Permisos de inventario confirmados")
            else:
                print("❌ Sin permisos de inventario o sin productos")
        
        # 4. Buscar archivos CSV para corregir
        print("\n4️⃣ CORRIGIENDO ARCHIVOS CSV")
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
        
        for csv_file in csv_files:
            if not csv_file.endswith('_fixed.csv'):  # No procesar archivos ya corregidos
                print(f"🔄 Procesando: {csv_file}")
                fixed_file = self.fix_csv_encoding(csv_file)
                if fixed_file:
                    print(f"✅ Archivo corregido: {fixed_file}")
        
        # 5. Crear script de gestión de stock
        print("\n5️⃣ CREANDO HERRAMIENTAS DE GESTIÓN")
        stock_script = self.create_stock_management_script()
        
        # 6. Resumen final
        print("\n" + "="*60)
        print("📋 RESUMEN DE CONFIGURACIÓN")
        print("="*60)
        
        if shop_info:
            print(f"🏪 Tienda: {shop_info['name']} (ID: {shop_info['id']})")
        
        if locations:
            print(f"📍 Ubicaciones: {len(locations)}")
            for loc in locations:
                print(f"   - {loc['name']} (ID: {loc['id']})")
        
        print(f"📄 Archivos CSV corregidos disponibles")
        print(f"🛠️ Script de gestión de stock: {stock_script}")
        
        print("\n🎯 PRÓXIMOS PASOS:")
        print("1. Usar los archivos *_fixed.csv para importar productos")
        print("2. Ejecutar stock_manager.py para gestionar inventario")
        print("3. Los caracteres especiales ahora se mostrarán correctamente")

def main():
    try:
        fixer = EncodingAndStockFixer()
        fixer.run_complete_analysis()
    except KeyboardInterrupt:
        print("\n👋 Análisis interrumpido por el usuario")
    except Exception as e:
        logging.error(f"❌ Error inesperado: {e}")
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()
