# Instrucciones para Generar Ejecutable

## Método 1: Automático (Recomendado)

1. **Ejecutar el script batch:**
   ```
   crear_ejecutable.bat
   ```
   
   Este script hará todo automáticamente:
   - Instalar PyInstaller
   - Instalar dependencias
   - Generar el ejecutable
   - Crear paquete para el cliente

## Método 2: Manual

1. **Instalar dependencias:**
   ```
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Generar ejecutable:**
   ```
   python build_executable.py
   ```

## Resultado

Se creará una carpeta `cliente_package` con todo lo necesario:
- `SyscomShopifyImporter.exe` - El ejecutable principal
- `.env.template` - Plantilla de configuración
- `README.md` - Instrucciones para el cliente
- `config.ini` - Configuración personalizable
- Archivos CSV (si existen)

## Para el Cliente

Envíe toda la carpeta `cliente_package` al cliente junto con:
1. Sus credenciales de Shopify (shop name y access token)
2. El archivo CSV de productos
3. Instrucciones de configuración del archivo `.env`

## Nuevas Características Agregadas

✅ **Orden aleatorio**: Los productos se procesan en orden aleatorio para evitar patrones
✅ **Pausas inteligentes**: Delays entre requests para evitar rate limiting
✅ **Actualización de inventario**: Se actualiza automáticamente el stock después de crear cada producto
✅ **Configuración personalizable**: Archivo `config.ini` para ajustar comportamiento
✅ **Ejecutable standalone**: No requiere Python instalado en el equipo del cliente
