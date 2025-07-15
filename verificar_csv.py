#!/usr/bin/env python3
"""
Verificador de CSV para Shopify
Diagnóstica archivos CSV y muestra su contenido y estructura
"""

import os
import csv
import logging
from datetime import datetime

def verificar_archivo_csv(archivo_csv: str):
    """Verificar y diagnosticar archivo CSV"""
    print(f"\n🔍 VERIFICANDO: {archivo_csv}")
    print("="*50)
    
    if not os.path.exists(archivo_csv):
        print(f"❌ El archivo {archivo_csv} no existe")
        return
    
    # Información del archivo
    try:
        size = os.path.getsize(archivo_csv)
        timestamp = os.path.getmtime(archivo_csv)
        fecha_mod = datetime.fromtimestamp(timestamp)
        print(f"📁 Tamaño: {size:,} bytes")
        print(f"📅 Última modificación: {fecha_mod.strftime('%d/%m/%Y %H:%M:%S')}")
    except Exception as e:
        print(f"⚠️ Error obteniendo info del archivo: {e}")
    
    # Verificar contenido
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            print(f"\n📋 Probando encoding: {encoding}")
            
            with open(archivo_csv, 'r', encoding=encoding, newline='') as f:
                # Leer primeras líneas para diagnóstico
                primeras_lineas = []
                for i, linea in enumerate(f):
                    primeras_lineas.append(linea.strip())
                    if i >= 5:  # Solo primeras 5 líneas
                        break
                
                # Mostrar contenido inicial
                print(f"📄 Primeras líneas:")
                for i, linea in enumerate(primeras_lineas):
                    print(f"   {i+1}: {linea[:100]}{'...' if len(linea) > 100 else ''}")
                
                # Verificar si es HTML
                primer_contenido = '\n'.join(primeras_lineas)
                if (primer_contenido.startswith('<!DOCTYPE html>') or 
                    primer_contenido.startswith('<html') or
                    '<html' in primer_contenido):
                    print("❌ EL ARCHIVO CONTIENE HTML, NO CSV")
                    print("💡 Esto indica restricción del servidor (1 descarga/hora)")
                    continue
                
                # Resetear archivo y analizar como CSV
                f.seek(0)
                
                # Detectar delimitador
                sample = f.read(1024)
                f.seek(0)
                
                delimiter = ','
                if sample.count(';') > sample.count(','):
                    delimiter = ';'
                elif sample.count('\t') > sample.count(','):
                    delimiter = '\t'
                
                print(f"🔧 Delimitador detectado: '{delimiter}'")
                
                # Leer como CSV
                reader = csv.DictReader(f, delimiter=delimiter)
                
                if reader.fieldnames:
                    columnas = list(reader.fieldnames)
                    print(f"📊 Columnas encontradas ({len(columnas)}):")
                    for i, col in enumerate(columnas):
                        print(f"   {i+1:2d}. {col}")
                    
                    # Verificar tipo de formato
                    campos_shopify = ['Handle', 'Title', 'Variant Price', 'Variant Inventory Qty']
                    campos_alternativos = ['Codigo', 'Nombre', 'Precio', 'Stock', 'Descripcion', 'SKU']
                    
                    es_shopify = any(campo in columnas for campo in campos_shopify)
                    es_convertible = any(campo in columnas for campo in campos_alternativos)
                    
                    if es_shopify:
                        print("✅ FORMATO SHOPIFY DETECTADO")
                    elif es_convertible:
                        print("🔄 FORMATO CONVERTIBLE A SHOPIFY")
                        print("📋 Campos reconocidos:")
                        for campo in campos_alternativos:
                            if campo in columnas:
                                print(f"   ✓ {campo}")
                    else:
                        print("❌ FORMATO NO RECONOCIDO")
                        print("💡 Campos necesarios: Codigo/SKU, Nombre/Title, Precio/Price, Stock/Inventory")
                    
                    # Contar productos
                    productos = list(reader)
                    print(f"📦 Total productos: {len(productos)}")
                    
                    if len(productos) > 0:
                        # Analizar primer producto
                        print(f"\n📋 Ejemplo de producto (primero):")
                        primer_producto = productos[0]
                        for campo, valor in primer_producto.items():
                            valor_mostrar = str(valor)[:50] + '...' if len(str(valor)) > 50 else str(valor)
                            print(f"   {campo}: {valor_mostrar}")
                        
                        # Verificar stock
                        productos_con_stock = 0
                        stock_campos = ['Variant Inventory Qty', 'Inventory Qty', 'Stock', 'Quantity', 'Available']
                        
                        for producto in productos:
                            for campo_stock in stock_campos:
                                if campo_stock in producto:
                                    try:
                                        stock = float(producto[campo_stock])
                                        if stock > 0:
                                            productos_con_stock += 1
                                            break
                                    except:
                                        pass
                        
                        print(f"📊 Productos con stock > 0: {productos_con_stock}")
                        print(f"📊 Productos sin stock: {len(productos) - productos_con_stock}")
                    
                    print(f"✅ ARCHIVO VÁLIDO CON {encoding}")
                    return True
                else:
                    print(f"❌ No se pudieron detectar columnas con {encoding}")
                    
        except Exception as e:
            print(f"❌ Error con {encoding}: {e}")
            continue
    
    print("❌ NO SE PUDO LEER EL ARCHIVO CON NINGÚN ENCODING")
    return False

def main():
    """Función principal de verificación"""
    print("🔍 VERIFICADOR DE CSV PARA SHOPIFY")
    print("="*50)
    
    # Lista de archivos a verificar
    archivos_a_verificar = [
        "ProductosHora.csv",
        "productos_ociostock.csv",
        "productos_shopify.csv",
        "productos.csv",
        "syscom.csv"
    ]
    
    archivos_encontrados = []
    
    for archivo in archivos_a_verificar:
        if os.path.exists(archivo):
            archivos_encontrados.append(archivo)
            verificar_archivo_csv(archivo)
    
    if not archivos_encontrados:
        print("\n❌ NO SE ENCONTRARON ARCHIVOS CSV")
        print("\n💡 SOLUCIÓN:")
        print("   1. Coloca ProductosHora.csv en esta carpeta")
        print("   2. O configura CSV_URL en .env para descarga automática")
        print("   3. El archivo debe contener columnas como:")
        print("      - Codigo/SKU (identificador)")
        print("      - Nombre/Title (nombre del producto)")  
        print("      - Precio/Price (precio)")
        print("      - Stock/Inventory (cantidad disponible)")
    else:
        print(f"\n✅ VERIFICACIÓN COMPLETADA")
        print(f"📁 Archivos encontrados: {len(archivos_encontrados)}")

if __name__ == "__main__":
    main()
