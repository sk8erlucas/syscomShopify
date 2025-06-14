#!/usr/bin/env python3
"""
Importador SYSCOM to Shopify - Versión Mejorada v2.2
Maneja mejor los permisos limitados de Shopify API
Incluye manejo de stock, timeouts, retry e interfaz interactiva
"""

import os
import sys
import csv
import json
import logging
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import shopify
import requests
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Cargar variables de entorno
load_dotenv()

class SyscomShopifyImporter:
    def __init__(self):
        """Inicializar el importador con configuración mejorada"""
        self.shop_name = os.getenv('SHOPIFY_SHOP_NAME')
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        self.csv_url = os.getenv('CSV_URL')
        self.max_products_per_batch = int(os.getenv('MAX_PRODUCTS_PER_BATCH', 5))
        self.delay_between_requests = float(os.getenv('DELAY_BETWEEN_REQUESTS', 2))
        
        # Estado del sistema
        self.location_id = None
        self.location_name = None
        self.has_location_permissions = False
        self.has_inventory_permissions = False
        
        # Configuración de retry para requests
        self.max_retries = 3
        self.timeout = 30
        self.backoff_factor = 0.3
        
        # Estadísticas mejoradas
        self.stats = {
            'productos_procesados': 0,
            'productos_creados': 0,
            'productos_duplicados': 0,
            'productos_con_error': 0,
            'productos_sin_stock': 0,
            'inventario_actualizado': 0,
            'errores_inventario': 0,
            'tiempo_inicio': None,
            'tiempo_fin': None
        }
        
        # Configurar sesión con retry
        self.session = self._crear_sesion_con_retry()
        
        # Configurar Shopify API
        if self.shop_name and self.access_token:
            self._setup_shopify_api()
            
    def _crear_sesion_con_retry(self):
        """Crear sesión de requests con retry automático"""
        session = requests.Session()
        
        # Configurar strategy de retry usando una implementación simple
        session.headers.update({
            'User-Agent': 'SYSCOM-Shopify-Importer/2.2',
            'Accept': 'text/csv, application/csv, text/plain, */*'
        })
        
        return session
            
    def _setup_shopify_api(self):
        """Configurar la API de Shopify"""
        try:
            shopify.ShopifyResource.set_site(f"https://{self.shop_name}/admin/api/2025-04")
            shopify.ShopifyResource.set_headers({"X-Shopify-Access-Token": self.access_token})
            logging.info("✅ API de Shopify configurada correctamente")
        except Exception as e:
            logging.error(f"❌ Error configurando API de Shopify: {e}")
            
    def verificar_permisos_shopify(self) -> Dict[str, bool]:
        """Verificar qué permisos tenemos en Shopify"""
        permisos = {
            'shop_read': False,
            'products_read': False,
            'products_write': False,
            'locations_read': False,
            'inventory_read': False,
            'inventory_write': False
        }
        
        try:
            # Test básico: leer info de la tienda
            shop = shopify.Shop.current()
            permisos['shop_read'] = True
            logging.info(f"✅ Tienda conectada: {shop.name}")
            
            # Test productos - lectura
            try:
                productos = shopify.Product.find(limit=1)
                permisos['products_read'] = True
                logging.info("✅ Permisos de lectura de productos: OK")
            except Exception as e:
                logging.warning(f"⚠️ Sin permisos de lectura de productos: {e}")
                
            # Test productos - escritura (creamos y eliminamos un producto de prueba)
            try:
                test_product = shopify.Product()
                test_product.title = f"TEST PRODUCT {datetime.now().timestamp()}"
                test_product.product_type = "Test"
                test_product.status = "draft"
                
                if test_product.save():
                    permisos['products_write'] = True
                    logging.info("✅ Permisos de escritura de productos: OK")
                    
                    # Eliminar producto de prueba
                    test_product.destroy()
                    logging.info("✅ Producto de prueba eliminado")
                else:
                    logging.warning("⚠️ Sin permisos de escritura de productos")
                    
            except Exception as e:
                logging.warning(f"⚠️ Sin permisos de escritura de productos: {e}")
                
            # Test ubicaciones - BUSCAR ESPECÍFICAMENTE OTANCAHUI 802
            try:
                locations = shopify.Location.find()
                permisos['locations_read'] = True
                self.has_location_permissions = True
                
                if locations:
                    # Buscar específicamente OTANCAHUI 802
                    location_encontrada = None
                    logging.info(f"📍 Ubicaciones disponibles:")
                    for loc in locations:
                        logging.info(f"   - {loc.name} (ID: {loc.id})")
                        if "OTANCAHUI" in loc.name.upper():
                            location_encontrada = loc
                            break
                    
                    if location_encontrada:
                        self.location_id = location_encontrada.id
                        self.location_name = location_encontrada.name
                        logging.info(f"✅ Ubicación OTANCAHUI configurada: {self.location_name} (ID: {self.location_id})")
                    else:
                        # Usar la primera ubicación como fallback
                        self.location_id = locations[0].id
                        self.location_name = locations[0].name
                        logging.warning(f"⚠️ OTANCAHUI no encontrada, usando: {self.location_name} (ID: {self.location_id})")
                    
            except Exception as e:
                logging.warning(f"⚠️ Sin permisos de ubicaciones: {e}")
                logging.info("💡 Para manejar inventario necesitas permisos 'read_locations'")
                
            # Test inventario
            if self.location_id:
                try:
                    inventory_levels = shopify.InventoryLevel.find(location_ids=self.location_id, limit=1)
                    permisos['inventory_read'] = True
                    permisos['inventory_write'] = True  # Asumimos que si puede leer, puede escribir
                    self.has_inventory_permissions = True
                    logging.info("✅ Permisos de inventario: OK")
                    
                except Exception as e:
                    logging.warning(f"⚠️ Sin permisos de inventario: {e}")
                    
        except Exception as e:
            logging.error(f"❌ Error verificando permisos: {e}")
            
        return permisos
        
    def descargar_csv(self, usar_local_si_falla: bool = True) -> Optional[str]:
        """Descargar CSV desde URL o usar archivo local con retry"""
        
        # Intentar descarga desde URL con retry
        if self.csv_url:
            for intento in range(self.max_retries):
                try:
                    logging.info(f"🔗 Descargando CSV desde: {self.csv_url} (Intento {intento + 1}/{self.max_retries})")
                    
                    response = self.session.get(
                        self.csv_url, 
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        
                        # Verificar si es realmente un CSV
                        if 'csv' in content_type.lower() or self._es_contenido_csv(response.text):
                            archivo_temp = f"productos_descargado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                            
                            with open(archivo_temp, 'w', encoding='utf-8', newline='') as f:
                                f.write(response.text)
                                
                            logging.info(f"✅ CSV descargado exitosamente: {archivo_temp}")
                            return archivo_temp
                        else:
                            logging.warning(f"⚠️ El contenido descargado no es un CSV válido (Content-Type: {content_type})")
                            logging.info("💡 La URL devuelve HTML, probablemente hay un problema de autenticación")
                            break  # No reintentar si el contenido es HTML
                            
                    else:
                        logging.warning(f"⚠️ Error descargando CSV: HTTP {response.status_code}")
                        if intento < self.max_retries - 1:
                            tiempo_espera = self.backoff_factor * (2 ** intento)
                            logging.info(f"⏳ Esperando {tiempo_espera:.1f}s antes del siguiente intento...")
                            time.sleep(tiempo_espera)
                        
                except Exception as e:
                    logging.warning(f"⚠️ Error descargando CSV (intento {intento + 1}): {e}")
                    if intento < self.max_retries - 1:
                        tiempo_espera = self.backoff_factor * (2 ** intento)
                        logging.info(f"⏳ Esperando {tiempo_espera:.1f}s antes del siguiente intento...")
                        time.sleep(tiempo_espera)
                
        # Usar archivo local como fallback
        if usar_local_si_falla:
            archivos_locales = [
                "productos_ociostock.csv",
                "productos_shopify.csv",
                "ProductosHora.csv"
            ]
            for archivo in archivos_locales:
                if os.path.exists(archivo):
                    logging.info(f"📁 Usando archivo local: {archivo}")
                    return archivo
                    
        logging.error("❌ No se pudo obtener archivo CSV (ni descargar ni local)")
        return None
        
    def _es_contenido_csv(self, contenido: str) -> bool:
        """Verificar si el contenido parece ser un CSV válido"""
        # Si contiene HTML, definitivamente no es CSV
        if '<html' in contenido.lower() or '<body' in contenido.lower() or '<!doctype' in contenido.lower():
            return False
            
        # Verificar si las primeras líneas tienen estructura de CSV
        lineas = contenido.split('\n')[:10]
        
        for linea in lineas:
            if linea.strip():
                # Si tiene comas y parece una cabecera CSV
                if ',' in linea and ('Handle' in linea or 'Title' in linea or 'SKU' in linea):
                    return True
                    
        return False
        
    def parsear_csv(self, archivo_csv: str) -> List[Dict]:
        """Parsear CSV con manejo robusto de encoding"""
        productos = []
        
        # Intentar diferentes encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                logging.info(f"🔄 Intentando encoding: {encoding}")
                
                with open(archivo_csv, 'r', encoding=encoding, newline='') as f:
                    reader = csv.DictReader(f)
                    
                    # Verificar que las columnas necesarias estén presentes
                    if not reader.fieldnames or 'Handle' not in reader.fieldnames:
                        continue
                        
                    productos = list(reader)
                    
                    logging.info(f"✅ CSV parseado con encoding {encoding}")
                    logging.info(f"📋 Productos encontrados: {len(productos)}")
                    logging.info(f"📝 Columnas: {len(reader.fieldnames)}")
                    
                    return productos
                    
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logging.error(f"❌ Error parseando CSV con {encoding}: {e}")
                continue
                
        logging.error("❌ No se pudo parsear el CSV con ningún encoding")
        return []
        
    def filtrar_productos_con_stock(self, productos: List[Dict]) -> List[Dict]:
        """Filtrar productos que tienen stock disponible (> 0)"""
        productos_filtrados = []
        productos_sin_stock = 0
        
        for producto in productos:
            try:
                stock = float(producto.get('Variant Inventory Qty', 0))
                if stock > 0:
                    productos_filtrados.append(producto)
                else:
                    productos_sin_stock += 1
            except (ValueError, TypeError):
                productos_sin_stock += 1
                continue
                
        self.stats['productos_sin_stock'] = productos_sin_stock
        logging.info(f"📦 Productos con stock > 0: {len(productos_filtrados)} de {len(productos)}")
        logging.info(f"🚫 Productos sin stock (filtrados): {productos_sin_stock}")
        return productos_filtrados
        
    def crear_producto_shopify(self, producto_data: Dict) -> Optional[shopify.Product]:
        """Crear un producto en Shopify con manejo de errores mejorado"""
        try:
            # Verificar stock antes de crear
            stock = float(producto_data.get('Variant Inventory Qty', 0))
            if stock <= 0:
                logging.info(f"⏭️ Producto sin stock saltado: {producto_data.get('Handle', 'Sin handle')}")
                self.stats['productos_sin_stock'] += 1
                return None
            
            # Verificar si el producto ya existe
            handle = producto_data.get('Handle', '').strip()
            if handle:
                productos_existentes = shopify.Product.find(handle=handle)
                if productos_existentes:
                    logging.info(f"⏭️ Producto duplicado saltado: {handle}")
                    self.stats['productos_duplicados'] += 1
                    return productos_existentes[0]
                    
            # Crear nuevo producto
            producto = shopify.Product()
              # Datos básicos con corrección de encoding
            titulo_original = producto_data.get('Title', '')
            titulo_corregido = self.fix_encoding_issues(titulo_original)
            
            descripcion_original = producto_data.get('Body (HTML)', '')
            descripcion_corregida = self.fix_encoding_issues(descripcion_original)
            
            producto.title = titulo_corregido[:255]  # Limitar título
            producto.handle = handle
            producto.body_html = descripcion_corregida
            producto.vendor = self.fix_encoding_issues(producto_data.get('Vendor', ''))
            producto.product_type = self.fix_encoding_issues(producto_data.get('Product Category', 'General'))
            producto.status = 'active'  # Siempre activo si tiene stock
            
            # Log si se hicieron correcciones
            if titulo_original != titulo_corregido:
                logging.info(f"🔧 Título corregido: '{titulo_original[:50]}...' -> '{titulo_corregido[:50]}...'")
            if descripcion_original != descripcion_corregida and descripcion_original:
                logging.info(f"🔧 Descripción corregida para: {handle}")
              # Tags con corrección de encoding
            tags = producto_data.get('Tags', '')
            if tags:
                tags_corregidas = self.fix_encoding_issues(tags)
                producto.tags = tags_corregidas
                
            # Variante principal
            variante = shopify.Variant()
            variante.title = "Default Title"
            variante.sku = producto_data.get('Variant SKU', '')
            
            # Precio
            try:
                precio = float(producto_data.get('Variant Price', 0))
                variante.price = precio
            except (ValueError, TypeError):
                variante.price = 0
                
            # Configurar inventario
            variante.inventory_management = "shopify"
            variante.inventory_policy = "deny"
            
            # Peso (si está disponible)
            peso = producto_data.get('Variant Grams', '')
            if peso:
                try:
                    variante.grams = int(float(peso))
                except (ValueError, TypeError):
                    pass
                    
            producto.variants = [variante]
            
            # Imagen principal
            imagen_url = producto_data.get('Image Src', '')
            if imagen_url and imagen_url.startswith('http'):
                try:
                    imagen = shopify.Image()
                    imagen.src = imagen_url
                    producto.images = [imagen]
                except Exception as e:
                    logging.warning(f"⚠️ Error añadiendo imagen para {handle}: {e}")
                    
            # Guardar producto
            if producto.save():
                logging.info(f"✅ Producto creado: {producto.title} (ID: {producto.id}) - Stock: {stock}")
                self.stats['productos_creados'] += 1
                
                # Intentar actualizar inventario si tenemos permisos
                if self.has_inventory_permissions and self.location_id:
                    self._actualizar_inventario_con_retry(producto.variants[0].id, int(stock))
                else:
                    logging.warning(f"⚠️ No se puede actualizar inventario automáticamente para {handle}")
                    logging.info(f"💡 Configura manualmente {int(stock)} unidades en {self.location_name or 'tu ubicación'}")
                    
                return producto
            else:
                logging.error(f"❌ Error creando producto {handle}: {producto.errors.full_messages()}")
                self.stats['productos_con_error'] += 1
                return None
                
        except Exception as e:
            logging.error(f"❌ Error inesperado creando producto: {e}")
            self.stats['productos_con_error'] += 1
            return None
            
    def _actualizar_inventario_con_retry(self, variant_id: int, cantidad: int):
        """Actualizar inventario con retry"""
        for intento in range(self.max_retries):
            try:
                if not self.location_id:
                    logging.warning("⚠️ No hay location_id para actualizar inventario")
                    return
                    
                # Buscar inventory item
                variant = shopify.Variant.find(variant_id)
                if not variant:
                    logging.warning(f"⚠️ No se encontró variante {variant_id}")
                    return
                    
                inventory_item_id = variant.inventory_item_id
                
                # Actualizar inventario
                inventory_level = shopify.InventoryLevel()
                result = inventory_level.set(
                    location_id=self.location_id,
                    inventory_item_id=inventory_item_id,
                    available=cantidad
                )
                
                if result:
                    logging.info(f"📦 Inventario actualizado: {cantidad} unidades en {self.location_name}")
                    self.stats['inventario_actualizado'] += 1
                    return
                else:
                    logging.warning(f"⚠️ No se pudo actualizar inventario para variante {variant_id}")
                    
            except Exception as e:
                logging.warning(f"⚠️ Error actualizando inventario (intento {intento + 1}): {e}")
                if intento < self.max_retries - 1:
                    time.sleep(self.backoff_factor * (2 ** intento))
                else:
                    self.stats['errores_inventario'] += 1
                    
    def importar_productos_interactivo(self):
        """Interfaz interactiva para importar productos"""
        print("\n" + "="*60)
        print("🛒 SYSCOM TO SHOPIFY - IMPORTADOR INTERACTIVO v2.2")
        print("="*60)
        
        # Verificar permisos primero
        print("\n🔍 Verificando permisos y configuración...")
        permisos = self.verificar_permisos_shopify()
        
        if not permisos['products_write']:
            print("❌ Sin permisos para crear productos en Shopify")
            return
            
        # Obtener archivo CSV
        archivo_csv = self.descargar_csv()
        if not archivo_csv:
            print("❌ No se pudo obtener archivo CSV")
            return
            
        # Parsear productos
        productos = self.parsear_csv(archivo_csv)
        if not productos:
            print("❌ No se pudieron parsear productos del CSV")
            return
            
        # Filtrar productos con stock
        productos_con_stock = self.filtrar_productos_con_stock(productos)
        
        if not productos_con_stock:
            print("❌ No hay productos con stock disponible")
            return
            
        # Mostrar estadísticas
        print(f"\n📊 ESTADÍSTICAS DEL CSV")
        print(f"   📋 Total productos: {len(productos):,}")
        print(f"   📦 Con stock > 0: {len(productos_con_stock):,}")
        print(f"   🚫 Sin stock: {len(productos) - len(productos_con_stock):,}")
        print(f"   📍 Ubicación: {self.location_name} (ID: {self.location_id})" if self.location_name else "   ⚠️ Sin ubicación configurada")
        
        # Preguntar cuántos importar
        print(f"\n❓ ¿Cuántos productos quieres importar?")
        print(f"   1. Importar TODOS los productos con stock ({len(productos_con_stock):,})")
        print(f"   2. Importar un número específico")
        print(f"   3. Importar solo una muestra pequeña (10 productos)")
        print(f"   4. Cancelar")
        
        while True:
            try:
                opcion = input("\nSelecciona una opción (1-4): ").strip()
                
                if opcion == '1':
                    limite = None
                    break
                elif opcion == '2':
                    while True:
                        try:
                            limite = int(input(f"¿Cuántos productos importar? (1-{len(productos_con_stock)}): "))
                            if 1 <= limite <= len(productos_con_stock):
                                break
                            else:
                                print(f"❌ Número inválido. Debe estar entre 1 y {len(productos_con_stock)}")
                        except ValueError:
                            print("❌ Por favor ingresa un número válido")
                    break
                elif opcion == '3':
                    limite = 10
                    break
                elif opcion == '4':
                    print("👋 Importación cancelada")
                    return
                else:
                    print("❌ Opción inválida")
                    
            except KeyboardInterrupt:
                print("\n👋 Importación cancelada")
                return
                
        # Confirmar importación
        productos_a_importar = min(limite or len(productos_con_stock), len(productos_con_stock))
        print(f"\n🚀 Se importarán {productos_a_importar:,} productos")
        
        if not self.has_inventory_permissions:
            print("⚠️ ADVERTENCIA: Sin permisos de inventario")
            print("   Los productos se crearán pero tendrás que configurar el stock manualmente")
            
        confirmacion = input("\n¿Continuar? (y/n): ").strip().lower()
        if confirmacion not in ['y', 'yes', 'sí', 's']:
            print("👋 Importación cancelada")
            return
            
        # Iniciar importación
        self.stats['tiempo_inicio'] = datetime.now()
        print(f"\n🚀 INICIANDO IMPORTACIÓN DE {productos_a_importar:,} PRODUCTOS")
        print(f"⏰ Inicio: {self.stats['tiempo_inicio'].strftime('%H:%M:%S')}")
        
        stats = self.importar_productos(archivo_csv, limite)
        
        # Finalizar
        self.stats['tiempo_fin'] = datetime.now()
        self.mostrar_estadisticas_detalladas()
        
        # Limpiar archivo temporal
        if archivo_csv.startswith("productos_descargado_"):
            try:
                os.remove(archivo_csv)
                logging.info(f"🗑️ Archivo temporal eliminado: {archivo_csv}")
            except:
                pass
                
    def importar_productos(self, archivo_csv: str = None, limite: int = None) -> Dict:
        """Importar productos desde CSV con límite opcional"""
        
        # Obtener archivo CSV si no se proporciona
        if not archivo_csv:
            archivo_csv = self.descargar_csv()
            if not archivo_csv:
                logging.error("❌ No se pudo obtener archivo CSV")
                return self.stats
                
        # Parsear productos si no están ya parseados
        productos = self.parsear_csv(archivo_csv)
        if not productos:
            logging.error("❌ No se pudieron parsear productos del CSV")
            return self.stats
            
        # Filtrar productos con stock
        productos_con_stock = self.filtrar_productos_con_stock(productos)
        
        # Aplicar límite si se especifica
        if limite:
            productos_con_stock = productos_con_stock[:limite]
            logging.info(f"📊 Limitando importación a {limite} productos")
            
        logging.info(f"📋 Productos a importar: {len(productos_con_stock)}")
        
        # Importar productos por lotes
        for i in range(0, len(productos_con_stock), self.max_products_per_batch):
            lote = productos_con_stock[i:i + self.max_products_per_batch]
            lote_num = i//self.max_products_per_batch + 1
            total_lotes = (len(productos_con_stock) + self.max_products_per_batch - 1) // self.max_products_per_batch
            
            logging.info(f"📦 Procesando lote {lote_num}/{total_lotes} ({len(lote)} productos)")
            
            for j, producto_data in enumerate(lote):
                self.stats['productos_procesados'] += 1
                producto_num = i + j + 1
                
                logging.info(f"🔄 Procesando producto {producto_num}/{len(productos_con_stock)}: {producto_data.get('Title', 'Sin título')[:50]}...")
                
                # Crear producto
                producto = self.crear_producto_shopify(producto_data)
                
                # Delay entre requests
                if self.delay_between_requests > 0:
                    time.sleep(self.delay_between_requests)
                    
            # Delay entre lotes
            if i + self.max_products_per_batch < len(productos_con_stock):
                logging.info(f"⏸️ Pausa entre lotes: {self.delay_between_requests * 2}s")
                time.sleep(self.delay_between_requests * 2)
                
        return self.stats
        
    def mostrar_estadisticas_detalladas(self):
        """Mostrar estadísticas finales detalladas"""
        print(f"\n{'='*60}")
        print(f"📊 ESTADÍSTICAS FINALES DE IMPORTACIÓN")
        print(f"{'='*60}")
        
        if self.stats['tiempo_inicio'] and self.stats['tiempo_fin']:
            duracion = self.stats['tiempo_fin'] - self.stats['tiempo_inicio']
            print(f"⏰ Duración total: {duracion}")
            print(f"📅 Finalizado: {self.stats['tiempo_fin'].strftime('%H:%M:%S')}")
            print()
            
        print(f"📋 Productos procesados: {self.stats['productos_procesados']:,}")
        print(f"✅ Productos creados: {self.stats['productos_creados']:,}")
        print(f"⏭️ Productos duplicados (saltados): {self.stats['productos_duplicados']:,}")
        print(f"🚫 Productos sin stock (filtrados): {self.stats['productos_sin_stock']:,}")
        print(f"❌ Productos con error: {self.stats['productos_con_error']:,}")
        print(f"📦 Inventarios actualizados: {self.stats['inventario_actualizado']:,}")
        print(f"⚠️ Errores de inventario: {self.stats['errores_inventario']:,}")
        
        if self.stats['productos_procesados'] > 0:
            tasa_exito = (self.stats['productos_creados'] / self.stats['productos_procesados']) * 100
            print(f"🎯 Tasa de éxito: {tasa_exito:.1f}%")
            
        print(f"{'='*60}")
        
        if self.stats['productos_creados'] > 0:
            print(f"🎉 IMPORTACIÓN EXITOSA!")
            print(f"✅ {self.stats['productos_creados']:,} productos agregados a tu tienda Shopify")
            
            if self.stats['inventario_actualizado'] < self.stats['productos_creados']:
                print(f"⚠️ RECORDATORIO: Algunos inventarios necesitan configuración manual")
                print(f"   Ve a tu Admin de Shopify -> Products -> Inventory")
                print(f"   Configura el stock en: {self.location_name or 'tu ubicación'}")
        else:
            print(f"❌ No se pudieron crear productos")
            
        print(f"\n🔗 Revisa tus productos en: https://{self.shop_name}/admin/products")
        
    def fix_encoding_issues(self, texto: str) -> str:
        """
        Corregir problemas comunes de encoding UTF-8 en títulos y descripciones
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
            'Ã\x8D': 'Í', 'Ã\x8C': 'Ì', 'Ã\x8e': 'Î', 'Ã\x8f': 'Ï',
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
        import re
        texto_corregido = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', texto_corregido)
        texto_corregido = re.sub(r'\s+', ' ', texto_corregido).strip()
        
        return texto_corregido

def main():
    """Función principal del script"""
    try:
        importador = SyscomShopifyImporter()
        importador.importar_productos_interactivo()
    except KeyboardInterrupt:
        print("\n👋 Programa interrumpido por el usuario")
    except Exception as e:
        logging.error(f"❌ Error inesperado: {e}")
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()
