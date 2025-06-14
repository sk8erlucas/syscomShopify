#!/usr/bin/env python3
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
