#!/usr/bin/env python3
"""
CSV Splitter para Shopify - v1.0
Descarga CSV grande y lo divide en archivos pequeños de 2000 líneas
Cada archivo está listo para importar a Shopify
"""

import os
import csv
import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('csv_splitter_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Cargar variables de entorno
load_dotenv()

class CSVSplitterShopify:
    def __init__(self):
        """Inicializar el divisor de CSV"""
        self.csv_url = os.getenv('CSV_URL')
        self.lineas_por_archivo = 2000
        self.directorio_salida = "csv_shopify_split"
        
        # Configuración de descarga
        self.timeout = 30
        self.max_retries = 3
        
        # Estadísticas
        self.stats = {
            'lineas_totales': 0,
            'archivos_generados': 0,
            'productos_con_stock': 0,
            'productos_sin_stock': 0,
            'tiempo_inicio': None,
            'tiempo_fin': None
        }
        
        # Crear directorio de salida
        if not os.path.exists(self.directorio_salida):
            os.makedirs(self.directorio_salida)
            logging.info(f"📁 Directorio creado: {self.directorio_salida}")
    
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
    
    def descargar_csv(self) -> Optional[str]:
        """Descargar CSV desde URL o usar archivo local con manejo inteligente de restricciones"""
        # Intentar descarga desde URL
        if self.csv_url:
            for intento in range(self.max_retries):
                try:
                    logging.info(f"🔗 Descargando CSV desde URL (intento {intento + 1})...")
                    
                    session = requests.Session()
                    session.headers.update({
                        'User-Agent': 'CSV-Splitter-Shopify/1.0',
                        'Accept': 'text/csv, application/csv, text/plain, */*'
                    })
                    
                    response = session.get(self.csv_url, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        # Verificar si es realmente CSV y no HTML (error del servidor)
                        content_text = response.text.strip()
                        content_type = response.headers.get('content-type', '').lower()
                        
                        # Detectar si es HTML (restricción del servidor)
                        if (content_text.startswith('<!DOCTYPE html>') or 
                            content_text.startswith('<html') or
                            '<html' in content_text[:100] or
                            'text/html' in content_type):
                            
                            logging.warning(f"⚠️ Servidor devolvió HTML en lugar de CSV (restricción de descarga)")
                            logging.info("📋 Parece que hay límite de 1 descarga por hora")
                            break  # Salir del loop de reintentos
                        
                        # Verificar si es CSV válido
                        elif ('csv' in content_type or 
                              content_text.count(',') > content_text.count(';') and
                              '\n' in content_text and
                              not content_text.startswith('<')):
                            
                            # Es un CSV válido - guardarlo y reemplazar el existente
                            archivo_csv_local = "ProductosHora.csv"
                            
                            # Hacer backup del archivo existente si existe
                            if os.path.exists(archivo_csv_local):
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                backup_name = f"ProductosHora_backup_{timestamp}.csv"
                                try:
                                    import shutil
                                    shutil.copy2(archivo_csv_local, backup_name)
                                    logging.info(f"📁 Backup creado: {backup_name}")
                                except Exception as e:
                                    logging.warning(f"⚠️ No se pudo crear backup: {e}")
                            
                            # Guardar el nuevo CSV
                            with open(archivo_csv_local, 'w', encoding='utf-8', newline='') as f:
                                f.write(content_text)
                            
                            logging.info(f"✅ CSV descargado y actualizado: {archivo_csv_local}")
                            return archivo_csv_local
                        else:
                            logging.warning(f"⚠️ Contenido no parece CSV válido")
                    else:
                        logging.warning(f"⚠️ Error HTTP: {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    logging.warning(f"⏰ Timeout en intento {intento + 1}")
                except Exception as e:
                    logging.warning(f"⚠️ Error en intento {intento + 1}: {e}")
                
                if intento < self.max_retries - 1:
                    import time
                    time.sleep(2 ** intento)  # Backoff exponencial
        
        # Usar archivo local como fallback (orden de prioridad específico)
        archivos_locales = [
            "ProductosHora.csv",  # Prioridad máxima
            "productos_ociostock.csv", 
            "productos_shopify.csv", 
            "productos.csv",
            "syscom.csv"
        ]
        
        for archivo in archivos_locales:
            if os.path.exists(archivo):
                # Verificar que no sea un archivo HTML por error previo
                try:
                    with open(archivo, 'r', encoding='utf-8') as f:
                        primeras_lineas = f.read(200)
                        if (primeras_lineas.strip().startswith('<!DOCTYPE html>') or 
                            primeras_lineas.strip().startswith('<html')):
                            logging.warning(f"⚠️ {archivo} parece contener HTML, saltando...")
                            continue
                except Exception:
                    pass
                
                logging.info(f"📁 Usando archivo local: {archivo}")
                if archivo == "ProductosHora.csv":
                    logging.info("💡 Usando ProductosHora.csv - si necesitas datos actualizados, espera 1 hora para nueva descarga")
                return archivo
                
        logging.error("❌ No se pudo obtener archivo CSV válido")
        return None
    
    def parsear_csv(self, archivo_csv: str) -> List[Dict]:
        """Parsear CSV con manejo robusto de encoding y formatos"""
        productos = []
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(archivo_csv, 'r', encoding=encoding, newline='') as f:
                    # Leer una muestra más grande para detectar formato
                    sample = f.read(2048)
                    f.seek(0)
                    
                    # Verificar que no sea HTML
                    if (sample.strip().startswith('<!DOCTYPE html>') or 
                        sample.strip().startswith('<html') or
                        '<html' in sample[:200]):
                        logging.error(f"❌ El archivo {archivo_csv} contiene HTML en lugar de CSV")
                        continue
                    
                    # Detectar delimitador
                    delimiter = ','
                    if sample.count(';') > sample.count(','):
                        delimiter = ';'
                    elif sample.count('\t') > sample.count(','):
                        delimiter = '\t'
                    
                    # Intentar leer como CSV
                    reader = csv.DictReader(f, delimiter=delimiter)
                    
                    if reader.fieldnames:
                        columnas = list(reader.fieldnames)
                        logging.info(f"📋 Columnas detectadas ({encoding}): {columnas[:5]}...")
                        
                        # Verificar si es formato Shopify válido O formato que podemos convertir
                        campos_shopify = ['Handle', 'Title', 'Variant Price', 'Variant Inventory Qty']
                        campos_alternativos = ['Codigo', 'Nombre', 'Precio', 'Stock', 'Descripcion', 'SKU']
                        
                        es_shopify = any(campo in columnas for campo in campos_shopify)
                        es_convertible = any(campo in columnas for campo in campos_alternativos)
                        
                        if es_shopify:
                            productos = list(reader)
                            logging.info(f"✅ CSV Shopify parseado con {encoding}: {len(productos)} productos")
                            return productos
                        elif es_convertible:
                            logging.info(f"📋 Detectado formato no-Shopify convertible con {encoding}")
                            productos_raw = list(reader)
                            productos = self.convertir_a_formato_shopify(productos_raw, columnas)
                            logging.info(f"✅ CSV convertido a Shopify con {encoding}: {len(productos)} productos")
                            return productos
                        else:
                            logging.warning(f"⚠️ Formato no reconocido con {encoding}")
                            logging.info(f"📋 Columnas disponibles: {', '.join(columnas)}")
                            
            except Exception as e:
                logging.debug(f"Error con encoding {encoding}: {e}")
                continue
                
        logging.error("❌ No se pudo parsear el CSV con ningún encoding")
        return []
    
    def convertir_a_formato_shopify(self, productos_raw: List[Dict], columnas: List[str]) -> List[Dict]:
        """Convertir CSV de formato personalizado a formato Shopify"""
        productos_shopify = []
        
        # Mapeo de campos comunes
        mapeo_campos = {
            # Campos principales
            'Codigo': 'Variant SKU',
            'SKU': 'Variant SKU', 
            'Nombre': 'Title',
            'Titulo': 'Title',
            'Title': 'Title',
            'Descripcion': 'Body (HTML)',
            'Description': 'Body (HTML)',
            'Precio': 'Variant Price',
            'Price': 'Variant Price',
            'Stock': 'Variant Inventory Qty',
            'Inventory': 'Variant Inventory Qty',
            'Cantidad': 'Variant Inventory Qty',
            'Marca': 'Vendor',
            'Brand': 'Vendor',
            'Categoria': 'Product Category',
            'Category': 'Product Category',
            'Imagen': 'Image Src',
            'Image': 'Image Src',
            'URL_Imagen': 'Image Src',
        }
        
        logging.info("🔄 Convirtiendo formato personalizado a Shopify...")
        
        for i, producto_raw in enumerate(productos_raw):
            producto_shopify = {}
            
            # Aplicar mapeo de campos
            for campo_original, campo_shopify in mapeo_campos.items():
                if campo_original in producto_raw and producto_raw[campo_original]:
                    valor = str(producto_raw[campo_original]).strip()
                    if valor:
                        producto_shopify[campo_shopify] = valor
            
            # Generar campos obligatorios si no existen
            if 'Title' not in producto_shopify:
                # Buscar cualquier campo que pueda ser título
                for campo in ['Nombre', 'Titulo', 'Descripcion', 'Description']:
                    if campo in producto_raw and producto_raw[campo]:
                        producto_shopify['Title'] = str(producto_raw[campo])[:100]
                        break
                else:
                    producto_shopify['Title'] = f"Producto {i+1}"
            
            # Generar Handle desde título
            if 'Title' in producto_shopify:
                titulo = producto_shopify['Title']
                handle = re.sub(r'[^a-z0-9\s-]', '', titulo.lower())
                handle = re.sub(r'\s+', '-', handle).strip('-')
                producto_shopify['Handle'] = handle[:100]
            
            # Campos por defecto requeridos por Shopify
            if 'Variant Inventory Tracker' not in producto_shopify:
                producto_shopify['Variant Inventory Tracker'] = 'shopify'
            if 'Variant Inventory Policy' not in producto_shopify:
                producto_shopify['Variant Inventory Policy'] = 'deny'
            if 'Variant Fulfillment Service' not in producto_shopify:
                producto_shopify['Variant Fulfillment Service'] = 'manual'
            if 'Variant Requires Shipping' not in producto_shopify:
                producto_shopify['Variant Requires Shipping'] = 'TRUE'
            if 'Variant Taxable' not in producto_shopify:
                producto_shopify['Variant Taxable'] = 'TRUE'
            if 'Status' not in producto_shopify:
                producto_shopify['Status'] = 'active'
            
            productos_shopify.append(producto_shopify)
        
        return productos_shopify
    
    def filtrar_productos_con_stock(self, productos: List[Dict]) -> List[Dict]:
        """Filtrar productos que tienen stock disponible"""
        productos_filtrados = []
        productos_sin_stock = 0
        
        for producto in productos:
            try:
                # Intentar diferentes nombres de columna para stock
                stock_campos = [
                    'Variant Inventory Qty',
                    'Inventory Qty',
                    'Stock',
                    'Quantity',
                    'Available'
                ]
                
                stock = 0
                for campo in stock_campos:
                    if campo in producto and producto[campo]:
                        try:
                            stock = float(producto[campo])
                            break
                        except (ValueError, TypeError):
                            continue
                
                if stock > 0:
                    productos_filtrados.append(producto)
                    self.stats['productos_con_stock'] += 1
                else:
                    productos_sin_stock += 1
                    self.stats['productos_sin_stock'] += 1
                    
            except Exception as e:
                logging.debug(f"Error procesando stock: {e}")
                productos_sin_stock += 1
                self.stats['productos_sin_stock'] += 1
        
        logging.info(f"📦 Productos filtrados - Con stock: {len(productos_filtrados)}, Sin stock: {productos_sin_stock}")
        return productos_filtrados
    
    def limpiar_producto_para_shopify(self, producto: Dict) -> Dict:
        """Limpiar y optimizar datos del producto para Shopify"""
        producto_limpio = {}
        
        # Mapeo de campos
        mapeo_campos = {
            'Handle': 'Handle',
            'Title': 'Title',
            'Body (HTML)': 'Body (HTML)',
            'Vendor': 'Vendor',
            'Product Category': 'Product Category',
            'Type': 'Type',
            'Tags': 'Tags',
            'Option1 Name': 'Option1 Name',
            'Option1 Value': 'Option1 Value',
            'Variant SKU': 'Variant SKU',
            'Variant Grams': 'Variant Grams',
            'Variant Inventory Tracker': 'Variant Inventory Tracker',
            'Variant Inventory Qty': 'Variant Inventory Qty',
            'Variant Inventory Policy': 'Variant Inventory Policy',
            'Variant Fulfillment Service': 'Variant Fulfillment Service',
            'Variant Price': 'Variant Price',
            'Variant Compare At Price': 'Variant Compare At Price',
            'Variant Requires Shipping': 'Variant Requires Shipping',
            'Variant Taxable': 'Variant Taxable',
            'Variant Barcode': 'Variant Barcode',
            'Image Src': 'Image Src',
            'Image Position': 'Image Position',
            'Image Alt Text': 'Image Alt Text',
            'Gift Card': 'Gift Card',
            'SEO Title': 'SEO Title',
            'SEO Description': 'SEO Description',
            'Google Shopping / Google Product Category': 'Google Shopping / Google Product Category',
            'Google Shopping / Gender': 'Google Shopping / Gender',
            'Google Shopping / Age Group': 'Google Shopping / Age Group',
            'Google Shopping / MPN': 'Google Shopping / MPN',
            'Google Shopping / AdWords Grouping': 'Google Shopping / AdWords Grouping',
            'Google Shopping / AdWords Labels': 'Google Shopping / AdWords Labels',
            'Google Shopping / Condition': 'Google Shopping / Condition',
            'Google Shopping / Custom Product': 'Google Shopping / Custom Product',
            'Google Shopping / Custom Label 0': 'Google Shopping / Custom Label 0',
            'Google Shopping / Custom Label 1': 'Google Shopping / Custom Label 1',
            'Google Shopping / Custom Label 2': 'Google Shopping / Custom Label 2',
            'Google Shopping / Custom Label 3': 'Google Shopping / Custom Label 3',
            'Google Shopping / Custom Label 4': 'Google Shopping / Custom Label 4',
            'Variant Image': 'Variant Image',
            'Variant Weight Unit': 'Variant Weight Unit',
            'Variant Tax Code': 'Variant Tax Code',
            'Cost per item': 'Cost per item',
            'Status': 'Status'
        }
        
        # Copiar campos existentes
        for campo_original, campo_shopify in mapeo_campos.items():
            if campo_original in producto:
                valor = producto[campo_original]
                if valor:  # Solo si tiene valor
                    # Aplicar corrección de encoding
                    if isinstance(valor, str):
                        valor = self.fix_encoding_issues(valor)
                    producto_limpio[campo_shopify] = valor
        
        # Valores por defecto para campos requeridos
        if 'Handle' not in producto_limpio and 'Title' in producto_limpio:
            # Generar handle desde título
            titulo = producto_limpio['Title']
            handle = re.sub(r'[^a-z0-9\s-]', '', titulo.lower())
            handle = re.sub(r'\s+', '-', handle).strip('-')
            producto_limpio['Handle'] = handle[:255]
        
        if 'Variant Inventory Tracker' not in producto_limpio:
            producto_limpio['Variant Inventory Tracker'] = 'shopify'
        
        if 'Variant Inventory Policy' not in producto_limpio:
            producto_limpio['Variant Inventory Policy'] = 'deny'
        
        if 'Variant Fulfillment Service' not in producto_limpio:
            producto_limpio['Variant Fulfillment Service'] = 'manual'
        
        if 'Variant Requires Shipping' not in producto_limpio:
            producto_limpio['Variant Requires Shipping'] = 'TRUE'
        
        if 'Variant Taxable' not in producto_limpio:
            producto_limpio['Variant Taxable'] = 'TRUE'
        
        if 'Status' not in producto_limpio:
            producto_limpio['Status'] = 'active'
        
        return producto_limpio
    
    def dividir_csv_en_archivos(self, productos: List[Dict]) -> List[str]:
        """Dividir lista de productos en archivos CSV más pequeños"""
        archivos_generados = []
        
        # Obtener encabezados (todos los campos únicos)
        todos_los_campos = set()
        for producto in productos:
            todos_los_campos.update(producto.keys())
        
        # Ordenar campos con Handle y Title primero
        campos_ordenados = []
        campos_prioritarios = ['Handle', 'Title', 'Body (HTML)', 'Vendor', 'Product Category', 'Type', 'Tags']
        
        for campo in campos_prioritarios:
            if campo in todos_los_campos:
                campos_ordenados.append(campo)
                todos_los_campos.remove(campo)
        
        campos_ordenados.extend(sorted(todos_los_campos))
        
        # Dividir en lotes
        total_archivos = (len(productos) + self.lineas_por_archivo - 1) // self.lineas_por_archivo
        
        for i in range(0, len(productos), self.lineas_por_archivo):
            lote = productos[i:i + self.lineas_por_archivo]
            numero_archivo = (i // self.lineas_por_archivo) + 1
            
            nombre_archivo = f"shopify_productos_parte_{numero_archivo:03d}_de_{total_archivos:03d}.csv"
            ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
            
            try:
                with open(ruta_archivo, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=campos_ordenados)
                    writer.writeheader()
                    
                    for producto in lote:
                        producto_limpio = self.limpiar_producto_para_shopify(producto)
                        writer.writerow(producto_limpio)
                
                archivos_generados.append(ruta_archivo)
                self.stats['archivos_generados'] += 1
                
                logging.info(f"✅ Archivo {numero_archivo}/{total_archivos}: {nombre_archivo} ({len(lote)} productos)")
                
            except Exception as e:
                logging.error(f"❌ Error creando archivo {nombre_archivo}: {e}")
        
        return archivos_generados
    
    def crear_archivo_instrucciones(self, archivos_generados: List[str]):
        """Crear archivo con instrucciones de uso"""
        archivo_instrucciones = os.path.join(self.directorio_salida, "INSTRUCCIONES_IMPORTACION.txt")
        
        contenido = f"""
INSTRUCCIONES PARA IMPORTAR A SHOPIFY
====================================

Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Archivos generados: {len(archivos_generados)}
Productos por archivo: {self.lineas_por_archivo}
Total productos: {self.stats['productos_con_stock']:,}

PASOS PARA IMPORTAR:
==================

1. Ve a tu admin de Shopify: https://[tu-tienda].myshopify.com/admin

2. Navega a: Productos > Todos los productos

3. Haz clic en "Importar" (botón en la esquina superior derecha)

4. Selecciona "Subir archivo" y elige el primer archivo:
   {os.path.basename(archivos_generados[0]) if archivos_generados else 'shopify_productos_parte_001_de_XXX.csv'}

5. Configura las opciones de importación:
   - Formato: CSV
   - Separador: Coma (,)
   - Encoding: UTF-8
   - ✅ Marcar "Omitir duplicados" si es reimportación

6. Haz clic en "Subir y continuar"

7. Revisa el mapeo de columnas (debería ser automático)

8. Haz clic en "Importar productos"

9. Espera a que termine la importación (recibirás email)

10. Repite con los siguientes archivos en orden:

ARCHIVOS GENERADOS:
==================
"""
        
        for i, archivo in enumerate(archivos_generados, 1):
            contenido += f"{i:3d}. {os.path.basename(archivo)}\n"
        
        contenido += f"""

NOTAS IMPORTANTES:
=================

• Importa los archivos en ORDEN para mantener consistencia
• Espera que termine cada importación antes de subir el siguiente
• Todos los productos tienen stock > 0
• Los precios están en la moneda configurada en tu tienda
• Las imágenes se cargarán desde las URLs incluidas
• Si hay errores, revisa el email de notificación de Shopify

ESTADÍSTICAS:
============

Productos con stock: {self.stats['productos_con_stock']:,}
Productos sin stock: {self.stats['productos_sin_stock']:,}
Archivos generados: {self.stats['archivos_generados']}
Líneas por archivo: {self.lineas_por_archivo:,}

¡Listo para importar! 🚀
"""
        
        try:
            with open(archivo_instrucciones, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            logging.info(f"📋 Instrucciones creadas: {archivo_instrucciones}")
        except Exception as e:
            logging.error(f"❌ Error creando instrucciones: {e}")
    
    def ejecutar_division(self):
        """Ejecutar el proceso completo de división"""
        print("\n" + "="*60)
        print("📊 CSV SPLITTER PARA SHOPIFY v1.0")
        print("="*60)
        
        self.stats['tiempo_inicio'] = datetime.now()
        print(f"⏰ Inicio: {self.stats['tiempo_inicio'].strftime('%H:%M:%S')}")
        
        # Información sobre limitaciones del servidor
        print(f"\n💡 INFORMACIÓN IMPORTANTE:")
        print(f"   • El servidor tiene límite de 1 descarga por hora")
        print(f"   • Si hay restricción, se usará ProductosHora.csv local")
        print(f"   • Si la descarga es exitosa, se actualizará el archivo local")
        
        # Paso 1: Descargar CSV
        print(f"\n🔽 PASO 1: DESCARGA/LOCALIZACIÓN DE CSV")
        archivo_csv = self.descargar_csv()
        if not archivo_csv:
            print("❌ No se pudo obtener el archivo CSV")
            return
        
        # Mostrar información del archivo utilizado
        if archivo_csv == "ProductosHora.csv":
            try:
                import os
                timestamp = os.path.getmtime(archivo_csv)
                fecha_modificacion = datetime.fromtimestamp(timestamp)
                print(f"📅 Usando ProductosHora.csv (última modificación: {fecha_modificacion.strftime('%d/%m/%Y %H:%M')})")
            except:
                print(f"📁 Usando ProductosHora.csv local")
        
        # Paso 2: Parsear CSV
        print(f"\n📋 PASO 2: PROCESAMIENTO DE CSV")
        productos = self.parsear_csv(archivo_csv)
        if not productos:
            print("❌ No se pudieron parsear los productos")
            print("\n🔍 DIAGNÓSTICO:")
            print("   • Verifica que ProductosHora.csv contenga datos válidos")
            print("   • El archivo no debe ser HTML (error de servidor)")
            print("   • Debe tener columnas como: Codigo, Nombre, Precio, Stock")
            return
        
        self.stats['lineas_totales'] = len(productos)
        print(f"✅ {len(productos):,} productos encontrados")
        
        # Paso 3: Filtrar productos con stock
        print(f"\n📦 PASO 3: FILTRADO POR STOCK")
        productos_con_stock = self.filtrar_productos_con_stock(productos)
        if not productos_con_stock:
            print("❌ No hay productos con stock")
            print("\n🔍 DIAGNÓSTICO:")
            print("   • Verifica que el CSV tenga columna de stock/inventario")
            print("   • Los valores de stock deben ser números > 0")
            return
        
        print(f"✅ {len(productos_con_stock):,} productos con stock > 0")
        
        # Paso 4: Dividir en archivos
        print(f"\n✂️ PASO 4: DIVISIÓN EN ARCHIVOS")
        print(f"📄 Creando archivos de {self.lineas_por_archivo:,} líneas cada uno...")
        
        archivos_generados = self.dividir_csv_en_archivos(productos_con_stock)
        
        if not archivos_generados:
            print("❌ No se pudieron generar archivos")
            return
        
        # Paso 5: Crear instrucciones
        print(f"\n📋 PASO 5: GENERANDO INSTRUCCIONES")
        self.crear_archivo_instrucciones(archivos_generados)
        
        # Estadísticas finales
        self.stats['tiempo_fin'] = datetime.now()
        self.mostrar_estadisticas_finales(archivos_generados)
        
        # Limpiar archivo temporal si fue descargado
        if archivo_csv.startswith("productos_original_"):
            try:
                os.remove(archivo_csv)
                logging.info(f"🧹 Archivo temporal eliminado: {archivo_csv}")
            except:
                pass
    
    def mostrar_estadisticas_finales(self, archivos_generados: List[str]):
        """Mostrar estadísticas finales"""
        print(f"\n{'='*60}")
        print(f"📊 ESTADÍSTICAS FINALES")
        print(f"{'='*60}")
        
        if self.stats['tiempo_inicio'] and self.stats['tiempo_fin']:
            duracion = self.stats['tiempo_fin'] - self.stats['tiempo_inicio']
            print(f"⏰ Duración: {duracion}")
        
        print(f"📋 Productos totales: {self.stats['lineas_totales']:,}")
        print(f"📦 Con stock: {self.stats['productos_con_stock']:,}")
        print(f"❌ Sin stock: {self.stats['productos_sin_stock']:,}")
        print(f"📁 Archivos generados: {self.stats['archivos_generados']}")
        print(f"📄 Líneas por archivo: {self.lineas_por_archivo:,}")
        
        if archivos_generados:
            print(f"\n📂 ARCHIVOS CREADOS EN: {self.directorio_salida}/")
            for i, archivo in enumerate(archivos_generados[:5], 1):  # Mostrar primeros 5
                print(f"   {i}. {os.path.basename(archivo)}")
            
            if len(archivos_generados) > 5:
                print(f"   ... y {len(archivos_generados) - 5} archivos más")
        
        print(f"\n🎉 DIVISIÓN COMPLETADA")
        print(f"📋 Revisa las instrucciones: {self.directorio_salida}/INSTRUCCIONES_IMPORTACION.txt")
        print(f"🚀 ¡Listo para importar a Shopify!")

def main():
    """Función principal"""
    try:
        splitter = CSVSplitterShopify()
        splitter.ejecutar_division()
    except KeyboardInterrupt:
        print("\n👋 División interrumpida por usuario")
    except Exception as e:
        logging.error(f"❌ Error crítico: {e}")
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    main()
