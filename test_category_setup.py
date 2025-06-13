#!/usr/bin/env python3
"""
Script de prueba para verificar configuración de categoría
"""
import os
import pandas as pd
import shopify
from dotenv import load_dotenv
import time

# Cargar variables de entorno
load_dotenv()

def main():
    """Función principal"""
    print("🧪 PRUEBA: Configuración de categoría con GraphQL")
    print("=" * 60)

    # Configurar Shopify
    shop_name = os.getenv('SHOPIFY_SHOP_NAME')
    access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    api_version = '2025-04'
    
    shop_url = f"https://{shop_name}/admin/api/{api_version}"
    session = shopify.Session(shop_url, api_version, access_token)
    shopify.ShopifyResource.activate_session(session)
    
    try:
        # Crear un producto de prueba simple
        product = shopify.Product()
        product.title = f"PRUEBA CATEGORIA - {pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        product.body_html = "<p>Producto de prueba para verificar configuración de categoría</p>"
        product.vendor = "Prueba"
        product.product_type = "Toys & Games"
        product.tags = ["Figuras de acción", "Prueba"]
        
        # Crear variante
        variant = shopify.Variant()
        variant.price = 9.99
        variant.sku = f"TEST-CAT-{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
        variant.inventory_management = 'shopify'
        variant.inventory_policy = 'deny'
        
        product.variants = [variant]
        
        print(f"📦 Creando producto de prueba: {product.title}")
        
        if product.save():
            print(f"✅ Producto creado exitosamente!")
            print(f"   🆔 ID: {product.id}")
            
            # Ahora probar la configuración de categoría
            from csv_to_shopify import CSVToShopifyImporter
            
            importer = CSVToShopifyImporter()
            
            print(f"\n🏷️ CONFIGURANDO CATEGORÍA...")
            category_success = importer.set_product_category(product.id)
            
            if category_success:
                print(f"✅ ¡Categoría configurada exitosamente!")
            else:
                print(f"❌ Error configurando categoría")
            
            # Verificar la categoría usando GraphQL
            print(f"\n🔍 VERIFICANDO CATEGORÍA ESTABLECIDA...")
            try:
                import requests
                import json
                
                graphql_url = f"https://{shop_name}/admin/api/{api_version}/graphql.json"
                headers = {
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": access_token
                }
                
                query = """
                query getProduct($id: ID!) {
                  product(id: $id) {
                    id
                    title
                    category {
                      id
                      name
                    }
                    productType
                  }
                }
                """
                
                variables = {
                    "id": f"gid://shopify/Product/{product.id}"
                }
                
                payload = {
                    "query": query,
                    "variables": variables
                }
                
                response = requests.post(graphql_url, headers=headers, json=payload, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    product_data = result.get('data', {}).get('product', {})
                    
                    if product_data:
                        print(f"📋 INFORMACIÓN DEL PRODUCTO:")
                        print(f"   🆔 ID: {product_data.get('id')}")
                        print(f"   📝 Título: {product_data.get('title')}")
                        print(f"   🏷️ Tipo: {product_data.get('productType')}")
                        
                        category = product_data.get('category')
                        if category:
                            print(f"   📂 Categoría ID: {category.get('id')}")
                            print(f"   📂 Categoría Nombre: {category.get('name')}")
                            print(f"✅ ¡CATEGORÍA VERIFICADA CORRECTAMENTE!")
                        else:
                            print(f"   📂 Categoría: No asignada")
                            print(f"⚠️ La categoría no se estableció correctamente")
                    else:
                        print(f"⚠️ No se pudo obtener información del producto")
                else:
                    print(f"❌ Error verificando: {response.status_code}")
                    
            except Exception as verify_error:
                print(f"⚠️ Error verificando categoría: {verify_error}")
            
            # URL del producto
            product_url = f"https://{shop_name}/products/{product.handle}" if hasattr(product, 'handle') else f"https://{shop_name}/admin/products/{product.id}"
            print(f"\n🔗 URL del producto: {product_url}")
            
        else:
            print(f"❌ Error creando producto: {product.errors}")
            
    except Exception as e:
        print(f"❌ Error general: {e}")
    
    print("\n" + "=" * 60)
    print("🧪 PRUEBA COMPLETADA")

if __name__ == "__main__":
    main()
