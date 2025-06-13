import os
import shopify
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_shopify_connection():
    """Verifica la conexión con Shopify"""
    shop_name = os.getenv('SHOPIFY_SHOP_NAME')
    access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    
    if not shop_name or not access_token:
        print("❌ Error: Faltan credenciales de Shopify en el archivo .env")
        print("Asegúrate de configurar:")
        print("- SHOPIFY_SHOP_NAME=tu-tienda.myshopify.com")
        print("- SHOPIFY_ACCESS_TOKEN=tu_access_token")
        return False
    
    try:
        # Configurar Shopify
        shopify.ShopifyResource.set_site(f"https://{access_token}@{shop_name}")
        
        # Probar la conexión obteniendo información de la tienda
        shop = shopify.Shop.current()
        
        print("✅ Conexión exitosa con Shopify!")
        print(f"Tienda: {shop.name}")
        print(f"Dominio: {shop.domain}")
        print(f"Email: {shop.email}")
        print(f"Moneda: {shop.currency}")
        
        # Contar productos existentes
        products_count = shopify.Product.count()
        print(f"Productos existentes: {products_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error conectando con Shopify: {e}")
        print("\nPosibles causas:")
        print("1. Credenciales incorrectas")
        print("2. Token de acceso expirado")
        print("3. Permisos insuficientes")
        print("4. Nombre de tienda incorrecto")
        return False

if __name__ == "__main__":
    print("=== Verificación de Conexión Shopify ===")
    test_shopify_connection()
