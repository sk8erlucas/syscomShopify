#!/usr/bin/env python3
"""
Script Simplificado de Automatización de Checkboxes
Versión más simple y específica para interfaces web
"""

import pyautogui
import time
import logging
from datetime import datetime
import keyboard
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_automation_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class SimpleCheckboxAutomator:
    def __init__(self):
        """Inicializar automatizador simple"""
        self.running = False
        self.paused = False
        self.click_delay = 3.0  # Segundos entre clicks
        self.page_wait = 5.0    # Tiempo después de avanzar página
        
        # Configurar PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
        # Sistema de lista negra para checkboxes problemáticos
        self.clicked_positions = {}  # Diccionario: posición -> cantidad de clicks
        self.blacklisted_positions = set()  # Posiciones que ya no se deben clickear
        self.max_clicks_per_position = 2  # Máximo de clicks por posición antes de blacklistear
        self.position_tolerance = 10  # Tolerancia en píxeles para considerar misma posición
        
        # Estadísticas
        self.stats = {
            'clicks_realizados': 0,
            'checkboxes_blacklisteados': 0,
            'desplazamientos_realizados': 0,
            'ciclos_sin_checkboxes': 0,
            'tiempo_inicio': None
        }
    
    def find_checkbox_image(self):
        """Buscar checkbox usando imagen de referencia"""
        try:
            # Primero intenta encontrar con la imagen que guardes
            checkbox_location = pyautogui.locateOnScreen('check.png', confidence=0.8)
            if checkbox_location:
                center = pyautogui.center(checkbox_location)
                return center
        except pyautogui.ImageNotFoundException:
            pass
        except FileNotFoundError:
            logging.warning("⚠️ No se encontró check.png - usa captura de ejemplo")
        
        return None
    
    def find_checkbox_by_color(self):
        """Buscar checkboxes por patrones de color comunes"""
        try:
            # Buscar colores típicos de checkboxes
            # Checkbox azul típico de muchas webs
            blue_checkbox = pyautogui.locateOnScreen(None, 
                                                   region=None,
                                                   confidence=0.7)
            # Esta función necesitaría una implementación más específica
            # basada en la interfaz que estés usando
            
        except Exception as e:
            logging.debug(f"Búsqueda por color falló: {e}")
        
        return None
    
    def click_at_position(self, x, y):
        """Clickear en posición específica con control de lista negra"""
        try:
            # Verificar si la posición está en lista negra
            if self.is_position_blacklisted(x, y):
                logging.info(f"🚫 Posición ({x}, {y}) en lista negra - ignorando")
                return False
            
            logging.info(f"🖱️ Clickeando en ({x}, {y})")
            pyautogui.click(x, y)
            
            # Registrar el click y manejar lista negra
            self.record_click(x, y)
            
            self.stats['clicks_realizados'] += 1
            time.sleep(self.click_delay)
            return True
        except Exception as e:
            logging.error(f"❌ Error clickeando: {e}")
            return False
    
    def search_and_click_checkboxes(self):
        """Buscar y clickear checkboxes evitando posiciones problemáticas"""
        checkboxes_found = 0
        checkboxes_clicked = 0
        checkboxes_ignored = 0
        
        # Método 1: Buscar por imagen de referencia
        checkbox_pos = self.find_checkbox_image()
        if checkbox_pos:
            if not self.is_position_blacklisted(checkbox_pos.x, checkbox_pos.y):
                if self.click_at_position(checkbox_pos.x, checkbox_pos.y):
                    checkboxes_clicked += 1
                checkboxes_found += 1
            else:
                checkboxes_ignored += 1
        
        # Método 2: Buscar múltiples checkboxes
        try:
            checkboxes = list(pyautogui.locateAllOnScreen('check.png', confidence=0.7))
            for checkbox in checkboxes:
                if not self.running:
                    break
                
                center = pyautogui.center(checkbox)
                checkboxes_found += 1
                
                # Verificar si la posición está en lista negra
                if not self.is_position_blacklisted(center.x, center.y):
                    if self.click_at_position(center.x, center.y):
                        checkboxes_clicked += 1
                else:
                    checkboxes_ignored += 1
                    logging.debug(f"Ignorando checkbox en ({center.x}, {center.y}) - en lista negra")
        except:
            pass
        
        if checkboxes_ignored > 0:
            print(f"🚫 {checkboxes_ignored} checkboxes ignorados (ya clickeados múltiples veces)")
        
        if checkboxes_clicked > 0:
            print(f"✅ {checkboxes_clicked} checkboxes clickeados exitosamente")
        
        return checkboxes_clicked
    
    def advance_page(self):
        """Avanzar usando flechas hacia abajo y limpiar lista negra"""
        try:
            logging.info("⬇️ Presionando flecha abajo 15 veces...")
            print("⬇️ Desplazando hacia abajo...")
            
            for i in range(15):
                pyautogui.press('down')
                logging.info(f"   Flecha abajo {i+1}/15")
                time.sleep(1)  # Pausa de 1 segundo entre cada presión
                
            self.stats['desplazamientos_realizados'] += 1
            
            # Limpiar lista negra parcialmente tras desplazamiento
            # Los checkboxes pueden haber cambiado de posición
            self.clean_blacklist_after_scroll()
            
            logging.info("✅ Desplazamiento completado, continuando búsqueda...")
            
        except Exception as e:
            logging.error(f"❌ Error desplazando hacia abajo: {e}")
    
    def clean_blacklist_after_scroll(self):
        """Limpiar parcialmente la lista negra después de desplazarse"""
        blacklist_size_before = len(self.blacklisted_positions)
        
        # Limpiar completamente la lista negra tras desplazamiento
        # Ya que las posiciones de los checkboxes pueden haber cambiado
        self.blacklisted_positions.clear()
        self.clicked_positions.clear()
        
        if blacklist_size_before > 0:
            logging.info(f"🧹 Lista negra limpiada tras desplazamiento ({blacklist_size_before} posiciones eliminadas)")
            print(f"🧹 Reiniciando detección tras desplazamiento")
    
    def setup_controls(self):
        """Configurar controles de teclado"""
        keyboard.add_hotkey('ctrl+alt+p', self.toggle_pause)
        keyboard.add_hotkey('ctrl+alt+s', self.stop)
        keyboard.add_hotkey('esc', self.emergency_stop)
        
        print("🎮 Controles:")
        print("   Ctrl+Alt+P: Pausar/Reanudar")
        print("   Ctrl+Alt+S: Parar")
        print("   ESC: Parada de emergencia")
    
    def toggle_pause(self):
        """Pausar/reanudar"""
        self.paused = not self.paused
        status = "PAUSADO" if self.paused else "REANUDADO"
        print(f"⏸️ {status}")
    
    def stop(self):
        """Parar automatización"""
        self.running = False
        print("🛑 PARANDO...")
    
    def emergency_stop(self):
        """Parada de emergencia"""
        print("🚨 PARADA DE EMERGENCIA")
        self.running = False
        os._exit(0)
    
    def get_position_key(self, x, y):
        """Convertir coordenadas a una clave única considerando tolerancia"""
        # Redondear a la tolerancia más cercana para agrupar clicks cercanos
        key_x = round(x / self.position_tolerance) * self.position_tolerance
        key_y = round(y / self.position_tolerance) * self.position_tolerance
        return (key_x, key_y)
    
    def is_position_blacklisted(self, x, y):
        """Verificar si una posición está en la lista negra"""
        position_key = self.get_position_key(x, y)
        return position_key in self.blacklisted_positions
    
    def record_click(self, x, y):
        """Registrar un click en una posición y manejar lista negra"""
        position_key = self.get_position_key(x, y)
        
        # Incrementar contador de clicks para esta posición
        if position_key not in self.clicked_positions:
            self.clicked_positions[position_key] = 0
        
        self.clicked_positions[position_key] += 1
        clicks_count = self.clicked_positions[position_key]
        
        logging.info(f"📍 Posición ({x}, {y}) clickeada {clicks_count} vez(es)")
        
        # Si se ha clickeado demasiadas veces, agregar a lista negra
        if clicks_count >= self.max_clicks_per_position:
            self.blacklisted_positions.add(position_key)
            self.stats['checkboxes_blacklisteados'] += 1
            logging.info(f"🚫 Posición ({x}, {y}) agregada a lista negra (clickeada {clicks_count} veces)")
            print(f"🚫 Checkbox en ({x}, {y}) ignorado - no desaparece tras {clicks_count} clicks")
        
        return clicks_count
    
    def get_blacklist_status(self):
        """Obtener estado actual de la lista negra"""
        return {
            'total_positions_tracked': len(self.clicked_positions),
            'blacklisted_positions': len(self.blacklisted_positions),
            'positions_with_multiple_clicks': sum(1 for count in self.clicked_positions.values() if count > 1)
        }
    
    def print_status_update(self):
        """Imprimir actualización de estado durante ejecución"""
        status = self.get_blacklist_status()
        if status['blacklisted_positions'] > 0:
            print(f"📊 Estado: {status['blacklisted_positions']} checkboxes ignorados, "
                  f"{status['positions_with_multiple_clicks']} con clicks múltiples")
    
    def run(self):
        """Ejecutar automatización"""
        print("\n" + "="*50)
        print("🤖 AUTOMATIZADOR SIMPLE DE CHECKBOXES")
        print("="*50)
        
        # Instrucciones
        print("\n📝 INSTRUCCIONES:")
        print("1. Toma una captura del checkbox y guárdala como 'check.png'")
        print("2. Colócala en la misma carpeta que este script")
        print("3. Posiciona tu navegador/aplicación")
        print("4. El script buscará y clickeará checkboxes automáticamente")
        print("5. Si un checkbox no desaparece tras 2 clicks, será ignorado")
        print("6. Cuando no encuentre más, presionará flecha abajo 15 veces")
        print("7. La lista de checkboxes ignorados se reinicia al desplazarse")
        
        self.setup_controls()
        
        input("\n✅ Presiona ENTER cuando estés listo...")
        
        print("\n⏰ Iniciando en 3 segundos...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("\n🚀 ¡AUTOMATIZACIÓN INICIADA!")
        
        self.running = True
        self.stats['tiempo_inicio'] = datetime.now()
        
        try:
            while self.running:
                # Pausar si está en pausa
                while self.paused and self.running:
                    time.sleep(0.5)
                
                if not self.running:
                    break
                
                # Buscar y clickear checkboxes
                checkboxes_found = self.search_and_click_checkboxes()
                
                if checkboxes_found == 0:
                    self.stats['ciclos_sin_checkboxes'] += 1
                    
                    if self.stats['ciclos_sin_checkboxes'] >= 3:
                        print("📭 No se encontraron checkboxes por 3 ciclos consecutivos")
                        print("⬇️ Desplazando hacia abajo con flechas...")
                        self.advance_page()
                        self.stats['ciclos_sin_checkboxes'] = 0
                    else:
                        print(f"⏳ No se encontraron checkboxes (intento {self.stats['ciclos_sin_checkboxes']}/3)")
                        # Mostrar estado de lista negra si hay posiciones ignoradas
                        self.print_status_update()
                        time.sleep(2)
                else:
                    print(f"✅ Se encontraron y clickearon {checkboxes_found} checkboxes")
                    self.stats['ciclos_sin_checkboxes'] = 0
                
                # Pausa entre ciclos
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n👋 Interrumpido por usuario")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            self.show_stats()
    
    def show_stats(self):
        """Mostrar estadísticas"""
        print(f"\n{'='*50}")
        print("📊 ESTADÍSTICAS")
        print("="*50)
        
        if self.stats['tiempo_inicio']:
            duration = datetime.now() - self.stats['tiempo_inicio']
            print(f"⏰ Duración: {duration}")
        
        print(f"🖱️ Clicks realizados: {self.stats['clicks_realizados']}")
        print(f"🚫 Checkboxes ignorados: {self.stats['checkboxes_blacklisteados']}")
        print(f"⬇️ Desplazamientos realizados: {self.stats['desplazamientos_realizados']}")
        
        # Mostrar información de la lista negra actual
        if len(self.blacklisted_positions) > 0:
            print(f"📋 Posiciones actualmente ignoradas: {len(self.blacklisted_positions)}")
        
        print(f"\n🎉 AUTOMATIZACIÓN COMPLETADA")
        print("💡 Los checkboxes que no desaparecen tras 2 clicks son ignorados automáticamente")

def main():
    """Función principal"""
    try:
        automator = SimpleCheckboxAutomator()
        automator.run()
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    main()
