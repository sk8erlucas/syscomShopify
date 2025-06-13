import os
import requests
import pandas as pd
import shopify
import time
import logging
from dotenv import load_dotenv
from urllib.parse import urlparse
import re
import xml.etree.ElementTree as ET
from functools import wraps

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def retry_on_timeout(max_retries=3, timeout_delay=2):
    """Decorador para reintentar operaciones que fallan por timeout"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e).lower()
                    # Detectar errores de timeout o conexión
                    if any(keyword in error_msg for keyword in ['timeout', 'timed out', 'connection', 'refused', '10060', 'read timeout']):
                        if attempt < max_retries - 1:
                            print(f"⚠️ Timeout/conexión (intento {attempt + 1}/{max_retries}): {e}")
                            print(f"🔄 Reintentando en {timeout_delay} segundos...")
                            time.sleep(timeout_delay * (attempt + 1))  # Backoff exponencial
                            continue
                        else:
                            print(f"❌ Error después de {max_retries} intentos: {e}")
                            raise
                    else:
                        # Si no es un error de timeout, lanzar inmediatamente
                        raise
            return None
        return wrapper
    return decorator


class CSVToShopifyImporter:
    def __init__(self):
        self.shop_name = os.getenv('SHOPIFY_SHOP_NAME')
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        self.csv_url = os.getenv('CSV_URL')
        self.max_products_per_batch = int(
            os.getenv('MAX_PRODUCTS_PER_BATCH', 10))
        self.delay_between_requests = float(
            os.getenv('DELAY_BETWEEN_REQUESTS', 1))

        # Configurar Shopify con la versión correcta de API y timeouts
        self.api_version = '2025-04'
        shop_url = f"https://{self.shop_name}/admin/api/{self.api_version}"
        session = shopify.Session(
            shop_url, self.api_version, self.access_token)
        shopify.ShopifyResource.activate_session(session)
          # Configurar timeouts más agresivos para evitar cuelgues
        shopify.ShopifyResource.timeout = 15  # 15 segundos timeout

    def download_csv(self):
        """Descarga el CSV desde la URL proporcionada"""
        try:
            logger.info(f"Descargando CSV desde: {self.csv_url}")
            response = requests.get(self.csv_url, timeout=30)
            response.raise_for_status()

            # Guardar el CSV localmente
            csv_filename = 'productos_ociostock.csv'
            with open(csv_filename, 'wb') as f:
                f.write(response.content)

            logger.info(f"CSV descargado exitosamente: {csv_filename}")
            return csv_filename

        except Exception as e:
            logger.error(f"Error descargando CSV: {e}")
            raise

    def parse_csv(self, csv_filename):
        """Parsea el CSV y lo convierte en un DataFrame"""
        try:
            # El CSV usa ; como separador
            df = pd.read_csv(csv_filename, sep=';', encoding='utf-8')
            logger.info(f"CSV parseado exitosamente. Filas: {len(df)}")
            return df
        except Exception as e:
            logger.error(f"Error parseando CSV: {e}")
            raise

    def extract_xml_data(self, xml_string, tag_name):
        """Extrae datos de campos XML"""
        if not xml_string or pd.isna(xml_string):
            return None

        try:
            # Limpiar el XML si es necesario
            xml_string = str(xml_string).strip()
            if not xml_string.startswith('<'):
                return None

            root = ET.fromstring(xml_string)

            if tag_name == 'weight':
                # Buscar shipping_weight directamente o con cualquier atributo
                weight_elem = root.find('.//shipping_weight')
                if weight_elem is not None:
                    return weight_elem.text
                # Si no funciona, buscar por tag sin namespaces
                for elem in root.iter():
                    if 'shipping_weight' in elem.tag or elem.tag == 'shipping_weight':
                        return elem.text

            elif tag_name == 'dimensions':
                # Buscar size directamente
                size_elem = root.find('.//size')
                if size_elem is not None:
                    width = size_elem.find('width')
                    height = size_elem.find('height')
                    depth = size_elem.find('depth')
                    if all([width is not None, height is not None, depth is not None]):
                        return f"{width.text}x{height.text}x{depth.text}mm"
                # Búsqueda alternativa sin namespaces
                width_val = height_val = depth_val = None
                for elem in root.iter():
                    if elem.tag == 'width':
                        width_val = elem.text
                    elif elem.tag == 'height':
                        height_val = elem.text
                    elif elem.tag == 'depth':
                        depth_val = elem.text
                if all([width_val, height_val, depth_val]):
                    return f"{width_val}x{height_val}x{depth_val}mm"

            elif tag_name == 'barcode':
                # Buscar barcode y extraer CDATA
                for elem in root.iter():
                    if 'barcode' in elem.tag:
                        # El texto puede estar en CDATA
                        return elem.text if elem.text else None

        except ET.ParseError:
            return None
        except Exception:
            return None

        return None

    def process_images(self, image_urls_string):
        """Procesa las URLs de imágenes"""
        if not image_urls_string or pd.isna(image_urls_string):
            return []

        # Las imágenes están separadas por |
        image_urls = str(image_urls_string).split('|')
        # Filtrar URLs válidas
        valid_urls = []
        for url in image_urls:
            url = url.strip()
            if url and url.startswith('http'):
                valid_urls.append(url)

        return valid_urls[:10]  # Máximo 10 imágenes por producto
    
    @retry_on_timeout(max_retries=3, timeout_delay=2)
    def create_shopify_product(self, row):
        """Crea un producto en Shopify desde una fila del CSV"""
        try:
            # Extraer datos básicos
            title = str(row['nombre']) if pd.notna(
                row['nombre']) else 'Producto sin título'
            description = str(row['descripcion']) if pd.notna(
                row['descripcion']) else ''
            price = float(row['precio_bruto']) if pd.notna(
                row['precio_bruto']) else 0.0
            sku = str(row['referencia']) if pd.notna(row['referencia']) else ''
            vendor = str(row['marca']) if pd.notna(row['marca']) else ''
            # Usar categoría estándar de Shopify para figuras/juguetes
            product_type = "Toys & Games"
            
            # Verificar si el producto ya existe
            if self.product_exists(title):
                print(f"⚠️  PRODUCTO YA EXISTE: {title}")
                logger.info(
                    f"Producto '{title}' ya existe en Shopify, saltando...")
                self._last_product_existed = True
                return None

            # Verificar stock usando la columna hay_stock
            hay_stock_value = row.get('hay_stock', 0)
            
            # Debug: mostrar el valor de hay_stock
            print(f"🔍 DEBUG STOCK - hay_stock: '{hay_stock_value}' (tipo: {type(hay_stock_value)})")
            
            # Convertir a entero de forma robusta
            has_stock = 0
            if pd.notna(hay_stock_value):
                try:
                    has_stock = int(hay_stock_value)
                    print(f"🔍 DEBUG STOCK - hay_stock convertido: {has_stock}")
                except (ValueError, TypeError) as e:
                    print(f"🔍 DEBUG STOCK - Error conversión hay_stock: {e}")
                    has_stock = 0
            
            # Si no hay stock disponible (hay_stock = 0), saltar el producto
            if has_stock <= 0:
                print(f"⚠️  SIN STOCK: {title} - hay_stock: {has_stock}")
                logger.info(f"Producto '{title}' sin stock disponible (hay_stock={has_stock}), saltando...")
                return None
            
            # Para la cantidad de inventario, usaremos un valor por defecto ya que hay_stock solo indica si hay o no
            # Podemos usar stock_disponible si existe y es válido, o usar un valor por defecto
            stock_disponible_value = row.get('stock_disponible', 1)
            inventory_quantity = 1  # Valor por defecto
            
            if pd.notna(stock_disponible_value):
                try:
                    stock_str = str(stock_disponible_value).strip()
                    if stock_str and stock_str.replace('.', '', 1).replace(',', '', 1).replace('-', '', 1).isdigit():
                        stock_str = stock_str.replace(',', '.')
                        inventory_quantity = max(1, int(float(stock_str)))  # Mínimo 1 si hay stock
                except (ValueError, TypeError):
                    inventory_quantity = 1  # Valor por defecto si hay stock
            
            print(f"🔍 DEBUG STOCK - Cantidad final inventario: {inventory_quantity}")

            # Extraer peso y dimensiones
            weight = self.extract_xml_data(row.get('xml_info_peso'), 'weight')
            dimensions = self.extract_xml_data(
                row.get('xml_info_dimensiones'), 'dimensions')
            barcode = self.extract_xml_data(
                row.get('xml_info_codigos_barras'), 'barcode')

            # Procesar imágenes
            image_urls = self.process_images(row.get('csv_imagenes'))

            # Crear descripción HTML mejorada
            html_description = self.create_rich_description(row, dimensions)

            # Crear el producto
            product = shopify.Product()
            product.title = title
            product.body_html = html_description
            product.vendor = vendor
            product.product_type = product_type            # Crear tags siempre con "Figuras de acción"
            tags = ["Figuras de acción"]

            product.tags = tags

            # Agregar metafields para información adicional
            metafields = []

            # Metafield para EAN/Código de barras
            if barcode:
                metafields.append({
                    'namespace': 'product_info',
                    'key': 'ean_code',
                    'value': barcode,
                    'type': 'single_line_text_field'
                })

            # Metafield para dimensiones
            if dimensions:
                metafields.append({
                    'namespace': 'product_info',
                    'key': 'dimensions',
                    'value': dimensions,
                    'type': 'single_line_text_field'
                })

            # Metafield para peso
            if weight:
                metafields.append({
                    'namespace': 'product_info',
                    'key': 'weight_grams',
                    'value': weight,
                    'type': 'number_integer'
                })

            # Metafield para URL original
            if pd.notna(row.get('product_url')):
                metafields.append({
                    'namespace': 'product_info',
                    'key': 'original_url',
                    'value': str(row['product_url']),
                    'type': 'url'
                })            # Crear variante con configuración de inventario mejorada
            variant = shopify.Variant()
            variant.price = price
            variant.sku = sku
              # Configurar inventario
            variant.inventory_management = 'shopify'
            variant.inventory_policy = 'deny'  # No permitir ventas cuando no hay stock
            
            # NO configurar inventory_quantity aquí, lo haremos después con InventoryLevel
            # variant.inventory_quantity = inventory_quantity
            
            # Configurar seguimiento de inventario
            variant.track_quantity = True
            
            print(f"🔍 CONFIGURANDO INVENTARIO: {inventory_quantity} unidades (se aplicará después de crear el producto)")

            if weight:
                try:
                    # Convertir gramos a kilogramos
                    weight_in_kg = float(weight) / 1000
                    variant.weight = weight_in_kg
                    variant.weight_unit = 'kg'
                except:
                    pass

            if barcode:
                variant.barcode = barcode

            product.variants = [variant]

            # Agregar imágenes
            images = []
            for img_url in image_urls:
                image = shopify.Image()
                image.src = img_url
                images.append(image)

            if images:
                product.images = images

            # Configurar SEO
            product.seo_title = title[:70] if len(
                title) > 70 else title  # Límite de 70 caracteres
            product.seo_description = description[:160] if len(
                description) > 160 else description  # Límite de 160 caracteres

            # Guardar el producto
            print(f"📦 CREANDO PRODUCTO: {title}")
            print(f"   💰 Precio: {price}€")
            print(f"   📊 Stock: {inventory_quantity}")
            print(f"   🏷️  SKU: {sku}")
            print(f"   🏭 Marca: {vendor}")
            print(f"   📸 Imágenes: {len(image_urls)}")

            if product.save():
                product_url = self.get_product_url(product)
                print(f"✅ PRODUCTO CREADO EXITOSAMENTE!")
                print(f"   🆔 ID: {product.id}")
                print(f"   🔗 URL: {product_url}")
                print(f"   📋 Handle: {getattr(product, 'handle', 'N/A')}")                # Actualizar inventario después de crear el producto
                try:
                    if product.variants and len(product.variants) > 0:
                        variant_id = product.variants[0].id
                        inventory_item_id = product.variants[0].inventory_item_id
                        print(f"🔍 ACTUALIZANDO INVENTARIO para variante {variant_id} (item: {inventory_item_id})")
                        
                        # Usar la ubicación ID conocida (79869018376 - ubicación principal de la tienda)
                        location_id = 79869018376
                        print(f"🏪 Usando ubicación Shopify ID: {location_id}")
                        
                        # Método 1: Usar InventoryLevel.set() directamente con la ubicación conocida
                        try:
                            from shopify import InventoryLevel
                            
                            print(f"🔄 Estableciendo inventario (timeout: 10s)...")
                            # Establecer el inventario directamente en la ubicación específica
                            InventoryLevel.set(location_id, inventory_item_id, inventory_quantity)
                            print(f"✅ INVENTARIO ESTABLECIDO vía InventoryLevel.set(): {inventory_quantity} unidades en ubicación {location_id}")
                            
                            # Verificar que se estableció correctamente (con timeout más corto)
                            try:
                                print(f"🔍 Verificando inventario...")
                                inventory_levels = InventoryLevel.find(inventory_item_ids=inventory_item_id)
                                if inventory_levels and len(inventory_levels) > 0:
                                    actual_quantity = inventory_levels[0].available
                                    print(f"✅ VERIFICACIÓN: Cantidad actual: {actual_quantity}")
                                else:
                                    print(f"⚠️ No se pudo verificar (pero probablemente se estableció)")
                            except Exception as verify_error:
                                print(f"⚠️ Error verificando (continuando): {str(verify_error)[:100]}...")
                                # No fallar si la verificación falla
                                
                        except Exception as inventory_level_error:
                            error_msg = str(inventory_level_error).lower()
                            if any(keyword in error_msg for keyword in ['timeout', 'timed out', 'connection', '10060', 'read timeout']):
                                print(f"⚠️ Timeout en inventario: {str(inventory_level_error)[:100]}...")
                                print(f"🔄 Continuando sin más intentos para evitar bloqueos...")
                            else:
                                print(f"⚠️ Error con InventoryLevel.set(): {str(inventory_level_error)[:100]}...")
                                print(f"🔄 Intentando método alternativo...")
                            
                            # Método 2: Solo si no es timeout, intentar adjust()
                            if not any(keyword in error_msg for keyword in ['timeout', 'timed out', 'connection', '10060']):
                                try:
                                    print(f"🔄 Método alternativo: adjust()...")
                                    # ...existing code...
                                    inventory_levels = InventoryLevel.find(inventory_item_ids=inventory_item_id)
                                    if inventory_levels and len(inventory_levels) > 0:
                                        current_quantity = inventory_levels[0].available or 0
                                        adjustment_needed = inventory_quantity - current_quantity
                                        
                                        if adjustment_needed != 0:
                                            InventoryLevel.adjust(location_id, inventory_item_id, adjustment_needed)
                                            print(f"✅ INVENTARIO AJUSTADO: {adjustment_needed} unidades (de {current_quantity} a {inventory_quantity})")
                                        else:
                                            print(f"ℹ️ No se necesita ajuste (ya es {inventory_quantity})")
                                    else:
                                        print(f"⚠️ No se encontraron niveles para ajustar")
                                        
                                except Exception as adjust_error:
                                    print(f"⚠️ Error con adjust(): {str(adjust_error)[:100]}...")
                                    print(f"⚠️ Saltando configuración de inventario para evitar más timeouts...")
                            else:
                                print(f"⚠️ Saltando métodos adicionales debido a timeout")
                        
                except Exception as inventory_error:
                    print(f"⚠️ Error configurando inventario: {inventory_error}")
                    logger.warning(f"Error configurando inventario para producto {title}: {inventory_error}")

                # Configurar categoría después de crear el producto
                try:
                    print(f"🏷️ CONFIGURANDO CATEGORÍA: Toys & Games...")
                    category_success = self.set_product_category(product.id)
                    if category_success:
                        print(f"✅ Categoría configurada correctamente")
                    else:
                        print(f"⚠️ No se pudo configurar la categoría (continuando)")
                except Exception as category_error:
                    print(f"⚠️ Error configurando categoría: {str(category_error)[:100]}...")
                    logger.warning(f"Error configurando categoría para producto {title}: {category_error}")

                # Agregar metafields después de crear el producto (con manejo de timeouts)
                print(f"🏷️ Agregando {len(metafields)} metafields...")
                for i, metafield_data in enumerate(metafields):
                    try:
                        print(f"🔄 Metafield {i+1}/{len(metafields)}: {metafield_data['key']}")
                        metafield = shopify.Metafield()
                        metafield.namespace = metafield_data['namespace']
                        metafield.key = metafield_data['key']
                        metafield.value = metafield_data['value']
                        metafield.type = metafield_data['type']
                        product.add_metafield(metafield)
                        print(f"✅ Metafield {metafield_data['key']} agregado")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if any(keyword in error_msg for keyword in ['timeout', 'timed out', 'connection', '10060']):
                            print(f"⚠️ Timeout en metafield {metafield_data['key']}: {str(e)[:100]}...")
                            print(f"🔄 Continuando con siguiente metafield...")
                        else:
                            print(f"⚠️ Error metafield {metafield_data['key']}: {str(e)[:100]}...")
                        logger.warning(f"Error agregando metafield {metafield_data['key']}: {e}")
                        # ...existing code...
                logger.info(
                    f"Producto creado exitosamente: {title} (ID: {product.id}) - URL: {product_url}")
                print("-" * 80)
                return product
            else:
                print(f"❌ ERROR CREANDO PRODUCTO: {title}")
                print(f"   🚫 Errores: {product.errors}")
                logger.error(
                    f"Error creando producto {title}: {product.errors}")
                print("-" * 80)
                return None

        except Exception as e:
            print(
                f"❌ ERROR PROCESANDO PRODUCTO: {row.get('nombre', 'Sin nombre')}")
            print(f"   🚫 Error: {e}")
            logger.error(
                f"Error procesando producto {row.get('nombre', 'Sin nombre')}: {e}")
            print("-" * 80)
            return None

    def import_products(self, df, start_index=0, limit=None):
        """Importa productos a Shopify"""
        if limit:
            df = df.iloc[start_index:start_index + limit]
        else:
            df = df.iloc[start_index:]

        successful_imports = 0
        failed_imports = 0
        skipped_imports = 0

        print(f"\n🚀 INICIANDO IMPORTACIÓN DE {len(df)} PRODUCTOS")
        print("=" * 80)
        logger.info(f"Iniciando importación de {len(df)} productos...")

        for index, row in df.iterrows():
            try:
                # Solo importar productos con stock o información válida
                if pd.notna(row['nombre']) and str(row['nombre']).strip():
                    print(f"\n📦 PROCESANDO PRODUCTO {index + 1}/{len(df)}")

                    product = self.create_shopify_product(row)
                    if product:
                        successful_imports += 1
                    elif product is None and hasattr(self, '_last_product_existed'):
                        # Si el producto ya existía
                        skipped_imports += 1
                        delattr(self, '_last_product_existed')
                    elif product is None:
                        # Producto saltado por falta de stock u otros motivos
                        skipped_imports += 1
                    else:
                        failed_imports += 1

                    # Delay entre requests para evitar rate limiting
                    time.sleep(self.delay_between_requests)

                # Log de progreso cada 10 productos
                if (index + 1) % 10 == 0:
                    print(
                        f"\n📊 PROGRESO: {index + 1}/{len(df)} productos procesados")
                    print(f"   ✅ Exitosos: {successful_imports}")
                    print(f"   ❌ Fallidos: {failed_imports}")
                    print(f"   ⚠️  Saltados: {skipped_imports}")
                    print("-" * 50)
                    logger.info(
                        f"Procesados {index + 1} productos. Exitosos: {successful_imports}, Fallidos: {failed_imports}, Saltados: {skipped_imports}")

            except Exception as e:
                print(f"❌ ERROR EN FILA {index}: {e}")
                logger.error(f"Error procesando fila {index}: {e}")
                failed_imports += 1

        # Resumen final
        print(f"\n🎯 IMPORTACIÓN COMPLETADA")
        print("=" * 80)
        print(f"✅ Productos creados exitosamente: {successful_imports}")
        print(f"❌ Productos que fallaron: {failed_imports}")
        print(f"⚠️  Productos saltados: {skipped_imports}")
        print(
            f"📊 Total procesado: {successful_imports + failed_imports + skipped_imports}")
        print("=" * 80)

        logger.info(
            f"Importación completada. Exitosos: {successful_imports}, Fallidos: {failed_imports}, Saltados: {skipped_imports}")
        return successful_imports, failed_imports

    def run(self, limit=None):
        """Ejecuta el proceso completo de importación"""
        try:
            # Verificar configuración
            if not all([self.shop_name, self.access_token, self.csv_url]):
                raise ValueError(
                    "Faltan variables de entorno requeridas. Revisa el archivo .env")

            # Descargar CSV
            csv_filename = self.download_csv()

            # Parsear CSV
            df = self.parse_csv(csv_filename)

            # Filtrar productos válidos
            df = df[df['nombre'].notna() & (df['nombre'] != '')]
            logger.info(f"Productos válidos encontrados: {len(df)}")

            # Importar productos
            if limit:
                logger.info(f"Importando los primeros {limit} productos...")
                successful, failed = self.import_products(df, limit=limit)
            else:
                successful, failed = self.import_products(df)

            logger.info(
                f"Proceso completado. Productos importados: {successful}, Fallos: {failed}")

        except Exception as e:
            logger.error(f"Error en el proceso de importación: {e}")
            raise

    @retry_on_timeout(max_retries=2, timeout_delay=1)
    def product_exists(self, title):
        """Verifica si un producto con el mismo título ya existe en Shopify"""
        try:
            # Buscar productos con el mismo título
            existing_products = shopify.Product.find(title=title, limit=1)
            return len(existing_products) > 0
        except Exception as e:
            logger.warning(
                f"Error verificando producto existente '{title}': {e}")
            return False

    def get_product_url(self, product):
        """Genera la URL del producto en la tienda"""
        try:
            if hasattr(product, 'handle') and product.handle:
                return f"https://{self.shop_name}/products/{product.handle}"
            elif hasattr(product, 'id') and product.id:
                return f"https://{self.shop_name}/admin/products/{product.id}"
            else:
                return f"https://{self.shop_name}/admin/products"
        except Exception:
            return f"https://{self.shop_name}/admin/products"

    def create_rich_description(self, row, dimensions=None):
        """Crea una descripción HTML rica para el producto"""
        description = str(row['descripcion']) if pd.notna(
            row['descripcion']) else ''

        # Comenzar con la descripción básica
        html_parts = []

        if description:
            html_parts.append(f"<p>{description}</p>")

        # Agregar información técnica
        tech_info = []

        if dimensions:
            tech_info.append(
                f"<li><strong>Dimensiones:</strong> {dimensions}</li>")

        if pd.notna(row.get('marca')):
            tech_info.append(
                f"<li><strong>Marca:</strong> {row['marca']}</li>")

        if pd.notna(row.get('referencia')):
            tech_info.append(
                f"<li><strong>Referencia:</strong> {row['referencia']}</li>")

        # Agregar información de entrega si está disponible
        if pd.notna(row.get('plazo_de_entrega')):
            tech_info.append(
                f"<li><strong>Plazo de entrega:</strong> {row['plazo_de_entrega']}</li>")

        # Agregar información de stock
        stock = row.get('stock_disponible', 0)
        if pd.notna(stock) and str(stock).isdigit() and int(stock) > 0:
            tech_info.append(
                f"<li><strong>Stock disponible:</strong> {stock} unidades</li>")

        if tech_info:
            html_parts.append("<h3>Información técnica:</h3>")
            html_parts.append("<ul>")
            html_parts.extend(tech_info)
            html_parts.append("</ul>")

        return "".join(html_parts) if html_parts else description

    def update_inventory_level(self, variant_id, inventory_quantity):
        """Actualiza el nivel de inventario usando la API de InventoryLevel"""
        try:
            # Obtener la información del inventario
            inventory_levels = shopify.InventoryLevel.find(inventory_item_ids=variant_id)
            
            if inventory_levels:
                for level in inventory_levels:
                    # Actualizar el nivel de inventario
                    level.set(level.location_id, inventory_quantity)
                    print(f"✅ INVENTARIO ACTUALIZADO vía InventoryLevel: {inventory_quantity} unidades")
                    return True
            else:
                print(f"⚠️ No se encontraron niveles de inventario para la variante {variant_id}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error actualizando inventario vía InventoryLevel: {e}")
            logger.warning(f"Error actualizando inventario vía InventoryLevel: {e}")
            return False    @retry_on_timeout(max_retries=2, timeout_delay=1)
    def set_product_category(self, product_id, category_name="Toys & Games"):
        """Configura la categoría de un producto usando GraphQL - Método simplificado"""
        try:
            import requests
            import json
            
            print(f"🏷️ Configurando categoría '{category_name}' para producto {product_id}...")
            
            # URL de GraphQL
            graphql_url = f"https://{self.shop_name}/admin/api/{self.api_version}/graphql.json"
            
            # Headers
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.access_token
            }
            
            # Método alternativo: actualizar usando REST API
            try:
                print(f"🔄 Usando REST API para establecer categoría...")
                
                # URL REST para actualizar producto
                rest_url = f"https://{self.shop_name}/admin/api/{self.api_version}/products/{product_id}.json"
                
                # Payload para REST API
                rest_payload = {
                    "product": {
                        "id": product_id,
                        "product_category": {
                            "product_taxonomy_node_id": "gid://shopify/TaxonomyValue/toys_and_games"
                        }
                    }
                }
                
                rest_headers = {
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": self.access_token
                }
                
                response = requests.put(rest_url, headers=rest_headers, json=rest_payload, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    product_data = result.get('product', {})
                    
                    print(f"✅ Producto actualizado vía REST API")
                    
                    # Verificar si tiene categoría
                    product_category = product_data.get('product_category')
                    if product_category:
                        print(f"✅ Categoría establecida: {product_category}")
                        return True
                    else:
                        print(f"⚠️ Categoría no visible en respuesta, pero actualización exitosa")
                        return True
                        
                else:
                    print(f"⚠️ REST API response {response.status_code}: {response.text[:200]}...")
                    
            except Exception as rest_error:
                print(f"⚠️ Error con REST API: {str(rest_error)[:100]}...")
            
            # Método alternativo: Solo actualizar product_type si es necesario
            try:
                print(f"🔄 Verificando product_type actual...")
                
                # Obtener el producto actual
                get_url = f"https://{self.shop_name}/admin/api/{self.api_version}/products/{product_id}.json"
                get_headers = {
                    "X-Shopify-Access-Token": self.access_token
                }
                
                get_response = requests.get(get_url, headers=get_headers, timeout=10)
                
                if get_response.status_code == 200:
                    current_product = get_response.json().get('product', {})
                    current_type = current_product.get('product_type', '')
                    
                    print(f"📋 Product type actual: '{current_type}'")
                    
                    if current_type != category_name:
                        print(f"🔄 Actualizando product_type de '{current_type}' a '{category_name}'...")
                        
                        update_payload = {
                            "product": {
                                "id": product_id,
                                "product_type": category_name
                            }
                        }
                        
                        update_response = requests.put(get_url, headers=rest_headers, json=update_payload, timeout=10)
                        
                        if update_response.status_code == 200:
                            print(f"✅ Product type actualizado a '{category_name}'")
                            return True
                        else:
                            print(f"⚠️ Error actualizando product_type: {update_response.status_code}")
                    else:
                        print(f"✅ Product type ya es '{category_name}'")
                        return True
                else:
                    print(f"⚠️ Error obteniendo producto actual: {get_response.status_code}")
                    
            except Exception as type_error:
                print(f"⚠️ Error actualizando product_type: {str(type_error)[:100]}...")
            
            return False
                
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['timeout', 'timed out', 'connection', '10060']):
                print(f"⚠️ Timeout configurando categoría: {str(e)[:100]}...")
            else:
                print(f"⚠️ Error configurando categoría: {str(e)[:100]}...")
            return False

def main():
    """Función principal"""
    print("=== Importador CSV a Shopify ===")
    print("1. Importar todos los productos")
    print("2. Importar solo los primeros 10 productos (prueba)")
    print("3. Importar cantidad personalizada")

    choice = input("Selecciona una opción (1-3): ").strip()

    importer = CSVToShopifyImporter()

    try:
        if choice == "1":
            importer.run()
        elif choice == "2":
            importer.run(limit=10)
        elif choice == "3":
            limit = int(input("¿Cuántos productos quieres importar? "))
            importer.run(limit=limit)
        else:
            print("Opción no válida")
            return

    except Exception as e:
        logger.error(f"Error ejecutando el importador: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
