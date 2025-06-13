# SYSCOM to Shopify - Importador de Productos v2.0

Sistema de importación automatizada de productos desde el catálogo de SYSCOM a Shopify, actualizado para la nueva tienda y formato CSV nativo de Shopify.

## ✨ Características

- 🔗 **Conexión moderna**: Utiliza Shopify API 2025-04
- 📦 **Formato nativo**: Lee CSV en formato Shopify directamente
- 🎯 **Filtrado inteligente**: Solo importa productos con stock disponible
- 🚫 **Anti-duplicados**: Evita crear productos existentes
- 📊 **Inventario automático**: Configura stock correctamente
- 🔧 **Manejo de errores**: Robusto sistema de reintentos
- 🌐 **Multi-encoding**: Soporte para diferentes codificaciones de texto

## 🏪 Configuración de Tienda

- **Tienda**: Sepacsye (9s08ym-uc.myshopify.com)
- **Moneda**: MXN (Pesos Mexicanos)
- **Productos**: Catálogo completo de SYSCOM
- **Stock**: Solo productos con inventario disponible

## 📋 Nuevas Columnas CSV (Formato Shopify)

El sistema maneja el formato CSV nativo de Shopify con columnas:

| Columna | Descripción |
|---------|-------------|
| `Handle` | Identificador único del producto |
| `Title` | Nombre del producto |
| `Body (HTML)` | Descripción completa en HTML |
| `Vendor` | Marca/Fabricante |
| `Variant SKU` | Código SKU |
| `Variant Price` | Precio en MXN |
| `Variant Inventory Qty` | Cantidad en stock |
| `Image Src` | URL de imagen principal |
| `Status` | Estado (active/draft) |

## 🚀 Instalación y Configuración

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno
Crear archivo `.env`:
```bash
# Configuración de Shopify
SHOPIFY_SHOP_NAME=9s08ym-uc.myshopify.com
SHOPIFY_ACCESS_TOKEN=tu_access_token

# URL del CSV (nuevo formato)
CSV_URL=http://www.syscom.mx/principal/reporte_art_hora?cadena1=104560616&cadena2=78086a2c10a542b2be92ba11a7d08fba&all=1&set_iva=1&format=shopify&format_shopify=all&tipo_precio=precio_lista&moneda=mxn&incremento=0&sel=22,37,30,26,32,38,27,65811,66523

# Configuraciones opcionales
MAX_PRODUCTS_PER_BATCH=10
DELAY_BETWEEN_REQUESTS=1
```

## 🧪 Ejecutar Tests

### Suite completa de tests
```bash
python run_tests.py
```

### Tests individuales
```bash
# Test de conexión a Shopify
python tests/test_connection.py

# Test de parseo CSV local
python tests/test_local.py
```

## 📦 Importar Productos

### Importación interactiva
```bash
python import_productos.py
```

### Importación programática
```python
from csv_to_shopify_v2 import ShopifyCSVImporter

# Crear importador
importer = ShopifyCSVImporter()

# Importar productos (ejemplo: 50 productos)
importer.import_products(max_products=50)
```

## 🔧 Características Técnicas

### Manejo de Errores
- **Timeouts**: Reintentos automáticos en conexiones lentas
- **Encoding**: Detección automática de codificación (UTF-8, Latin-1, CP1252)
- **Duplicados**: Verificación previa de productos existentes
- **Stock**: Filtrado automático de productos sin inventario

### Configuración de Inventario
- **Tracking**: Seguimiento automático de stock
- **Policy**: Política `deny` (no permitir ventas sin stock)
- **Location**: Configuración automática de ubicación principal

### Limites y Validaciones
- **Precios**: Validación y conversión de formatos de precio
- **HTML**: Limpieza y limitación de tamaño para descripciones
- **Imágenes**: Validación de URLs de imágenes
- **SEO**: Configuración automática de títulos y descripciones

## 📊 Estadísticas del Catálogo

- **Total productos**: ~23,500
- **Con stock**: ~13,200
- **Marcas**: 100+ fabricantes
- **Categorías**: Seguridad, Automatización, Comunicaciones

## 🛡️ Mejores Prácticas

### Antes de Importar
1. Ejecutar `python run_tests.py` para verificar configuración
2. Comenzar con importaciones pequeñas (5-10 productos)
3. Verificar productos creados en Shopify admin
4. Revisar configuración de stock e inventario

### Durante la Importación
- Monitorear la consola para errores
- Evitar interrumpir el proceso en lotes grandes
- Verificar límites de API de Shopify

### Después de Importar
- Revisar productos en Shopify admin
- Verificar configuración de inventario
- Comprobar imágenes y descripciones
- Ajustar categorías si es necesario

## 🔍 Troubleshooting

### Error de Conexión
```
❌ Error conectando con Shopify
```
**Solución**: Verificar credenciales en `.env` y permisos del access token

### Error de CSV
```
❌ Error parseando CSV
```
**Solución**: Verificar conectividad o usar archivo CSV local

### Error de Stock
```
⚠️ No hay productos con stock disponible
```
**Solución**: Normal, filtro de productos sin inventario

### Error de Permisos
```
❌ Response(code=403)
```
**Solución**: Revisar permisos del access token en Shopify

## 📁 Estructura del Proyecto

```
syscomShopify/
├── csv_to_shopify_v2.py      # Importador principal v2.0
├── import_productos.py       # Script de importación interactivo
├── run_tests.py             # Suite de tests completa
├── .env                     # Configuración (crear)
├── requirements.txt         # Dependencias
├── README.md               # Esta documentación
└── tests/
    ├── test_connection.py   # Test de conexión Shopify
    ├── test_local.py       # Test de CSV local
    └── test_v2.py          # Test completo v2
```

## 🆕 Nuevas Funcionalidades v2.0

- ✅ **Formato Shopify nativo**: Lee CSV en formato estándar de Shopify
- ✅ **Multi-encoding**: Soporte automático para diferentes codificaciones
- ✅ **Mejor manejo de errores**: Sistema robusto de fallbacks
- ✅ **Validación mejorada**: Verificaciones de datos más completas
- ✅ **Interface interactiva**: Script amigable para el usuario
- ✅ **Tests automatizados**: Suite completa de verificaciones

## 🔄 Migración desde v1.0

Los cambios principales desde la versión anterior:

1. **Nuevo formato CSV**: Ahora usa formato nativo de Shopify
2. **Nuevas columnas**: Mapeo directo de campos Shopify
3. **Nueva tienda**: Configurada para Sepacsye
4. **Mejor encoding**: Soporte para caracteres especiales

## 🤝 Soporte

Para problemas o sugerencias:
1. Revisar esta documentación
2. Ejecutar `python run_tests.py` para diagnóstico
3. Verificar logs de error en la consola
4. Comprobar configuración en `.env`

---

*Sistema desarrollado para automatizar la importación del catálogo SYSCOM a Shopify v2.0*
