# Importador CSV a Shopify - AnimeShopify

Este proyecto permite descargar un CSV de productos desde OcioStock y subirlos automáticamente a tu tienda de Shopify.

## Configuración Inicial

### 1. Configurar Credenciales de Shopify

Edita el archivo `.env` y completa las siguientes variables:

```env
SHOPIFY_SHOP_NAME=tu-tienda.myshopify.com
SHOPIFY_ACCESS_TOKEN=tu_access_token_aqui
```

#### Cómo obtener las credenciales:

1. **Nombre de la tienda**: Es la parte antes de `.myshopify.com` en tu URL
2. **Access Token**: 
   - Ve a tu admin de Shopify
   - Ve a Apps > Develop apps (o Apps privadas)
   - Crea una nueva app privada
   - En la configuración de la app, habilita los siguientes permisos:
     - `write_products` (para crear productos)
     - `read_products` (para leer productos)
     - `write_inventory` (para gestionar inventario)
   - Genera el Access Token

### 2. Verificar Conexión

Antes de importar productos, verifica que la conexión funcione:

```bash
python test_connection.py
```

## Uso

### Importación Básica

Ejecuta el script principal:

```bash
python csv_to_shopify.py
```

El script te dará opciones:
1. **Importar todos los productos**: Procesará todo el CSV
2. **Importar 10 productos de prueba**: Para hacer pruebas
3. **Cantidad personalizada**: Especifica cuántos productos importar

### Características del Importador

- **Descarga automática**: Descarga el CSV desde la URL configurada
- **Procesamiento inteligente**: Extrae información de campos XML
- **Gestión de imágenes**: Procesa múltiples imágenes por producto
- **Control de inventario**: Configura stock y políticas de inventario
- **Rate limiting**: Respeta los límites de la API de Shopify
- **Logging detallado**: Registra todo el proceso

### Datos que se importan:

- ✅ Nombre del producto
- ✅ Descripción
- ✅ Precio
- ✅ SKU (referencia)
- ✅ Marca (vendor)
- ✅ Categoría (product_type)
- ✅ Inventario/Stock
- ✅ Peso (extraído de XML)
- ✅ Código de barras (extraído de XML)
- ✅ Múltiples imágenes
- ✅ Tags automáticos

## Estructura del Proyecto

```
animeShopify/
├── venv/                    # Entorno virtual
├── .env                     # Configuración (credenciales)
├── csv_to_shopify.py       # Script principal
├── test_connection.py      # Verificador de conexión
├── productos_ociostock.csv # CSV descargado (se genera automáticamente)
└── README.md              # Esta documentación
```

## Troubleshooting

### Error: "Faltan variables de entorno"
- Verifica que el archivo `.env` existe
- Asegúrate de que las variables están correctamente configuradas
- No uses espacios alrededor del `=`

### Error: "Error conectando con Shopify"
- Verifica las credenciales
- Asegúrate de que el access token tiene los permisos correctos
- Verifica que el nombre de la tienda es correcto

### Error: "Rate limiting"
- El script ya incluye delays automáticos
- Si sigues teniendo problemas, aumenta `DELAY_BETWEEN_REQUESTS` en `.env`

### Productos no se crean
- Verifica que el CSV se descarga correctamente
- Revisa los logs para ver errores específicos
- Algunos productos pueden fallar si faltan datos requeridos

## Configuraciones Avanzadas

En el archivo `.env` puedes configurar:

```env
# Máximo productos por lote
MAX_PRODUCTS_PER_BATCH=10

# Delay entre requests (segundos)
DELAY_BETWEEN_REQUESTS=1
```

## Logs

El script genera logs detallados que incluyen:
- Progreso de descarga del CSV
- Productos procesados exitosamente
- Errores específicos por producto
- Resumen final de la importación

## Notas Importantes

- **Productos duplicados**: El script no verifica duplicados. Si ejecutas múltiples veces, creará productos duplicados
- **Límites de Shopify**: Respeta los límites de la API de Shopify (2 requests por segundo por defecto)
- **Imágenes**: Las imágenes se enlazan desde las URLs originales (no se suben a Shopify)
- **Backup**: Siempre haz backup de tu tienda antes de importaciones masivas
