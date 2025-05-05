from motores import MotorNema
from finales_carrera import FinalDeCarrera
import threading
import time
import math
import cv2
import numpy as np
import serial
from gpiozero import PWMOutputDevice

# Configuración del sensor A010
SER = None  # Variable global para la conexión serial
PORT = '/dev/ttyUSB0'  # Mantener el puerto original
BAUDRATE = 115200
TIMEOUT = 2
FRAME_WIDTH = 100
FRAME_HEIGHT = 100
FRAME_SIZE = FRAME_WIDTH * FRAME_HEIGHT
HEADER_SIZE = 16
DIFF_THRESHOLD = 30
PIXEL_CHANGE_LIMIT = 20
PASOS_POR_CM = 100  
M1_RANGO_MAX_CM = 100
M2_RANGO_MAX_CM = 100
detener_hilo = threading.Event()
MAX_INTENTOS_ESTABILIZACION = 10  # Número máximo de intentos para estabilizar el sensor

# Configuración de los pines
RPWM = PWMOutputDevice(19)
LPWM = PWMOutputDevice(18)

def iniciar_sensor_a010():
    """
    Inicializa el sensor Maix Sense A010 una sola vez.
    """
    global SER
    try:
        # Liberar el puerto por si está en uso
        try:
            import subprocess
            import os
            output = subprocess.check_output(['lsof', PORT])
            lines = output.decode().split('\n')[1:]
            for line in lines:
                if line:
                    pid = int(line.split()[1])
                    print(f"Liberando puerto {PORT} (PID {pid})")
                    os.kill(pid, 9)
        except:
            pass
            
        # Abrir conexión serial
        SER = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
        print("Sensor de profundidad A010 inicializado correctamente.")
        
        # Enviar comandos de configuración
        commands = [
            b'AT+BAUD=5\r',
            b'AT+PC=1\r',
            b'AT+VIDEO=1\r',
            b'AT+ISP=1\r',
            b'AT+DISP=3\r'
        ]
        for cmd in commands:
            SER.write(cmd)
            time.sleep(0.2)
            SER.read_all()
            
        # Verificar que el sensor esté listo
        print("Sensor A010 listo para su uso.")
        return True
    except Exception as e:
        print(f"Error al inicializar el sensor A010: {e}")
        return False
    
def probar_sensor_a010(solo_conectividad=True):
    """
    Realiza una prueba del sensor A010 para verificar su funcionamiento.
    Si solo_conectividad=True, solo verifica que el sensor esté conectado.
    Si solo_conectividad=False, realiza una prueba completa de detección de movimiento.
    """
    global SER
    print("Iniciando prueba del sensor A010...")
    
    if SER is None or not SER.is_open:
        print("Error: El sensor A010 no está inicializado.")
        return False
    
    # Prueba básica de conectividad
    # Intentar leer varios frames
    frames_capturados = 0
    frames_necesarios = 5
    frames = []
    
    print(f"Intentando capturar {frames_necesarios} frames para verificar el sensor...")
    
    # Limpiar buffer
    SER.read_all()
    
    timeout_start = time.time()
    while frames_capturados < frames_necesarios:
        if time.time() - timeout_start > 10:  # Timeout de 10 segundos
            print("Tiempo de espera agotado. El sensor podría no estar funcionando correctamente.")
            return False
            
        frame = leer_frame_profundidad()
        if frame is not None:
            frames.append(frame)
            frames_capturados += 1
            print(f"Frame {frames_capturados}/{frames_necesarios} capturado.")
            
            # Mostrar el frame para debug visual
            cv2.imshow('Prueba Sensor A010', frame)
            cv2.waitKey(500)  # Esperar 500ms
        
        time.sleep(0.1)
    
    # Analizar estadísticas básicas de los frames
    if frames:
        promedio_intensidad = np.mean([np.mean(f) for f in frames])
        desviacion = np.std([np.mean(f) for f in frames])
        print(f"Estadísticas del sensor: Intensidad promedio={promedio_intensidad:.2f}, Desviación={desviacion:.2f}")
        
        # Verificar si las estadísticas son razonables
        conectividad_ok = promedio_intensidad > 5 and desviacion < 50
        
        if not conectividad_ok:
            print("El sensor A010 muestra valores anómalos. Verifique su posición o conexión.")
            return False
        else:
            print("El sensor A010 está conectado correctamente.")
            
            # Si solo queríamos verificar la conectividad, terminamos aquí
            if solo_conectividad:
                return True
                
            # Prueba de detección de movimiento
            return probar_deteccion_movimiento()
    
    print("No se pudieron capturar suficientes frames. Verifique la conexión del sensor.")
    return False

def probar_deteccion_movimiento():
    """
    Prueba la capacidad de detección de movimiento del sensor A010 sin activar el motor3.
    """
    print("\n--- PRUEBA DE DETECCIÓN DE MOVIMIENTO ---")
    print("Por favor, mueva un objeto frente al sensor para probar la detección.")
    print("El sistema esperará hasta detectar movimiento para continuar.")
    
    # Definir ROI y preparar máscara
    roi_pts = np.array([(30, 30), (70, 30), (70, 70), (30, 70)], dtype=np.int32)
    
    def get_mask_from_polygon(shape, polygon):
        mask = np.zeros(shape, dtype=np.uint8)
        return cv2.fillPoly(mask, [polygon], 255)
    
    # Estabilizar la escena para tener un frame de referencia
    print("Estabilizando la escena para prueba de detección...")
    ref_frame = None
    stable_count = 0
    intentos = 0
    tiempo_inicio_estabilizacion = time.time()
    
    while stable_count < 5 and intentos < MAX_INTENTOS_ESTABILIZACION and (time.time() - tiempo_inicio_estabilizacion < 15):
        intentos += 1
        frame = leer_frame_profundidad()
        if frame is None:
            continue
            
        frame_blur = cv2.GaussianBlur(frame, (3, 3), 0)
        
        if ref_frame is None:
            ref_frame = frame_blur
            continue
            
        # Calcular diferencia con frame anterior
        diff = cv2.absdiff(ref_frame, frame_blur)
        diff_mask = get_mask_from_polygon(diff.shape, roi_pts)
        diff_roi = cv2.bitwise_and(diff, diff, mask=diff_mask)
        _, diff_thresh = cv2.threshold(diff_roi, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)
        changes = cv2.countNonZero(diff_thresh)
        
        if changes < PIXEL_CHANGE_LIMIT:
            stable_count += 1
            print(f"Frame estable {stable_count}/5")
        else:
            stable_count = 0
            print(f"Reseteo de estabilización. Intento {intentos}/{MAX_INTENTOS_ESTABILIZACION}")
            
        ref_frame = frame_blur
        
        # Mostrar frame actual con ROI
        img_display = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        cv2.polylines(img_display, [roi_pts], isClosed=True, color=(0, 255, 0), thickness=1)
        cv2.putText(img_display, "Estabilizando...", (10, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow('Prueba Detección', img_display)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC para salir
            print("Prueba cancelada por el usuario.")
            return False
    
    if stable_count < 5:
        print("No se pudo estabilizar la escena. Continuando con la mejor referencia disponible.")
        
    # Crear máscara para la ROI
    mask_roi = get_mask_from_polygon(ref_frame.shape, roi_pts)
    
    # Monitorear movimiento
    tiempo_inicio = time.time()
    tiempo_maximo = 60  # Tiempo máximo de espera: 60 segundos
    movimiento_detectado = False
    detecciones_contador = 0
    
    print("\nEsperando detección de movimiento. Mueva un objeto frente al sensor...")
    print("Presione ESC para cancelar la prueba.")
    
    while time.time() - tiempo_inicio < tiempo_maximo:
        tiempo_transcurrido = int(time.time() - tiempo_inicio)
        tiempo_restante = tiempo_maximo - tiempo_transcurrido
        
        frame = leer_frame_profundidad()
        if frame is None:
            continue
            
        frame_blur = cv2.GaussianBlur(frame, (3, 3), 0)
        
        # Aplicar ROI
        roi_ref = cv2.bitwise_and(ref_frame, ref_frame, mask=mask_roi)
        roi_now = cv2.bitwise_and(frame_blur, frame_blur, mask=mask_roi)
        
        # Calcular diferencia
        diff = cv2.absdiff(roi_ref, roi_now)
        _, diff_thresh = cv2.threshold(diff, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)
        num_changes = cv2.countNonZero(diff_thresh)
        
        # Verificar si hay movimiento
        if num_changes > PIXEL_CHANGE_LIMIT:
            detecciones_contador += 1
            print(f"Movimiento detectado ({detecciones_contador}/3)")
            
            if detecciones_contador >= 3:  # Requerir 3 detecciones para confirmación
                print("\n¡MOVIMIENTO CONFIRMADO! Prueba de detección exitosa.")
                movimiento_detectado = True
                break
        
        # Mostrar visualización
        img_display = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        cv2.polylines(img_display, [roi_pts], isClosed=True, color=(0, 255, 0), thickness=1)
        
        estado = "MOVIMIENTO DETECTADO" if num_changes > PIXEL_CHANGE_LIMIT else "Esperando movimiento..."
        color = (0, 0, 255) if num_changes > PIXEL_CHANGE_LIMIT else (0, 255, 0)
        
        cv2.putText(img_display, f"Tiempo restante: {tiempo_restante}s", (10, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(img_display, estado, (10, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        cv2.putText(img_display, f"Cambios: {num_changes}/{PIXEL_CHANGE_LIMIT}", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Mostrar la máscara de diferencia para mejor visualización
        diff_display = cv2.cvtColor(diff_thresh, cv2.COLOR_GRAY2BGR)
        combined = np.hstack((img_display, diff_display))
        cv2.imshow('Prueba Detección', combined)
        
        if cv2.waitKey(1) & 0xFF == 27:  # ESC para salir
            print("Prueba cancelada por el usuario.")
            return False
    
    cv2.destroyWindow('Prueba Detección')
    
    if movimiento_detectado:
        return True
    else:
        print("\nTiempo agotado. No se detectó movimiento suficiente durante la prueba.")
        return False
    
def leer_frame_profundidad():
    """
    Lee un frame de datos de profundidad del sensor A010.
    Devuelve una matriz numpy de tamaño FRAME_HEIGHT x FRAME_WIDTH.
    """
    global SER
    if SER is None or not SER.is_open:
        print("Error: El sensor A010 no está inicializado.")
        return None
        
    try:
        # Establecer timeout para evitar bloqueos indefinidos
        timeout = time.time() + 2  # 2 segundos timeout
        
        while time.time() < timeout:
            header = SER.read(2)
            if header == b'\x00\xff':
                length_bytes = SER.read(2)
                if len(length_bytes) < 2:
                    continue
                frame_len = int.from_bytes(length_bytes, 'little')
                frame_data = SER.read(frame_len)
                if len(frame_data) >= HEADER_SIZE + FRAME_SIZE:
                    frame_body = frame_data[HEADER_SIZE:HEADER_SIZE + FRAME_SIZE]
                    return np.frombuffer(frame_body, dtype=np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH))
        
        # Si llegamos aquí, no se pudo leer un frame completo
        print("Tiempo de espera agotado al leer frame del sensor.")
        return None
    except Exception as e:
        print(f"Error al leer frame de profundidad: {e}")
        return None
            
def detectar_movimiento_a010(motor):
    """
    Detecta movimiento utilizando el sensor de profundidad A010.
    Con mejoras en la estabilización.
    """
    global SER, detener_hilo
    detener_hilo.clear()
    
    # Definir región de interés (ROI) - ajustar según la ubicación del sensor
    roi_pts = np.array([(30, 30), (70, 30), (70, 70), (30, 70)], dtype=np.int32)
    
    # Preparar máscara para la región de interés
    def get_mask_from_polygon(shape, polygon):
        mask = np.zeros(shape, dtype=np.uint8)
        return cv2.fillPoly(mask, [polygon], 255)
    
    # Estabilizar la escena (obtener frame de referencia) con control de intentos
    print("Estabilizando la escena...")
    ref_frame = None
    stable_count = 0
    intentos = 0
    
    while stable_count < 5 and intentos < MAX_INTENTOS_ESTABILIZACION:  # Requerir 5 frames estables con límite de intentos
        intentos += 1
        frame = leer_frame_profundidad()
        if frame is None:
            print(f"No se pudo leer frame en intento {intentos}")
            time.sleep(0.2)
            continue
            
        frame_blur = cv2.GaussianBlur(frame, (3, 3), 0)
        
        if ref_frame is None:
            ref_frame = frame_blur
            continue
            
        # Calcular diferencia con frame anterior
        diff = cv2.absdiff(ref_frame, frame_blur)
        diff_mask = get_mask_from_polygon(diff.shape, roi_pts)
        diff_roi = cv2.bitwise_and(diff, diff, mask=diff_mask)
        _, diff_thresh = cv2.threshold(diff_roi, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)
        changes = cv2.countNonZero(diff_thresh)
        
        if changes < PIXEL_CHANGE_LIMIT:
            stable_count += 1
            print(f"Frame estable {stable_count}/5")
        else:
            stable_count = 0
            print(f"Reseteo de estabilización. Intento {intentos}/{MAX_INTENTOS_ESTABILIZACION}")
            
        ref_frame = frame_blur
    
    # Verificar si se logró la estabilización
    if stable_count < 5:
        print("¡ADVERTENCIA! No se pudo estabilizar la escena después de múltiples intentos.")
        print("Continuando con la mejor referencia disponible...")
    
    # Iniciar hilo de control del motor
    print("Detector de movimiento iniciado.")
    time.sleep(1)
    hilo_velocidad = threading.Thread(target=perfil_velocidad, args=(motor,))
    hilo_velocidad.start()
    
    # Máscara ROI
    mask_roi = get_mask_from_polygon(ref_frame.shape, roi_pts)
    
    # Monitorear movimiento
    movimiento_detectado = False
    detecciones_contador = 0
    tiempo_inicio = time.time()
    tiempo_maximo = 30  # Tiempo máximo de espera en segundos

    while time.time() - tiempo_inicio < tiempo_maximo:
        frame = leer_frame_profundidad()
        if frame is None:
            continue
            
        frame_blur = cv2.GaussianBlur(frame, (3, 3), 0)
        
        # Aplicar ROI
        roi_ref = cv2.bitwise_and(ref_frame, ref_frame, mask=mask_roi)
        roi_now = cv2.bitwise_and(frame_blur, frame_blur, mask=mask_roi)
        
        # Calcular diferencia
        diff = cv2.absdiff(roi_ref, roi_now)
        _, diff_thresh = cv2.threshold(diff, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)
        num_changes = cv2.countNonZero(diff_thresh)

        # Dentro del bucle while
        if num_changes > PIXEL_CHANGE_LIMIT:
            detecciones_contador += 1
            print(f"Movimiento detectado ({detecciones_contador}/2)")
            
            if detecciones_contador >= 2:
                print("Movimiento confirmado: Detener eyector.")
                movimiento_detectado = True
                detener_hilo.set()
                hilo_velocidad.join()
                detener_hilo.clear()
                break
            
        # Opcional: Mostrar visualización para debug
        img_gray = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        cv2.polylines(img_gray, [roi_pts], isClosed=True, color=(0, 255, 0), thickness=1)
        cv2.putText(img_gray, f"Tiempo: {int(time.time() - tiempo_inicio)}s", (10, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow('Sensor A010', img_gray)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    # Si se agotó el tiempo, detener el hilo de velocidad
    if not movimiento_detectado:
        print(f"Tiempo máximo de detección ({tiempo_maximo}s) alcanzado. Deteniendo motor.")
        detener_hilo.set()
        hilo_velocidad.join()
        detener_hilo.clear()
    
    if movimiento_detectado:
        print("Movimiento detectado, reiniciando detección.")
        return True
    
    return False
    
def perfil_velocidad(motor3):
    """
    Realizando perfil de velocidad
    """
    while not detener_hilo.is_set():
        motor3.mover(direccion=1, pasos=1, retardo=0.0008)


def extender_actuador(velocidad):
    """
    Extiende el actuador lineal.
    :param velocidad: Velocidad de extensión (0.0 a 1.0).
    """
    print(f"Extendiendo actuador con velocidad {velocidad}")
    RPWM.value = 0
    LPWM.value = velocidad
    time.sleep(1.9)  #1.9 Ajusta el tiempo según lo necesario    parar_actuador()


def main():

    try:

        if not iniciar_sensor_a010():
            print("ERROR: No se pudo conectar al sensor A010.")
            return
        
        extender_actuador(1)

        # Primero realizar prueba de conectividad básica del sensor

        print("\n--- REALIZANDO PRUEBA DE CONECTIVIDAD DEL SENSOR A010 ---")

        if not probar_sensor_a010(solo_conectividad=True):
            respuesta = input("¿Desea continuar a pesar del error en el sensor? (s/n): ")
            if respuesta.lower() != 's':
                print("Saliendo del programa debido a fallo en el sensor.")
                return
    

    except KeyboardInterrupt:
        print("\n--------------Programa interrumpido manualmente.--------------")

    finally:
    
        # Cerrar conexión con el sensor A010

        global SER

        if SER and SER.is_open:
            SER.close()
            print("Conexión con sensor A010 cerrada correctamente.")
            
        print("Recursos liberados correctamente.")

if __name__ == "__main__":
    main() 