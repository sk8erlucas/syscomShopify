#!/usr/bin/env python3
"""
Script de prueba final: inventario + categoría + timeouts
"""
import os
import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def main():
    """Función principal"""
    print("🚀 PRUEBA FINAL: Importador completo mejorado")
    print("=" * 60)

    # Importar el importador
    from csv_to_shopify import CSVToShopifyImporter
    
    try:
        # Leer solo las primeras 2 filas del CSV para prueba rápida
        csv_file = "productos_ociostock.csv"
        if not os.path.exists(csv_file):
            print(f"❌ No se encuentra el archivo {csv_file}")
            return
        
        df = pd.read_csv(csv_file, sep=';', encoding='utf-8', nrows=10)
        print(f"📊 Leyendo {len(df)} productos del CSV...")
        
        # Filtrar productos con stock que no existan
        df_with_stock = df[df['hay_stock'] == 1]
        print(f"📦 Productos con stock: {len(df_with_stock)}")
        
        if len(df_with_stock) == 0:
            print("⚠️ No hay productos con stock en la muestra")
            return
        
        # Crear importador
        importer = CSVToShopifyImporter()
        
        # Procesar solo 1 producto para prueba
        print(f"\n🎯 PROCESANDO 1 PRODUCTO DE PRUEBA...")
        
        processed = 0
        for index, row in df_with_stock.iterrows():
            if processed >= 1:  # Solo 1 producto
                break
                
            product_name = row['nombre']
            print(f"\n📦 PRODUCTO: {product_name}")
            
            # Verificar si ya existe
            if importer.product_exists(product_name):
                print(f"⚠️ Producto ya existe, saltando...")
                continue
            
            print(f"✅ Producto no existe, creando...")
            
            # Crear producto
            result = importer.create_shopify_product(row)
            
            if result:
                print(f"🎉 ¡PRODUCTO CREADO EXITOSAMENTE!")
                print(f"   🆔 ID: {result.id}")
                print(f"   🔗 URL: https://{importer.shop_name}/products/{result.handle}")
                processed += 1
            else:
                print(f"❌ Error creando producto")
            
            break  # Solo 1 producto para la prueba
        
        if processed == 0:
            print(f"⚠️ No se procesó ningún producto nuevo")
        else:
            print(f"\n✅ Prueba completada exitosamente: {processed} producto(s) procesado(s)")
            
    except Exception as e:
        print(f"❌ Error general: {e}")
    
    print("\n" + "=" * 60)
    print("🚀 PRUEBA FINAL COMPLETADA")

if __name__ == "__main__":
    main()
