#!/usr/bin/env python3
"""
Script para investigar categorías de productos disponibles
"""
import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def main():
    """Función principal"""
    print("🔍 INVESTIGANDO CATEGORÍAS DE SHOPIFY")
    print("=" * 60)

    shop_name = os.getenv('SHOPIFY_SHOP_NAME')
    access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    api_version = '2025-04'
    
    graphql_url = f"https://{shop_name}/admin/api/{api_version}/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    
    try:
        # Query para obtener categorías de productos disponibles
        query = """
        query {
          productTaxonomyNode(id: "gid://shopify/TaxonomyCategory/tg-5") {
            id
            name
            fullName
            isLeaf
            isRoot
            attributes {
              id
              name
            }
          }
        }
        """
        
        payload = {"query": query}
        
        print("🔍 Verificando categoría tg-5...")
        response = requests.post(graphql_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 Respuesta: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            
        # Intentar obtener algunas categorías de juguetes
        print(f"\n🔍 Buscando categorías de Toys...")
        
        query2 = """
        query {
          productTaxonomyNodes(first: 20, query: "toys") {
            edges {
              node {
                id
                name
                fullName
                isLeaf
                isRoot
              }
            }
          }
        }
        """
        
        payload2 = {"query": query2}
        response2 = requests.post(graphql_url, headers=headers, json=payload2, timeout=10)
        
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"📋 Categorías de Toys encontradas:")
            
            nodes = result2.get('data', {}).get('productTaxonomyNodes', {}).get('edges', [])
            for edge in nodes:
                node = edge.get('node', {})
                print(f"   🏷️ ID: {node.get('id')}")
                print(f"      Nombre: {node.get('name')}")
                print(f"      Nombre completo: {node.get('fullName')}")
                print(f"      Es hoja: {node.get('isLeaf')}")
                print("")
        else:
            print(f"❌ Error HTTP {response2.status_code}: {response2.text}")
            
        # Intentar con una categoría más específica
        print(f"\n🔍 Buscando categorías más específicas...")
        
        query3 = """
        query {
          productTaxonomyNodes(first: 50) {
            edges {
              node {
                id
                name
                fullName
                isLeaf
                isRoot
              }
            }
          }
        }
        """
        
        payload3 = {"query": query3}
        response3 = requests.post(graphql_url, headers=headers, json=payload3, timeout=10)
        
        if response3.status_code == 200:
            result3 = response3.json()
            print(f"📋 Primeras categorías disponibles:")
            
            nodes = result3.get('data', {}).get('productTaxonomyNodes', {}).get('edges', [])
            for i, edge in enumerate(nodes[:10]):  # Solo las primeras 10
                node = edge.get('node', {})
                print(f"   {i+1}. 🏷️ ID: {node.get('id')}")
                print(f"       Nombre: {node.get('name')}")
                print(f"       Nombre completo: {node.get('fullName')}")
                if 'toy' in node.get('name', '').lower() or 'game' in node.get('name', '').lower():
                    print(f"       ⭐ ¡POSIBLE COINCIDENCIA!")
                print("")
        else:
            print(f"❌ Error HTTP {response3.status_code}: {response3.text}")
            
    except Exception as e:
        print(f"❌ Error general: {e}")
    
    print("=" * 60)
    print("🔍 INVESTIGACIÓN COMPLETADA")

if __name__ == "__main__":
    main()
