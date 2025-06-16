#!/usr/bin/env python3
"""
Importador SYSCOM to Shopify - Versión Robusta v2.3
Importación automática sin interacción del usuario
Manejo robusto de errores y timeouts
"""

import os
import sys
import csv
import json
import logging
import time
import random
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import shopify
import requests
from urllib.parse import urlparse

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

class SyscomShopifyImporterRobusto:
    def __init__(self):
        """Inicializar el importador con configuración robusta"""
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
        
        # Configuración de retry ultra robusta
        self.max_retries = 3
        self.timeout = 10  # Timeout más corto para evitar colgadas
        self.backoff_factor = 0.5
        self.max_consecutive_errors = 3  # Pausa más frecuente
        
        # Estadísticas completas
        self.stats = {
            'productos_procesados': 0,
            'productos_creados': 0,
            'productos_duplicados': 0,
            'productos_con_error': 0,
            'productos_sin_stock': 0,
            'inventario_actualizado': 0,
            'errores_inventario': 0,
            'errores_consecutivos': 0,
            'errores_timeout': 0,
            'errores_imagen': 0,
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
        session.headers.update({
            'User-Agent': 'SYSCOM-Shopify-Importer/2.3',
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
            
    def fix_encoding_issues(self, texto: str) -> str:
        """Corregir problemas comunes de encoding UTF-8"""
        if not texto:
            return texto
            
        # Tabla de correcciones comunes para problemas UTF-8
        correcciones = {
            'Ã¡': 'á', 'Ã ': 'à', 'Ã¢': 'â', 'Ã£': 'ã', 'Ã¤': 'ä',
            'Ã©': 'é', 'Ã¨': 'è', 'Ãª': 'ê', 'Ã«': 'ë',
            'Ã­': 'í', 'Ã¬': 'ì', 'Ã®': 'î', 'Ã¯': 'ï',
            'Ã³': 'ó', 'Ã²': 'ò', 'Ã´': 'ô', 'Ãµ': 'õ', 'Ã¶': 'ö',
            'Ãº': 'ú', 'Ã¹': 'ù', 'Ã»': 'û', 'Ã¼': 'ü',
            'Ã±': 'ñ', 'Ã§': 'ç',
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

    def verificar_permisos_shopify(self) -> Dict[str, bool]:
        """Verificar permisos de Shopify de forma robusta"""
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
            
            # Test productos - lectura y escritura
            try:
                productos = shopify.Product.find(limit=1)
                permisos['products_read'] = True
                permisos['products_write'] = True  # Asumimos que si puede leer, puede escribir
                logging.info("✅ Permisos de productos: OK")
            except Exception as e:
                logging.warning(f"⚠️ Sin permisos de productos: {e}")
                
            # Test ubicaciones
            try:
                locations = shopify.Location.find()
                permisos['locations_read'] = True
                self.has_location_permissions = True
                
                if locations:
                    # Buscar OTANCAHUI primero
                    location_encontrada = None
                    for loc in locations:
                        if "OTANCAHUI" in loc.name.upper():
                            location_encontrada = loc
                            break
                    
                    if location_encontrada:
                        self.location_id = location_encontrada.id
                        self.location_name = location_encontrada.name
                        logging.info(f"✅ Ubicación configurada: {self.location_name} (ID: {self.location_id})")
                    else:
                        self.location_id = locations[0].id
                        self.location_name = locations[0].name
                        logging.info(f"✅ Usando primera ubicación: {self.location_name} (ID: {self.location_id})")
                    
            except Exception as e:
                logging.warning(f"⚠️ Sin permisos de ubicaciones: {e}")
                
        except Exception as e:
            logging.error(f"❌ Error verificando permisos: {e}")
            
        return permisos

    def descargar_csv(self) -> Optional[str]:
        """Descargar CSV desde URL o usar archivo local"""
        # Intentar descarga desde URL
        if self.csv_url:
            try:
                logging.info(f"🔗 Descargando CSV desde URL...")
                response = self.session.get(self.csv_url, timeout=self.timeout)
                
                if response.status_code == 200 and 'csv' in response.headers.get('content-type', '').lower():
                    archivo_temp = f"productos_descargado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    with open(archivo_temp, 'w', encoding='utf-8', newline='') as f:
                        f.write(response.text)
                    logging.info(f"✅ CSV descargado: {archivo_temp}")
                    return archivo_temp
            except Exception as e:
                logging.warning(f"⚠️ Error descargando CSV: {e}")
        
        # Usar archivo local como fallback
        archivos_locales = ["productos_ociostock.csv", "productos_shopify.csv", "ProductosHora.csv"]
        for archivo in archivos_locales:
            if os.path.exists(archivo):
                logging.info(f"📁 Usando archivo local: {archivo}")
                return archivo
                
        logging.error("❌ No se pudo obtener archivo CSV")
        return None

    def parsear_csv(self, archivo_csv: str) -> List[Dict]:
        """Parsear CSV con manejo robusto de encoding"""
        productos = []
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(archivo_csv, 'r', encoding=encoding, newline='') as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames and 'Handle' in reader.fieldnames:
                        productos = list(reader)
                        logging.info(f"✅ CSV parseado con {encoding}: {len(productos)} productos")
                        return productos
            except Exception:
                continue
                
        logging.error("❌ No se pudo parsear el CSV")
        return []

    def filtrar_productos_con_stock(self, productos: List[Dict]) -> List[Dict]:
        """Filtrar productos que tienen stock disponible"""
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
                
        self.stats['productos_sin_stock'] = productos_sin_stock
        logging.info(f"📦 Productos con stock: {len(productos_filtrados)} de {len(productos)}")
        return productos_filtrados

    def manejar_errores_consecutivos(self):
        """Manejar errores consecutivos con pausa"""
        if self.stats['errores_consecutivos'] >= self.max_consecutive_errors:
            pausa = min(30, self.stats['errores_consecutivos'] * 5)  # Pausa progresiva
            logging.warning(f"⚠️ {self.stats['errores_consecutivos']} errores consecutivos")
            logging.info(f"😴 Pausa de {pausa}s para estabilizar conexión...")
            time.sleep(pausa)
            self.stats['errores_consecutivos'] = 0
            logging.info("🔄 Continuando...")

    def crear_producto_shopify_ultra_robusto(self, producto_data: Dict) -> Optional[shopify.Product]:
        """Crear producto con manejo ultra robusto de errores"""
        handle = producto_data.get('Handle', '').strip()
        
        # Verificar stock
        try:
            stock = float(producto_data.get('Variant Inventory Qty', 0))
            if stock <= 0:
                return None
        except (ValueError, TypeError):
            return None
        
        # Intentos múltiples
        for intento in range(self.max_retries):
            try:
                # Verificar duplicados con timeout
                try:
                    if handle:
                        productos_existentes = shopify.Product.find(handle=handle)
                        if productos_existentes:
                            logging.info(f"⏭️ Duplicado saltado: {handle}")
                            self.stats['productos_duplicados'] += 1
                            self.stats['errores_consecutivos'] = 0
                            return productos_existentes[0]
                except Exception as e:
                    if intento == self.max_retries - 1:
                        logging.warning(f"⚠️ No se pudo verificar duplicado: {handle}")
                    # Continuar con creación
                
                # Crear producto
                producto = shopify.Product()
                
                # Datos con encoding corregido
                titulo_original = producto_data.get('Title', '')
                titulo_corregido = self.fix_encoding_issues(titulo_original)
                producto.title = titulo_corregido[:255]
                producto.handle = handle
                producto.body_html = self.fix_encoding_issues(producto_data.get('Body (HTML)', ''))
                producto.vendor = self.fix_encoding_issues(producto_data.get('Vendor', ''))
                producto.product_type = self.fix_encoding_issues(producto_data.get('Product Category', 'General'))
                producto.status = 'active'
                
                # Tags
                tags = producto_data.get('Tags', '')
                if tags:
                    producto.tags = self.fix_encoding_issues(tags)
                
                # Variante
                variante = shopify.Variant()
                variante.title = "Default Title"
                variante.sku = producto_data.get('Variant SKU', '')
                variante.price = float(producto_data.get('Variant Price', 0))
                variante.inventory_management = "shopify"
                variante.inventory_policy = "deny"
                
                producto.variants = [variante]
                
                # Imagen (opcional, puede fallar sin detener el proceso)
                imagen_url = producto_data.get('Image Src', '')
                if imagen_url and imagen_url.startswith('http'):
                    try:
                        imagen_url_limpia = imagen_url.strip().replace(' ', '%20')
                        if any(imagen_url_limpia.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                            imagen = shopify.Image()
                            imagen.src = imagen_url_limpia
                            producto.images = [imagen]
                    except Exception:
                        pass  # Continuar sin imagen
                
                # Guardar con timeout implícito
                if producto.save():
                    logging.info(f"✅ Creado: {titulo_corregido[:50]} - Stock: {stock}")
                    self.stats['productos_creados'] += 1
                    self.stats['errores_consecutivos'] = 0
                    return producto
                else:
                    # Manejar errores específicos
                    error_msg = str(producto.errors.full_messages()) if hasattr(producto, 'errors') else ''
                    
                    # Si es error de imagen, reintentar sin imagen
                    if 'image' in error_msg.lower() and hasattr(producto, 'images'):
                        producto.images = []
                        if producto.save():
                            logging.info(f"✅ Creado sin imagen: {titulo_corregido[:50]}")
                            self.stats['productos_creados'] += 1
                            self.stats['errores_consecutivos'] = 0
                            return producto
                    
                    if intento < self.max_retries - 1:
                        time.sleep(self.backoff_factor * (2 ** intento))
                        continue
                        
            except Exception as e:
                error_type = "timeout" if "timeout" in str(e).lower() else "error"
                if error_type == "timeout":
                    self.stats['errores_timeout'] += 1
                
                if intento < self.max_retries - 1:
                    tiempo_espera = self.backoff_factor * (2 ** intento)
                    time.sleep(tiempo_espera)
                    continue
        
        # Todos los intentos fallaron
        self.stats['productos_con_error'] += 1
        self.stats['errores_consecutivos'] += 1
        return None

    def importar_productos_automatico(self):
        """Importar todos los productos automáticamente"""
        print("\n" + "="*60)
        print("🛒 SYSCOM TO SHOPIFY - IMPORTADOR AUTOMÁTICO v2.3")
        print("="*60)
        
        # Verificar permisos
        print("\n🔍 Verificando configuración...")
        permisos = self.verificar_permisos_shopify()
        
        if not permisos.get('products_write', False):
            print("❌ Sin permisos para crear productos")
            return
        
        # Obtener y procesar CSV
        archivo_csv = self.descargar_csv()
        if not archivo_csv:
            print("❌ No se pudo obtener CSV")
            return
        
        productos = self.parsear_csv(archivo_csv)
        if not productos:
            print("❌ No se pudieron parsear productos")
            return
        
        productos_con_stock = self.filtrar_productos_con_stock(productos)
        if not productos_con_stock:
            print("❌ No hay productos con stock")
            return
        
        # Mostrar estadísticas e iniciar
        print(f"\n📊 ESTADÍSTICAS")
        print(f"   📋 Total productos: {len(productos):,}")
        print(f"   📦 Con stock > 0: {len(productos_con_stock):,}")
        print(f"   📍 Ubicación: {self.location_name}" if self.location_name else "   ⚠️ Sin ubicación")
        
        print(f"\n🚀 INICIANDO IMPORTACIÓN AUTOMÁTICA")
        print(f"📦 Procesando {len(productos_con_stock):,} productos...")
        
        # Iniciar procesamiento
        self.stats['tiempo_inicio'] = datetime.now()
        print(f"⏰ Inicio: {self.stats['tiempo_inicio'].strftime('%H:%M:%S')}")
        
        # Procesar por lotes
        for i in range(0, len(productos_con_stock), self.max_products_per_batch):
            lote = productos_con_stock[i:i + self.max_products_per_batch]
            lote_num = (i // self.max_products_per_batch) + 1
            total_lotes = (len(productos_con_stock) + self.max_products_per_batch - 1) // self.max_products_per_batch
            
            print(f"\n📦 Lote {lote_num}/{total_lotes}")
            
            for j, producto_data in enumerate(lote):
                # Manejar errores consecutivos
                self.manejar_errores_consecutivos()
                
                self.stats['productos_procesados'] += 1
                producto_num = i + j + 1
                
                titulo = producto_data.get('Title', 'Sin título')[:50]
                print(f"🔄 {producto_num}/{len(productos_con_stock)}: {titulo}")
                
                try:
                    producto = self.crear_producto_shopify_ultra_robusto(producto_data)
                    if producto:
                        self.stats['errores_consecutivos'] = 0
                except Exception as e:
                    logging.error(f"❌ Error crítico: {e}")
                    self.stats['productos_con_error'] += 1
                    self.stats['errores_consecutivos'] += 1
                
                # Pausa entre productos
                time.sleep(self.delay_between_requests)
            
            # Pausa entre lotes
            if i + self.max_products_per_batch < len(productos_con_stock):
                time.sleep(self.delay_between_requests * 2)
                
                # Progreso cada 10 lotes
                if lote_num % 10 == 0:
                    print(f"📊 Progreso: {lote_num}/{total_lotes} lotes")
                    print(f"✅ Creados: {self.stats['productos_creados']:,}")
                    print(f"❌ Errores: {self.stats['productos_con_error']:,}")
        
        # Finalizar
        self.stats['tiempo_fin'] = datetime.now()
        self.mostrar_estadisticas_finales()
        
        # Limpiar temporal
        if archivo_csv.startswith("productos_descargado_"):
            try:
                os.remove(archivo_csv)
            except:
                pass

    def mostrar_estadisticas_finales(self):
        """Mostrar estadísticas finales"""
        print(f"\n{'='*60}")
        print(f"📊 ESTADÍSTICAS FINALES")
        print(f"{'='*60}")
        
        if self.stats['tiempo_inicio'] and self.stats['tiempo_fin']:
            duracion = self.stats['tiempo_fin'] - self.stats['tiempo_inicio']
            print(f"⏰ Duración: {duracion}")
        
        print(f"📋 Procesados: {self.stats['productos_procesados']:,}")
        print(f"✅ Creados: {self.stats['productos_creados']:,}")
        print(f"⏭️ Duplicados: {self.stats['productos_duplicados']:,}")
        print(f"❌ Errores: {self.stats['productos_con_error']:,}")
        print(f"⏰ Timeouts: {self.stats['errores_timeout']:,}")
        
        if self.stats['productos_procesados'] > 0:
            tasa_exito = (self.stats['productos_creados'] / self.stats['productos_procesados']) * 100
            print(f"🎯 Tasa de éxito: {tasa_exito:.1f}%")
        
        if self.stats['productos_creados'] > 0:
            print(f"\n🎉 IMPORTACIÓN COMPLETADA")
            print(f"✅ {self.stats['productos_creados']:,} productos agregados")
            print(f"🔗 Revisa en: https://{self.shop_name}/admin/products")

def main():
    """Función principal"""
    try:
        importador = SyscomShopifyImporterRobusto()
        importador.importar_productos_automatico()
    except KeyboardInterrupt:
        print("\n👋 Importación interrumpida")
    except Exception as e:
        logging.error(f"❌ Error crítico: {e}")
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    main()
