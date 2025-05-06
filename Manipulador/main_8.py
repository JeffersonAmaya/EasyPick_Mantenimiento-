import serial
import time
import cv2
import numpy as np
import os
import subprocess
import glob
from gpiozero import PWMOutputDevice

# Configuración del sensor A010
SENSORES = []  # Lista para almacenar múltiples sensores
BAUDRATE = 115200
TIMEOUT = 2
FRAME_WIDTH = 100
FRAME_HEIGHT = 100
FRAME_SIZE = FRAME_WIDTH * FRAME_HEIGHT
HEADER_SIZE = 16
DIFF_THRESHOLD = 30
PIXEL_CHANGE_LIMIT = 20
MAX_INTENTOS_ESTABILIZACION = 10
MAX_INTENTOS_LECTURA = 5

# Configuración de los pines
RPWM = PWMOutputDevice(19)
LPWM = PWMOutputDevice(18)

class SensorA010:
    """
    Clase para manejar el sensor A010 individualmente
    """
    def __init__(self, puerto, id_sensor=0):
        self.puerto = puerto
        self.id_sensor = id_sensor
        self.ser = None
        self.ultima_lectura = time.time()
        self.frames_leidos = 0
        self.frames_fallidos = 0
        self.conectado = False
        
    def inicializar(self):
        """
        Inicializa la conexión con el sensor
        """
        try:
            # Cerrar si ya está abierto
            if self.ser and self.ser.is_open:
                self.ser.close()
            
            # Liberar el puerto por si está en uso
            try:
                output = subprocess.check_output(['lsof', self.puerto])
                lines = output.decode().split('\n')[1:]
                for line in lines:
                    if line:
                        pid = int(line.split()[1])
                        print(f"Liberando puerto {self.puerto} (PID {pid})")
                        os.kill(pid, 9)
            except:
                pass
                
            # Abrir conexión serial
            self.ser = serial.Serial(self.puerto, BAUDRATE, timeout=TIMEOUT)
            print(f"Sensor {self.id_sensor} inicializado en puerto {self.puerto}.")
            
            # Limpiar buffer
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            # Esperar un momento para estabilizar la conexión
            time.sleep(0.5)
            
            # Enviar comandos de configuración con verificación
            comandos = [
                (b'AT+BAUD=5\r', b'OK'),
                (b'AT+PC=1\r', b'OK'),
                (b'AT+VIDEO=1\r', b'OK'),
                (b'AT+ISP=1\r', b'OK'),
                (b'AT+DISP=3\r', b'OK')
            ]
            
            for cmd, resp_esperada in comandos:
                for intento in range(3):  # Intentar 3 veces cada comando
                    self.ser.write(cmd)
                    time.sleep(0.3)
                    respuesta = self.ser.read_all()
                    if resp_esperada in respuesta:
                        print(f"Comando {cmd} ejecutado correctamente en sensor {self.id_sensor}")
                        break
                    else:
                        print(f"Intento {intento+1}: Comando {cmd} no confirmado. Reintentando...")
                        time.sleep(0.2)
            
            # Verificar la conexión leyendo algunos frames de prueba
            self.conectado = self.verificar_conexion()
            return self.conectado
            
        except Exception as e:
            print(f"Error al inicializar el sensor {self.id_sensor} en {self.puerto}: {e}")
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.conectado = False
            return False
    
    def verificar_conexion(self):
        """
        Verifica que el sensor esté respondiendo correctamente
        """
        print(f"Verificando conexión del sensor {self.id_sensor}...")
        frames_ok = 0
        max_intentos = 10
        
        for i in range(max_intentos):
            frame = self.leer_frame()
            if frame is not None:
                frames_ok += 1
                if frames_ok >= 3:  # Si tenemos 3 frames válidos, consideramos que está conectado
                    print(f"Conexión verificada para sensor {self.id_sensor}. ({frames_ok}/{max_intentos} frames OK)")
                    return True
            time.sleep(0.1)
        
        print(f"No se pudo verificar la conexión del sensor {self.id_sensor}. Solo {frames_ok}/{max_intentos} frames fueron válidos.")
        return False
    
    def leer_frame(self):
        """
        Lee un frame del sensor con reintento y diagnóstico
        """
        if not self.ser or not self.ser.is_open:
            return None
            
        try:
            # Actualizar estadísticas
            self.ultima_lectura = time.time()
            
            # Establecer timeout para evitar bloqueos
            timeout = time.time() + 2
            
            # Limpiar buffer si ha pasado tiempo desde la última lectura
            if self.frames_leidos % 10 == 0:  # Cada 10 frames
                self.ser.reset_input_buffer()
                
            while time.time() < timeout:
                try:
                    # Leer el encabezado
                    header = self.ser.read(2)
                    if len(header) < 2:
                        continue
                        
                    if header == b'\x00\xff':
                        # Leer el tamaño del paquete
                        length_bytes = self.ser.read(2)
                        if len(length_bytes) < 2:
                            continue
                        frame_len = int.from_bytes(length_bytes, 'little')
                        
                        # Verificar que el tamaño sea razonable
                        if frame_len < HEADER_SIZE or frame_len > 20000:
                            print(f"Tamaño de frame inválido: {frame_len}")
                            continue
                        
                        # Leer el resto del paquete
                        frame_data = self.ser.read(frame_len)
                        if len(frame_data) >= HEADER_SIZE + FRAME_SIZE:
                            frame_body = frame_data[HEADER_SIZE:HEADER_SIZE + FRAME_SIZE]
                            self.frames_leidos += 1
                            
                            # Convertir a imagen numpy
                            frame = np.frombuffer(frame_body, dtype=np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH))
                            
                            # Verificar que el frame es válido (no todo negro o blanco)
                            if np.mean(frame) > 5 and np.mean(frame) < 250:
                                return frame
                            else:
                                print(f"Frame descartado: valores anómalos (media={np.mean(frame):.2f})")
                                self.frames_fallidos += 1
                                
                except serial.SerialException as se:
                    print(f"Error de comunicación serial en sensor {self.id_sensor}: {se}")
                    self.frames_fallidos += 1
                    break
            
            # Si llegamos aquí, no se pudo leer un frame válido
            self.frames_fallidos += 1
            return None
            
        except Exception as e:
            print(f"Error al leer frame del sensor {self.id_sensor}: {e}")
            self.frames_fallidos += 1
            return None
    
    def cerrar(self):
        """
        Cierra la conexión del sensor
        """
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
                print(f"Sensor {self.id_sensor} en puerto {self.puerto} cerrado correctamente.")
            self.conectado = False
        except Exception as e:
            print(f"Error al cerrar el sensor {self.id_sensor}: {e}")
    
    def obtener_estado(self):
        """
        Devuelve un resumen del estado del sensor
        """
        error_rate = 0
        if (self.frames_leidos + self.frames_fallidos) > 0:
            error_rate = self.frames_fallidos / (self.frames_leidos + self.frames_fallidos) * 100
            
        return {
            "id": self.id_sensor,
            "puerto": self.puerto,
            "conectado": self.conectado,
            "frames_leidos": self.frames_leidos,
            "frames_fallidos": self.frames_fallidos,
            "tasa_error": error_rate,
            "ultima_lectura": self.ultima_lectura
        }

# Funciones para manejo de sensores
def listar_puertos_usb():
    puertos = glob.glob('/dev/sensor_*')
    return puertos

def reiniciar_puertos():
    try:
        print("Reiniciando puertos USB...")
        subprocess.run(["sudo", "uhubctl", "-l", "1-1", "-a", "cycle"], check=False)
        print("Esperando a que los puertos se reinicien...")
        time.sleep(5)
        print("Puertos USB reiniciados.")
        return True
    except Exception as e:
        print(f"Error al reiniciar puertos USB: {e}")
        print("Intentando alternativa...")
        try:
            # Alternativa si uhubctl no está disponible
            subprocess.run(["sudo", "modprobe", "-r", "ehci_hcd"], check=False)
            time.sleep(2)
            subprocess.run(["sudo", "modprobe", "ehci_hcd"], check=False)
            time.sleep(5)
            print("Puertos USB reiniciados usando modprobe.")
            return True
        except Exception as e2:
            print(f"Error al reiniciar puertos usando método alternativo: {e2}")
            return False

def cerrar_todos_sensores():
    """
    Cierra todas las conexiones de sensores
    """
    global SENSORES
    for sensor in SENSORES:
        sensor.cerrar()
    SENSORES.clear()
    return True

def inicializar_sensor(puerto, id_sensor=0):
    """
    Inicializa un nuevo sensor A010
    """
    # Primero comprobar si ya hay un sensor con ese puerto
    for sensor in SENSORES:
        if sensor.puerto == puerto:
            print(f"Ya existe un sensor en el puerto {puerto}. Cerrándolo primero.")
            sensor.cerrar()
            SENSORES.remove(sensor)
            break
    
    # Crear y añadir el nuevo sensor
    nuevo_sensor = SensorA010(puerto, id_sensor)
    if nuevo_sensor.inicializar():
        SENSORES.append(nuevo_sensor)
        return nuevo_sensor
    return None

def probar_sensor(sensor, mostrar_frames=True):
    """
    Prueba un sensor específico
    """
    if not sensor or not sensor.conectado:
        print("El sensor no está conectado o inicializado.")
        return False
    
    print(f"\n--- PRUEBA DEL SENSOR {sensor.id_sensor} ---")
    print("Intentando capturar y mostrar frames del sensor...")
    
    frames_capturados = 0
    max_frames = 30
    start_time = time.time()
    window_name = f"Sensor {sensor.id_sensor}"
    
    try:
        if mostrar_frames:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        while frames_capturados < max_frames:
            frame = sensor.leer_frame()
            
            if frame is not None:
                frames_capturados += 1
                
                if mostrar_frames:
                    # Mejorar la visualización
                    frame_norm = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
                    frame_colored = cv2.applyColorMap(frame_norm, cv2.COLORMAP_JET)
                    
                    # Añadir información
                    cv2.putText(frame_colored, f"Frame: {frames_capturados}/{max_frames}", (10, 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame_colored, f"Sensor ID: {sensor.id_sensor}", (10, 40), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    cv2.imshow(window_name, frame_colored)
                    key = cv2.waitKey(100)
                    if key == 27:  # ESC para salir
                        break
                
                print(f"Frame {frames_capturados}/{max_frames} capturado. Media: {np.mean(frame):.2f}, Min: {np.min(frame)}, Max: {np.max(frame)}")
            
            else:
                print(f"No se pudo capturar el frame {frames_capturados+1}.")
                time.sleep(0.1)
            
            # Si tarda más de 20 segundos, abortamos
            if time.time() - start_time > 20:
                print("Tiempo de prueba excedido.")
                break
        
        fps = frames_capturados / (time.time() - start_time)
        print(f"\nPrueba completada: {frames_capturados} frames capturados a {fps:.2f} FPS")
        
        # Evaluar resultado
        if frames_capturados >= max_frames * 0.8:  # 80% o más frames capturados correctamente
            print("RESULTADO: El sensor funciona correctamente.")
            resultado = True
        elif frames_capturados >= max_frames * 0.3:  # Entre 30% y 80%
            print("RESULTADO: El sensor funciona con algunos problemas de estabilidad.")
            resultado = True
        else:
            print("RESULTADO: El sensor no funciona correctamente.")
            resultado = False
        
        if mostrar_frames:
            # Mantener la ventana abierta hasta que se presione una tecla
            print("Presione cualquier tecla para continuar...")
            cv2.waitKey(0)
            cv2.destroyWindow(window_name)
        
        return resultado
    
    except Exception as e:
        print(f"Error durante la prueba del sensor: {e}")
        if mostrar_frames:
            cv2.destroyWindow(window_name)
        return False

def probar_todos_sensores():
    """
    Prueba todos los sensores conectados
    """
    if not SENSORES:
        print("No hay sensores inicializados.")
        return False
    
    resultados = []
    for sensor in SENSORES:
        print(f"\nProbando sensor {sensor.id_sensor} en puerto {sensor.puerto}...")
        resultado = probar_sensor(sensor)
        resultados.append(resultado)
        time.sleep(1)
    
    # Mostrar resumen
    print("\n--- RESUMEN DE PRUEBAS ---")
    for i, sensor in enumerate(SENSORES):
        estado = sensor.obtener_estado()
        print(f"Sensor {estado['id']} en {estado['puerto']}: {'OK' if resultados[i] else 'FALLO'}")
        print(f"  - Frames leídos: {estado['frames_leidos']}")
        print(f"  - Frames fallidos: {estado['frames_fallidos']}")
        print(f"  - Tasa de error: {estado['tasa_error']:.2f}%")
    
    return all(resultados)

def menu_principal():
    """
    Muestra un menú para seleccionar el puerto y realizar pruebas.
    """
    while True:
        print("\n----- SISTEMA DE PRUEBA DE SENSORES A010 -----")
        print(f"Sensores activos: {len(SENSORES)}")
        for i, sensor in enumerate(SENSORES):
            estado = sensor.obtener_estado()
            print(f"  {i+1}. Sensor {estado['id']} en {estado['puerto']} - {'Conectado' if estado['conectado'] else 'Desconectado'}")
        
        print("\nOpciones:")
        print("1. Listar puertos USB disponibles")
        print("2. Inicializar nuevo sensor")
        print("3. Probar sensor específico")
        print("4. Probar todos los sensores")
        print("5. Cerrar un sensor")
        print("6. Cerrar todos los sensores")
        print("7. Diagnosticar problemas de conexión")
        print("8. Reiniciar puertos USB")
        print("0. Salir")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == "1":
            puertos = listar_puertos_usb()
            if puertos:
                print("\nPuertos USB disponibles:")
                for i, puerto in enumerate(puertos):
                    print(f"{i+1}. {puerto}")
            else:
                print("No se encontraron puertos USB disponibles.")
                
        elif opcion == "2":
            puertos = listar_puertos_usb()
            if not puertos:
                print("No se encontraron puertos USB disponibles.")
                continue
                
            print("\nPuertos USB disponibles:")
            for i, puerto in enumerate(puertos):
                print(f"{i+1}. {puerto}")
                
            seleccion = input("\nSeleccione un puerto (número): ")
            try:
                indice = int(seleccion) - 1
                if 0 <= indice < len(puertos):
                    puerto_seleccionado = puertos[indice]
                    id_sensor = len(SENSORES) + 1
                    print(f"\nIniciando sensor {id_sensor} en puerto {puerto_seleccionado}...")
                    
                    sensor = inicializar_sensor(puerto_seleccionado, id_sensor)
                    if sensor:
                        preguntar = input("¿Desea probar el sensor ahora? (s/n): ")
                        if preguntar.lower() == 's':
                            probar_sensor(sensor)
                else:
                    print("Número de puerto inválido.")
            except ValueError:
                print("Por favor, ingrese un número válido.")
                
        elif opcion == "3":
            if not SENSORES:
                print("No hay sensores inicializados.")
                continue
                
            print("\nSensores disponibles:")
            for i, sensor in enumerate(SENSORES):
                estado = sensor.obtener_estado()
                print(f"{i+1}. Sensor {estado['id']} en {estado['puerto']}")
                
            seleccion = input("\nSeleccione un sensor (número): ")
            try:
                indice = int(seleccion) - 1
                if 0 <= indice < len(SENSORES):
                    probar_sensor(SENSORES[indice])
                else:
                    print("Número de sensor inválido.")
            except ValueError:
                print("Por favor, ingrese un número válido.")
                
        elif opcion == "4":
            probar_todos_sensores()
                
        elif opcion == "5":
            if not SENSORES:
                print("No hay sensores para cerrar.")
                continue
                
            print("\nSensores disponibles:")
            for i, sensor in enumerate(SENSORES):
                estado = sensor.obtener_estado()
                print(f"{i+1}. Sensor {estado['id']} en {estado['puerto']}")
                
            seleccion = input("\nSeleccione un sensor para cerrar (número): ")
            try:
                indice = int(seleccion) - 1
                if 0 <= indice < len(SENSORES):
                    sensor = SENSORES.pop(indice)
                    sensor.cerrar()
                    print(f"Sensor {sensor.id_sensor} cerrado y eliminado.")
                else:
                    print("Número de sensor inválido.")
            except ValueError:
                print("Por favor, ingrese un número válido.")
                
        elif opcion == "6":
            cerrar_todos_sensores()
            print("Todos los sensores han sido cerrados.")
                
        elif opcion == "7":
            diagnosticar_problemas_conexion()
                
        elif opcion == "8":
            print("Reiniciando puertos...")
            cerrar_todos_sensores()  # Cerrar sensores antes de reiniciar
            reiniciar_puertos()
            print("Reinicio completo.")
                
        elif opcion == "0":
            print("Saliendo del programa...")
            cerrar_todos_sensores()
            break
             
        else:
            print("Opción no válida. Intente de nuevo.")

def diagnosticar_problemas_conexion():
    """
    Función para diagnosticar problemas comunes de conexión
    """
    print("\n--- DIAGNÓSTICO DE PROBLEMAS DE CONEXIÓN ---")
    
    # 1. Verificar puertos disponibles
    puertos = listar_puertos_usb()
    if not puertos:
        print("PROBLEMA DETECTADO: No hay puertos USB disponibles.")
        print("Soluciones posibles:")
        print("- Verifique que los sensores estén conectados físicamente")
        print("- Pruebe en otro puerto USB")
        print("- Reinicie el dispositivo")
        print("- Verifique los permisos de usuario para acceder a los puertos")
        return
    
    print(f"OK: Se encontraron {len(puertos)} puertos USB: {', '.join(puertos)}")
    
    # 2. Verificar permisos
    try:
        for puerto in puertos:
            proceso = subprocess.run(['ls', '-l', puerto], capture_output=True, text=True)
            salida = proceso.stdout.strip()
            print(f"Permisos para {puerto}: {salida}")
            
            if 'dialout' in salida and os.getuid() != 0:
                usuario = subprocess.run(['whoami'], capture_output=True, text=True).stdout.strip()
                grupos = subprocess.run(['groups', usuario], capture_output=True, text=True).stdout.strip()
                
                if 'dialout' not in grupos:
                    print("PROBLEMA DETECTADO: El usuario actual no pertenece al grupo 'dialout'")
                    print("Solución:")
                    print("  sudo usermod -a -G dialout $USER")
                    print("  (Necesitará cerrar sesión y volver a iniciarla)")
    except Exception as e:
        print(f"Error al verificar permisos: {e}")
    
    # 3. Verificar si el kernel reconoce los dispositivos
    try:
        proceso = subprocess.run(['dmesg', '|', 'grep', 'ttyUSB'], shell=True, capture_output=True, text=True)
        salida = proceso.stdout.strip()
        if salida:
            print("\nRegistros del kernel relacionados con dispositivos USB:")
            print(salida)
    except Exception as e:
        print(f"Error al obtener registros del kernel: {e}")
    
    # 4. Verificar carga del driver
    try:
        proceso = subprocess.run(['lsmod', '|', 'grep', 'cp210x'], shell=True, capture_output=True, text=True)
        if proceso.stdout.strip():
            print("\nOK: Driver CP210x cargado correctamente")
        else:
            print("\nPROBLEMA DETECTADO: Driver CP210x no parece estar cargado")
            print("Solución:")
            print("  sudo modprobe cp210x")
    except Exception as e:
        print(f"Error al verificar driver: {e}")
    
    # 5. Sugerencias generales
    print("\nRECOMENDACIONES GENERALES:")
    print("1. Si los sensores funcionan intermitentemente, puede ser un problema de alimentación.")
    print("   - Utilice un hub USB con alimentación externa")
    print("   - Evite cables USB largos o de baja calidad")
    print("2. Si un sensor deja de funcionar cuando conecta otro:")
    print("   - Puede haber conflicto de recursos")
    print("   - Pruebe a conectarlos en puertos USB de diferentes controladores")
    print("3. Si los sensores se detectan pero luego fallan:")
    print("   - Pruebe a reiniciar los puertos USB")
    print("   - Verifique la velocidad de transmisión")
    
    print("\nDiagnóstico completo.")

def main():
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n--------------Programa interrumpido manualmente.--------------")
    except Exception as e:
        print(f"\n--------------Error inesperado: {e}--------------")
    finally:
        # Cerrar todas las ventanas de OpenCV
        cv2.destroyAllWindows()
        # Cerrar conexiones con los sensores
        cerrar_todos_sensores()
        print("Recursos liberados correctamente.")

if __name__ == "__main__":
    main()

# sudo nano /etc/udev/rules.d/99-ftdi-sensors.rules

# # Sensor 1
# SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6010", ATTRS{serial}=="202206 48535F", SYMLINK+="sensor_1"

# # Sensor 2
# SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6010", ATTRS{serial}=="202206 C86F5F", SYMLINK+="sensor_2"
