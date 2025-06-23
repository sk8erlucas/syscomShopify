#!/usr/bin/env python3
"""
Script para generar ejecutable del importador SYSCOM to Shopify
Usar PyInstaller para crear un .exe que el cliente pueda ejecutar
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """Instalar PyInstaller si no está instalado"""
    try:
        import PyInstaller
        print("✅ PyInstaller ya está instalado")
        return True
    except ImportError:
        print("📦 Instalando PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller instalado correctamente")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando PyInstaller: {e}")
            return False

def create_spec_file():
    """Crear archivo .spec personalizado para el ejecutable"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['csv_to_shopify.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('requirements.txt', '.'),
        ('*.csv', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'shopify',
        'requests',
        'python-dotenv',
        'csv',
        'json',
        'logging',
        'datetime',
        'urllib.parse',
        'typing',
        'os',
        'sys',
        'time',
        'random',
        're'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SyscomShopifyImporter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    cofile=None,
    icon=None,
    version_file=None,
)
'''
    
    with open('SyscomShopifyImporter.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ Archivo .spec creado")

def create_env_template():
    """Crear plantilla de archivo .env para el cliente"""
    env_template = '''# Configuración para Syscom Shopify Importer
# Copie este archivo a .env y complete con sus datos reales

# Datos de la tienda Shopify
SHOPIFY_SHOP_NAME=su-tienda.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# URL del CSV de SYSCOM (opcional, puede usar archivo local)
CSV_URL=https://ejemplo.com/productos.csv

# Configuración de importación
MAX_PRODUCTS_PER_BATCH=5
DELAY_BETWEEN_REQUESTS=2.0
'''
    
    with open('.env.template', 'w', encoding='utf-8') as f:
        f.write(env_template)
    
    print("✅ Plantilla .env creada")

def create_readme_for_client():
    """Crear README específico para el cliente"""
    readme_content = '''# Syscom Shopify Importer - Ejecutable

## Instrucciones de Uso

### 1. Configuración Inicial

1. **Copie el archivo `.env.template` a `.env`**
   ```
   copy .env.template .env
   ```

2. **Edite el archivo `.env` con sus datos:**
   - `SHOPIFY_SHOP_NAME`: El nombre de su tienda (ej: mitienda.myshopify.com)
   - `SHOPIFY_ACCESS_TOKEN`: Su token de acceso privado de Shopify
   - `CSV_URL`: URL del CSV de SYSCOM (opcional)

### 2. Obtener Token de Shopify

1. Vaya a su Admin de Shopify
2. Navegue a **Configuración > Aplicaciones y canales de venta**
3. Haga clic en **Desarrollar aplicaciones**
4. Cree una aplicación privada con permisos:
   - `read_products`, `write_products`
   - `read_inventory`, `write_inventory` 
   - `read_locations`

### 3. Preparar Archivo CSV

- Coloque su archivo CSV en la misma carpeta que el ejecutable
- Nombre sugerido: `ProductosHora.csv`
- O configure la URL en el archivo `.env`

### 4. Ejecutar

1. **Abra una terminal/cmd en esta carpeta**
2. **Ejecute:**
   ```
   SyscomShopifyImporter.exe
   ```

### 5. Características

- ✅ **Orden aleatorio**: Los productos se procesan en orden aleatorio
- ✅ **Control de velocidad**: Pausas automáticas entre requests
- ✅ **Manejo de errores**: Recuperación automática de errores
- ✅ **Actualización de inventario**: Stock actualizado automáticamente
- ✅ **Log detallado**: Archivo `import_log.txt` con todos los detalles

### 6. Archivos Generados

- `import_log.txt`: Log detallado de la importación
- Archivos CSV temporales (se eliminan automáticamente)

### 7. Solución de Problemas

**Error "Sin permisos":**
- Verifique que el token tenga todos los permisos necesarios

**Error "No se pudo obtener CSV":**
- Verifique la URL del CSV o coloque el archivo localmente

**Errores de conexión:**
- El programa incluye reintentos automáticos
- Verifique su conexión a internet

### 8. Soporte

Para soporte técnico, proporcione el archivo `import_log.txt` generado.
'''
    
    with open('README_CLIENTE.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ README para cliente creado")

def build_executable():
    """Construir el ejecutable"""
    print("🔨 Construyendo ejecutable...")
    
    try:
        # Usar el archivo .spec personalizado
        subprocess.check_call([
            sys.executable, "-m", "PyInstaller", 
            "--clean",
            "SyscomShopifyImporter.spec"
        ])
        
        print("✅ Ejecutable construido exitosamente")
        
        # Verificar si el ejecutable se creó
        exe_path = Path("dist/SyscomShopifyImporter.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📁 Ejecutable creado: {exe_path}")
            print(f"📏 Tamaño: {size_mb:.1f} MB")
            return True
        else:
            print("❌ No se encontró el ejecutable generado")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error construyendo ejecutable: {e}")
        return False

def create_distribution_package():
    """Crear paquete de distribución para el cliente"""
    print("📦 Creando paquete de distribución...")
    
    # Crear carpeta de distribución
    dist_folder = Path("cliente_package")
    if dist_folder.exists():
        shutil.rmtree(dist_folder)
    
    dist_folder.mkdir()
    
    # Copiar archivos necesarios
    files_to_copy = [
        ("dist/SyscomShopifyImporter.exe", "SyscomShopifyImporter.exe"),
        (".env.template", ".env.template"),
        ("README_CLIENTE.md", "README.md"),
        ("requirements.txt", "requirements.txt")
    ]
    
    for src, dst in files_to_copy:
        src_path = Path(src)
        if src_path.exists():
            shutil.copy2(src_path, dist_folder / dst)
            print(f"✅ Copiado: {dst}")
        else:
            print(f"⚠️ No encontrado: {src}")
    
    # Copiar archivos CSV si existen
    for csv_file in Path(".").glob("*.csv"):
        if csv_file.name != "productos_descargado*.csv":  # Excluir temporales
            shutil.copy2(csv_file, dist_folder / csv_file.name)
            print(f"✅ Copiado CSV: {csv_file.name}")
    
    print(f"📦 Paquete creado en: {dist_folder.absolute()}")
    print(f"🎁 Envíe toda la carpeta '{dist_folder.name}' al cliente")

def main():
    """Función principal"""
    print("🚀 SYSCOM SHOPIFY IMPORTER - CONSTRUCTOR DE EJECUTABLE")
    print("=" * 60)
    
    # Verificar que existe el archivo principal
    if not Path("csv_to_shopify.py").exists():
        print("❌ No se encontró csv_to_shopify.py")
        return
    
    # Instalar PyInstaller
    if not install_pyinstaller():
        return
    
    # Crear archivos necesarios
    create_spec_file()
    create_env_template()
    create_readme_for_client()
    
    # Construir ejecutable
    if build_executable():
        create_distribution_package()
        print("\n🎉 ¡EJECUTABLE LISTO PARA EL CLIENTE!")
        print("📁 Envíe la carpeta 'cliente_package' completa")
    else:
        print("\n❌ Error creando ejecutable")

if __name__ == "__main__":
    main()
