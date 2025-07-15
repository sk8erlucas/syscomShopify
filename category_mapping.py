#!/usr/bin/env python3
"""
Mapeo de categorías SYSCOM a categorías Shopify/Google Shopping
"""

# Diccionario de mapeo de categorías
CATEGORY_MAPPING = {
    # Cableado Estructurado
    "Cableado Estructurado > Fibra Óptica > Distribuidores de Fibra Óptica": "Electronics > Electronics Accessories > Cable Management > Patch Panels",
    "Cableado Estructurado > Fibra Óptica > Cables": "Electronics > Electronics Accessories > Cables > Fiber Optic Cables",
    "Cableado Estructurado > Fibra Óptica > Conectores": "Electronics > Electronics Accessories > Cable Management > Connectors",
    "Cableado Estructurado > Fibra Óptica > Pigtails": "Electronics > Electronics Accessories > Cables > Fiber Optic Cables",
    "Cableado Estructurado > Fibra Óptica > Acopladores": "Electronics > Electronics Accessories > Cable Management > Couplers",
    "Cableado Estructurado > Fibra Óptica > Adaptadores": "Electronics > Electronics Accessories > Cable Management > Adapters",
    "Cableado Estructurado > Fibra Óptica > Atenuadores": "Electronics > Electronics Accessories > Cable Management > Attenuators",
    "Cableado Estructurado > Fibra Óptica > Patch Cords": "Electronics > Electronics Accessories > Cables > Patch Cables",
    "Cableado Estructurado > Fibra Óptica > Patch Panels": "Electronics > Electronics Accessories > Cable Management > Patch Panels",
    "Cableado Estructurado > Fibra Óptica > Cajas de Terminación": "Electronics > Electronics Accessories > Cable Management > Junction Boxes",
    "Cableado Estructurado > Fibra Óptica > Organizadores": "Electronics > Electronics Accessories > Cable Management > Cable Organizers",
    "Cableado Estructurado > Fibra Óptica > Gabinetes": "Electronics > Electronics Accessories > Cable Management > Cabinets",
    "Cableado Estructurado > Fibra Óptica > Herramientas": "Electronics > Electronics Accessories > Tools > Fiber Optic Tools",
    "Cableado Estructurado > Fibra Óptica > Medidores": "Electronics > Electronics Accessories > Test Equipment > Optical Meters",
    "Cableado Estructurado > Fibra Óptica > Fusionadoras": "Electronics > Electronics Accessories > Tools > Fusion Splicers",
    "Cableado Estructurado > Fibra Óptica > Limpiadoras": "Electronics > Electronics Accessories > Tools > Fiber Cleaners",
    "Cableado Estructurado > Fibra Óptica > Todos": "Electronics > Electronics Accessories > Cables > Fiber Optic Cables",

    # Cables de Cobre
    "Cableado Estructurado > Cables de Cobre > UTP": "Electronics > Electronics Accessories > Cables > Network Cables",
    "Cableado Estructurado > Cables de Cobre > FTP": "Electronics > Electronics Accessories > Cables > Network Cables",
    "Cableado Estructurado > Cables de Cobre > STP": "Electronics > Electronics Accessories > Cables > Network Cables",
    "Cableado Estructurado > Cables de Cobre > Coaxial": "Electronics > Electronics Accessories > Cables > Coaxial Cables",
    "Cableado Estructurado > Cables de Cobre > Patch Cords": "Electronics > Electronics Accessories > Cables > Patch Cables",
    "Cableado Estructurado > Cables de Cobre > Extensiones": "Electronics > Electronics Accessories > Cables > Extension Cables",
    "Cableado Estructurado > Cables de Cobre > Todos": "Electronics > Electronics Accessories > Cables > Network Cables",

    # Conectividad
    "Cableado Estructurado > Conectividad > Jacks": "Electronics > Electronics Accessories > Cable Management > Jacks",
    "Cableado Estructurado > Conectividad > Plugs": "Electronics > Electronics Accessories > Cable Management > Plugs",
    "Cableado Estructurado > Conectividad > Patch Panels": "Electronics > Electronics Accessories > Cable Management > Patch Panels",
    "Cableado Estructurado > Conectividad > Face Plates": "Electronics > Electronics Accessories > Cable Management > Wall Plates",
    "Cableado Estructurado > Conectividad > Cajas de Piso": "Electronics > Electronics Accessories > Cable Management > Floor Boxes",
    "Cableado Estructurado > Conectividad > Organizadores": "Electronics > Electronics Accessories > Cable Management > Cable Organizers",
    "Cableado Estructurado > Conectividad > Canaletas": "Electronics > Electronics Accessories > Cable Management > Raceways",
    "Cableado Estructurado > Conectividad > Gabinetes": "Electronics > Electronics Accessories > Cable Management > Cabinets",
    "Cableado Estructurado > Conectividad > Racks": "Electronics > Electronics Accessories > Cable Management > Racks",
    "Cableado Estructurado > Conectividad > Todos": "Electronics > Electronics Accessories > Cable Management",

    # Herramientas
    "Cableado Estructurado > Herramientas > Pinzas": "Electronics > Electronics Accessories > Tools > Pliers",
    "Cableado Estructurado > Herramientas > Ponchadores": "Electronics > Electronics Accessories > Tools > Crimping Tools",
    "Cableado Estructurado > Herramientas > Testers": "Electronics > Electronics Accessories > Test Equipment > Cable Testers",
    "Cableado Estructurado > Herramientas > Certificadores": "Electronics > Electronics Accessories > Test Equipment > Cable Certifiers",
    "Cableado Estructurado > Herramientas > Insertadoras": "Electronics > Electronics Accessories > Tools > Insertion Tools",
    "Cableado Estructurado > Herramientas > Peladoras": "Electronics > Electronics Accessories > Tools > Wire Strippers",
    "Cableado Estructurado > Herramientas > Todos": "Electronics > Electronics Accessories > Tools",

    # Automatización e Intrusión
    "Automatización e Intrusión > Alarmas > Paneles": "Electronics > Electronics Accessories > Security > Alarm Panels",
    "Automatización e Intrusión > Alarmas > Detectores": "Electronics > Electronics Accessories > Security > Detectors",
    "Automatización e Intrusión > Alarmas > Sensores": "Electronics > Electronics Accessories > Security > Sensors",
    "Automatización e Intrusión > Alarmas > Sirenas": "Electronics > Electronics Accessories > Security > Sirens",
    "Automatización e Intrusión > Alarmas > Teclados": "Electronics > Electronics Accessories > Security > Keypads",
    "Automatización e Intrusión > Alarmas > Contactos": "Electronics > Electronics Accessories > Security > Contacts",
    "Automatización e Intrusión > Alarmas > Cables": "Electronics > Electronics Accessories > Cables > Security Cables",
    "Automatización e Intrusión > Alarmas > Fuentes": "Electronics > Electronics Accessories > Power > Power Supplies",
    "Automatización e Intrusión > Alarmas > Todos": "Electronics > Electronics Accessories > Security",

    # Videovigilancia
    "Videovigilancia > Cámaras IP > Domo": "Electronics > Electronics Accessories > Security > IP Cameras",
    "Videovigilancia > Cámaras IP > Bullet": "Electronics > Electronics Accessories > Security > IP Cameras",
    "Videovigilancia > Cámaras IP > Fisheye": "Electronics > Electronics Accessories > Security > IP Cameras",
    "Videovigilancia > Cámaras IP > PTZ": "Electronics > Electronics Accessories > Security > PTZ Cameras",
    "Videovigilancia > Cámaras IP > Térmicas": "Electronics > Electronics Accessories > Security > Thermal Cameras",
    "Videovigilancia > Cámaras IP > Todos": "Electronics > Electronics Accessories > Security > IP Cameras",

    "Videovigilancia > Cámaras Análogas > Domo": "Electronics > Electronics Accessories > Security > Analog Cameras",
    "Videovigilancia > Cámaras Análogas > Bullet": "Electronics > Electronics Accessories > Security > Analog Cameras",
    "Videovigilancia > Cámaras Análogas > Térmicas": "Electronics > Electronics Accessories > Security > Thermal Cameras",
    "Videovigilancia > Cámaras Análogas > Todos": "Electronics > Electronics Accessories > Security > Analog Cameras",

    "Videovigilancia > Grabadores > NVR": "Electronics > Electronics Accessories > Security > NVR",
    "Videovigilancia > Grabadores > DVR": "Electronics > Electronics Accessories > Security > DVR",
    "Videovigilancia > Grabadores > Híbridos": "Electronics > Electronics Accessories > Security > Hybrid Recorders",
    "Videovigilancia > Grabadores > Todos": "Electronics > Electronics Accessories > Security > Video Recorders",

    "Videovigilancia > Almacenamiento > Discos Duros": "Electronics > Electronics Accessories > Storage > Hard Drives",
    "Videovigilancia > Almacenamiento > Todos": "Electronics > Electronics Accessories > Storage",

    "Videovigilancia > Accesorios > Monitores": "Electronics > Electronics Accessories > Video > Monitors",
    "Videovigilancia > Accesorios > Soportes": "Electronics > Electronics Accessories > Video > Mounts",
    "Videovigilancia > Accesorios > Cables": "Electronics > Electronics Accessories > Cables > Video Cables",
    "Videovigilancia > Accesorios > Fuentes": "Electronics > Electronics Accessories > Power > Power Supplies",
    "Videovigilancia > Accesorios > Todos": "Electronics > Electronics Accessories > Video",

    # Networking
    "Networking > Switches > Administrables": "Electronics > Electronics Accessories > Networking > Managed Switches",
    "Networking > Switches > No Administrables": "Electronics > Electronics Accessories > Networking > Unmanaged Switches",
    "Networking > Switches > PoE": "Electronics > Electronics Accessories > Networking > PoE Switches",
    "Networking > Switches > Industriales": "Electronics > Electronics Accessories > Networking > Industrial Switches",
    "Networking > Switches > Todos": "Electronics > Electronics Accessories > Networking > Switches",

    "Networking > Routers > Empresariales": "Electronics > Electronics Accessories > Networking > Enterprise Routers",
    "Networking > Routers > SOHO": "Electronics > Electronics Accessories > Networking > SOHO Routers",
    "Networking > Routers > Industriales": "Electronics > Electronics Accessories > Networking > Industrial Routers",
    "Networking > Routers > Todos": "Electronics > Electronics Accessories > Networking > Routers",

    "Networking > Access Points > Indoor": "Electronics > Electronics Accessories > Networking > Indoor Access Points",
    "Networking > Access Points > Outdoor": "Electronics > Electronics Accessories > Networking > Outdoor Access Points",
    "Networking > Access Points > Controladores": "Electronics > Electronics Accessories > Networking > WLAN Controllers",
    "Networking > Access Points > Todos": "Electronics > Electronics Accessories > Networking > Access Points",

    "Networking > Antenas > Omnidireccionales": "Electronics > Electronics Accessories > Networking > Omnidirectional Antennas",
    "Networking > Antenas > Direccionales": "Electronics > Electronics Accessories > Networking > Directional Antennas",
    "Networking > Antenas > Sectoriales": "Electronics > Electronics Accessories > Networking > Sectoral Antennas",
    "Networking > Antenas > Todos": "Electronics > Electronics Accessories > Networking > Antennas",

    # Control de Acceso
    "Control de Acceso > Lectores > Proximidad": "Electronics > Electronics Accessories > Security > Proximity Readers",
    "Control de Acceso > Lectores > Biométricos": "Electronics > Electronics Accessories > Security > Biometric Readers",
    "Control de Acceso > Lectores > Magnéticos": "Electronics > Electronics Accessories > Security > Magnetic Readers",
    "Control de Acceso > Lectores > Todos": "Electronics > Electronics Accessories > Security > Access Control Readers",

    "Control de Acceso > Controladores > Standalone": "Electronics > Electronics Accessories > Security > Standalone Controllers",
    "Control de Acceso > Controladores > Networked": "Electronics > Electronics Accessories > Security > Network Controllers",
    "Control de Acceso > Controladores > Todos": "Electronics > Electronics Accessories > Security > Access Controllers",

    "Control de Acceso > Cerraduras > Electromagnéticas": "Electronics > Electronics Accessories > Security > Electromagnetic Locks",
    "Control de Acceso > Cerraduras > Eléctricas": "Electronics > Electronics Accessories > Security > Electric Locks",
    "Control de Acceso > Cerraduras > Todos": "Electronics > Electronics Accessories > Security > Electronic Locks",

    # Audio y Video
    "Audio y Video > Micrófonos > Dinámicos": "Electronics > Electronics Accessories > Audio > Dynamic Microphones",
    "Audio y Video > Micrófonos > Condensador": "Electronics > Electronics Accessories > Audio > Condenser Microphones",
    "Audio y Video > Micrófonos > Inalámbricos": "Electronics > Electronics Accessories > Audio > Wireless Microphones",
    "Audio y Video > Micrófonos > Todos": "Electronics > Electronics Accessories > Audio > Microphones",

    "Audio y Video > Amplificadores > Potencia": "Electronics > Electronics Accessories > Audio > Power Amplifiers",
    "Audio y Video > Amplificadores > Mezcladoras": "Electronics > Electronics Accessories > Audio > Audio Mixers",
    "Audio y Video > Amplificadores > Todos": "Electronics > Electronics Accessories > Audio > Amplifiers",

    "Audio y Video > Bocinas > Pasivas": "Electronics > Electronics Accessories > Audio > Passive Speakers",
    "Audio y Video > Bocinas > Activas": "Electronics > Electronics Accessories > Audio > Active Speakers",
    "Audio y Video > Bocinas > Todos": "Electronics > Electronics Accessories > Audio > Speakers",

    # Energía
    "Energía > UPS > Interactivos": "Electronics > Electronics Accessories > Power > Interactive UPS",
    "Energía > UPS > Online": "Electronics > Electronics Accessories > Power > Online UPS",
    "Energía > UPS > Offline": "Electronics > Electronics Accessories > Power > Offline UPS",
    "Energía > UPS > Todos": "Electronics > Electronics Accessories > Power > UPS",

    "Energía > Reguladores > Ferroresonantes": "Electronics > Electronics Accessories > Power > Voltage Regulators",
    "Energía > Reguladores > Electrónicos": "Electronics > Electronics Accessories > Power > Electronic Regulators",
    "Energía > Reguladores > Todos": "Electronics > Electronics Accessories > Power > Voltage Regulators",

    "Energía > Baterías > Selladas": "Electronics > Electronics Accessories > Power > Sealed Batteries",
    "Energía > Baterías > Gel": "Electronics > Electronics Accessories > Power > Gel Batteries",
    "Energía > Baterías > Todos": "Electronics > Electronics Accessories > Power > Batteries",

    # Automatización Domótica
    "Automatización Domótica > Iluminación > Dimmers": "Electronics > Electronics Accessories > Home Automation > Dimmers",
    "Automatización Domótica > Iluminación > Switches": "Electronics > Electronics Accessories > Home Automation > Smart Switches",
    "Automatización Domótica > Iluminación > Todos": "Electronics > Electronics Accessories > Home Automation > Lighting",

    "Automatización Domótica > Climatización > Termostatos": "Electronics > Electronics Accessories > Home Automation > Thermostats",
    "Automatización Domótica > Climatización > Sensores": "Electronics > Electronics Accessories > Home Automation > Climate Sensors",
    "Automatización Domótica > Climatización > Todos": "Electronics > Electronics Accessories > Home Automation > Climate Control",

    "Automatización Domótica > Seguridad > Sensores": "Electronics > Electronics Accessories > Home Automation > Security Sensors",
    "Automatización Domótica > Seguridad > Detectores": "Electronics > Electronics Accessories > Home Automation > Security Detectors",
    "Automatización Domótica > Seguridad > Todos": "Electronics > Electronics Accessories > Home Automation > Security",

    # Computo
    "Computo > Equipos > Desktops": "Electronics > Computers > Desktop Computers",
    "Computo > Equipos > Laptops": "Electronics > Computers > Laptop Computers",
    "Computo > Equipos > Tablets": "Electronics > Computers > Tablet Computers",
    "Computo > Equipos > Todos": "Electronics > Computers",

    "Computo > Accesorios > Monitores": "Electronics > Electronics Accessories > Computer Components > Monitors",
    "Computo > Accesorios > Teclados": "Electronics > Electronics Accessories > Computer Components > Keyboards",
    "Computo > Accesorios > Mouse": "Electronics > Electronics Accessories > Computer Components > Mice",
    "Computo > Accesorios > Todos": "Electronics > Electronics Accessories > Computer Components",

    # Telefonía
    "Telefonía > Teléfonos IP > Escritorio": "Electronics > Electronics Accessories > Telephony > IP Desk Phones",
    "Telefonía > Teléfonos IP > Inalámbricos": "Electronics > Electronics Accessories > Telephony > IP Wireless Phones",
    "Telefonía > Teléfonos IP > Todos": "Electronics > Electronics Accessories > Telephony > IP Phones",

    "Telefonía > PBX > IP": "Electronics > Electronics Accessories > Telephony > IP PBX",
    "Telefonía > PBX > Híbridos": "Electronics > Electronics Accessories > Telephony > Hybrid PBX",
    "Telefonía > PBX > Todos": "Electronics > Electronics Accessories > Telephony > PBX Systems",

    # Mapeo por defecto para categorías no específicas
    "Automatización e Intrusión": "Electronics > Electronics Accessories > Security",
    "Videovigilancia": "Electronics > Electronics Accessories > Security",
    "Networking": "Electronics > Electronics Accessories > Networking",
    "Control de Acceso": "Electronics > Electronics Accessories > Security",
    "Audio y Video": "Electronics > Electronics Accessories > Audio",
    "Energía": "Electronics > Electronics Accessories > Power",
    "Automatización Domótica": "Electronics > Electronics Accessories > Home Automation",
    "Computo": "Electronics > Computers",
    "Telefonía": "Electronics > Electronics Accessories > Telephony",
    "Cableado Estructurado": "Electronics > Electronics Accessories > Cables",
}

# Mapeos específicos para categorías más frecuentes
SPECIFIC_CATEGORY_MAPPING = {
    # Cableado Estructurado - Específicos
    "Cableado Estructurado > Cableado de Cobre > Patch Cords": "Electronics > Electronics Accessories > Cables > Patch Cables",
    "Cableado Estructurado > Canalización > Tubería Metálica CONDUIT / Accesorios": "Electronics > Electronics Accessories > Cable Management > Conduits",
    "Cableado Estructurado > Canalización > Fijación": "Electronics > Electronics Accessories > Cable Management > Mounting Hardware",
    "Cableado Estructurado > Cableado de Cobre > Herramientas": "Electronics > Electronics Accessories > Tools > Cable Tools",
    "Cableado Estructurado > Fibra Óptica > Jumpers y Pigtails": "Electronics > Electronics Accessories > Cables > Fiber Optic Cables",
    "Cableado Estructurado > Cableado de Cobre > Jacks / Plugs": "Electronics > Electronics Accessories > Cable Management > Jacks",
    "Cableado Estructurado > Canalización > Tubería PVC / Registros PVC": "Electronics > Electronics Accessories > Cable Management > PVC Conduits",
    "Cableado Estructurado > Canalización > Accesorios para Canaletas": "Electronics > Electronics Accessories > Cable Management > Raceway Accessories",
    
    # Control de Acceso - Específicos
    "Control  de Acceso > Acceso Vehicular > Accesorios": "Electronics > Electronics Accessories > Security > Vehicle Access Accessories",
    "Control  de Acceso > Acceso Vehicular > Refacciones": "Electronics > Electronics Accessories > Security > Vehicle Access Parts",
    "Control  de Acceso > Herramientas > Accesorios de Instalación": "Electronics > Electronics Accessories > Security > Installation Tools",
    
    # Videovigilancia - Específicos
    "Videovigilancia > Accesorios Generales > Montajes y Brackets para Cámaras": "Electronics > Electronics Accessories > Security > Camera Mounts",
    "Videovigilancia > Cámaras IP y NVRs > Domo / Eyeball / Turret": "Electronics > Electronics Accessories > Security > IP Cameras",
    "Videovigilancia > Cámaras IP y NVRs > WiFi / 4G / PoE": "Electronics > Electronics Accessories > Security > IP Cameras",
    "Videovigilancia > Servidores / Almacenamiento > Servidores": "Electronics > Electronics Accessories > Security > Video Servers",
    "Videovigilancia > Accesorios Generales > Fuentes de Alimentación": "Electronics > Electronics Accessories > Power > Power Supplies",
    
    # Automatización e Intrusión - Específicos
    "Automatización   e Intrusión > Automatización - Casa Inteligente > Lutron": "Electronics > Electronics Accessories > Home Automation > Lutron",
    "Automatización e Intrusión > Automatización - Casa Inteligente > Lutron": "Electronics > Electronics Accessories > Home Automation > Lutron",
    "Automatización e Intrusión > Cercas Eléctricas > Postes": "Electronics > Electronics Accessories > Security > Electric Fence Posts",
    "Automatización e Intrusión > Accesorios > Sirenas y Estrobos": "Electronics > Electronics Accessories > Security > Sirens",
    "Automatización e Intrusión > Cables > Todos": "Electronics > Electronics Accessories > Cables > Security Cables",
    "Automatización e Intrusión > Paneles de Alarma > Todos": "Electronics > Electronics Accessories > Security > Alarm Panels",
    "Automatización e Intrusión > Detectores / Sensores > Movimiento para Interior": "Electronics > Electronics Accessories > Security > Motion Detectors",
    "Automatización e Intrusión > Detectores / Sensores > Movimiento para Exterior": "Electronics > Electronics Accessories > Security > Outdoor Motion Detectors",
    "Automatización e Intrusión > Megafonía y Audioevacuación > EPCOM ProAudio": "Electronics > Electronics Accessories > Audio > Professional Audio",
    
    # Redes e IT - Específicos
    "Redes e IT > Racks y Gabinetes > Accesorios para Racks y Gabinetes": "Electronics > Electronics Accessories > Cable Management > Rack Accessories",
    "Redes e IT > Networking > Pólizas de Garantía": "Electronics > Electronics Accessories > Networking > Service Plans",
    "Redes e IT > Networking > Switches PoE": "Electronics > Electronics Accessories > Networking > PoE Switches",
    "Redes e IT > Networking > Transceptores de Fibra": "Electronics > Electronics Accessories > Networking > Fiber Transceivers",
    "Redes e IT > Networking > Switches": "Electronics > Electronics Accessories > Networking > Switches",
    "Redes e IT > Networking > Access Points": "Electronics > Electronics Accessories > Networking > Access Points",
    "Redes e IT > Networking > Routers": "Electronics > Electronics Accessories > Networking > Routers",
    "Redes e IT > Networking > Wireless": "Electronics > Electronics Accessories > Networking > Wireless Equipment",
    
    # Energía / Herramientas - Específicos
    "Energía / Herramientas > Calidad de la Energía > Accesorios para Tierra Física": "Electronics > Electronics Accessories > Power > Grounding Accessories",
    "Energía / Herramientas > UPS > Baterías": "Electronics > Electronics Accessories > Power > UPS Batteries",
    "Energía / Herramientas > UPS > Interactivos": "Electronics > Electronics Accessories > Power > Interactive UPS",
    "Energía / Herramientas > Reguladores > Todos": "Electronics > Electronics Accessories > Power > Voltage Regulators",
    "Energía / Herramientas > Herramientas > Medición": "Electronics > Electronics Accessories > Test Equipment > Measurement Tools",
}

# Agregar mapeos específicos al diccionario principal
CATEGORY_MAPPING.update(SPECIFIC_CATEGORY_MAPPING)

def convertir_categoria(categoria_syscom: str) -> str:
    """
    Convierte una categoría SYSCOM a categoría Shopify/Google Shopping
    
    Args:
        categoria_syscom: Categoría en formato SYSCOM
        
    Returns:
        Categoría convertida o la original si no se encuentra mapeo
    """
    if not categoria_syscom:
        return categoria_syscom
    
    # Limpiar la categoría de caracteres especiales y espacios extra
    categoria_limpia = categoria_syscom.strip()
    
    # Buscar mapeo directo
    if categoria_limpia in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[categoria_limpia]
    
    # Buscar mapeo parcial (por categoría principal)
    for categoria_syscom_key, categoria_shopify in CATEGORY_MAPPING.items():
        if categoria_limpia.startswith(categoria_syscom_key.split(' > ')[0]):
            # Si encuentra la categoría principal, usar el mapeo más específico posible
            partes_categoria = categoria_limpia.split(' > ')
            if len(partes_categoria) >= 2:
                # Buscar mapeo más específico
                for key in CATEGORY_MAPPING:
                    if key.startswith(f"{partes_categoria[0]} > {partes_categoria[1]}"):
                        return CATEGORY_MAPPING[key]
                        
                # Si no encuentra específico, usar el de la categoría principal
                categoria_principal = partes_categoria[0]
                if categoria_principal in CATEGORY_MAPPING:
                    return CATEGORY_MAPPING[categoria_principal]
            break
    
    # Si no encuentra mapeo, devolver la categoría original
    return categoria_syscom

def obtener_estadisticas_mapeo():
    """
    Obtiene estadísticas del mapeo de categorías
    
    Returns:
        Dict con estadísticas del mapeo
    """
    categorias_principales = set()
    categorias_secundarias = set()
    categorias_terciarias = set()
    
    for categoria in CATEGORY_MAPPING.keys():
        partes = categoria.split(' > ')
        if len(partes) >= 1:
            categorias_principales.add(partes[0])
        if len(partes) >= 2:
            categorias_secundarias.add(f"{partes[0]} > {partes[1]}")
        if len(partes) >= 3:
            categorias_terciarias.add(categoria)
    
    return {
        'total_mapeos': len(CATEGORY_MAPPING),
        'categorias_principales': len(categorias_principales),
        'categorias_secundarias': len(categorias_secundarias),
        'categorias_terciarias': len(categorias_terciarias),
        'mapeos_principales': list(categorias_principales),
        'ejemplo_mapeo': list(CATEGORY_MAPPING.items())[:5]
    }

if __name__ == "__main__":
    # Ejemplo de uso
    print("🗂️ MAPEO DE CATEGORÍAS SYSCOM A SHOPIFY")
    print("="*50)
    
    # Mostrar estadísticas
    stats = obtener_estadisticas_mapeo()
    print(f"📊 Total de mapeos: {stats['total_mapeos']}")
    print(f"📋 Categorías principales: {stats['categorias_principales']}")
    print(f"📋 Categorías secundarias: {stats['categorias_secundarias']}")
    print(f"📋 Categorías terciarias: {stats['categorias_terciarias']}")
    
    print(f"\n📝 Ejemplos de mapeo:")
    for original, convertida in stats['ejemplo_mapeo']:
        print(f"   {original}")
        print(f"   → {convertida}")
        print()
    
    # Pruebas
    print(f"🧪 Pruebas de conversión:")
    categorias_prueba = [
        "Cableado Estructurado > Fibra Óptica > Distribuidores de Fibra Óptica",
        "Automatización e Intrusión > Alarmas > Paneles",
        "Videovigilancia > Cámaras IP > Domo",
        "Networking > Switches > PoE",
        "Categoría No Mapeada"
    ]
    
    for categoria in categorias_prueba:
        convertida = convertir_categoria(categoria)
        print(f"   {categoria}")
        print(f"   → {convertida}")
        print()
