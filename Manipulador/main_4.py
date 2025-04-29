from motores import MotorNema
from finales_carrera import FinalDeCarrera
import threading
import time
import math
import cv2
import numpy as np
import serial

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

def iniciar_sensor_a010():
    """
    Inicializa el sensor Maix Sense A010 una sola vez.
    MANTIENE LA LÓGICA ORIGINAL QUE FUNCIONA.
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
    
def leer_frame_profundidad():
    """
    Lee un frame de datos de profundidad del sensor A010.
    Devuelve una matriz numpy de tamaño FRAME_HEIGHT x FRAME_WIDTH.
    """
    global SER
    if SER is None or not SER.is_open:
        print("Error: El sensor A010 no está inicializado.")
        return None
        
    while True:
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
            
def detectar_movimiento_a010(motor):
    """
    Detecta movimiento utilizando el sensor de profundidad A010.
    Reemplaza a la función detectar_movimiento_cam().
    """
    global SER, detener_hilo
    detener_hilo.clear()
    
    # Definir región de interés (ROI) - ajustar según la ubicación del sensor
    roi_pts = np.array([(30, 30), (70, 30), (70, 70), (30, 70)], dtype=np.int32)
    
    # Preparar máscara para la región de interés
    def get_mask_from_polygon(shape, polygon):
        mask = np.zeros(shape, dtype=np.uint8)
        return cv2.fillPoly(mask, [polygon], 255)
    
    # Estabilizar la escena (obtener frame de referencia)
    print("Estabilizando la escena...")
    ref_frame = None
    stable_count = 0
    while stable_count < 5:  # Requerir 5 frames estables
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
            
        ref_frame = frame_blur
    
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

    while True:
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
        cv2.imshow('Sensor A010', img_gray)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    if movimiento_detectado:
        print("Movimiento detectado, reiniciando detección.")
        # Resetear el fondo
        return True
    
    return False
    
def perfil_velocidad(motor3):
    """
    Realizando perfil de velocidad
    """
    while not detener_hilo.is_set():
        motor3.mover(direccion=1, pasos=1, retardo=0.0003)

def calcular_distancia(punto1, punto2):
    """Calcula la distancia euclidiana entre dos puntos."""
    return math.sqrt((punto1[0] - punto2[0])**2 + (punto1[1] - punto2[1])**2)

def optimizar_ruta(coordenadas, punto_inicial=(0, 0)):
    """
    Optimiza la ruta para minimizar la distancia total recorrida.
    Usa el algoritmo del vecino más cercano.
    """
    ruta_optimizada = [punto_inicial]
    coordenadas_restantes = coordenadas.copy()

    while coordenadas_restantes:
        punto_actual = ruta_optimizada[-1]
        punto_mas_cercano = min(coordenadas_restantes, 
                                key=lambda x: calcular_distancia(punto_actual, x))
        ruta_optimizada.append(punto_mas_cercano)
        coordenadas_restantes.remove(punto_mas_cercano)

    return ruta_optimizada[1:]  # Excluir el punto inicial

def homing_motor3(motor3, final3):
    """Realiza el homing del motor 3 antes del movimiento en paralelo."""
    print("Realizando homing de motor3...")
    while not final3.esta_activado():
        motor3.mover(direccion=0, pasos=1, retardo=0.0003)
    time.sleep(0.5)
    motor3.mover(direccion=0, pasos=50, retardo=0.0004)
    print("Motor3 homing completado.")
    return True

def homing_en_paralelo(motor1, motor2, final1, final2, final3):
    """Realiza el homing de los motores 1 y 2 en paralelo."""
    resultados_homing = {'motor1': False, 'motor2': False}
    
    def realizar_homing(motor, final_carrera, nombre):
        try:
            direccion_inicial = 1 if nombre == 'motor1' else 0
            velocidad = 0.0008 if nombre == 'motor1' else 0.0003
            pasos_retroceso = 200 if nombre == 'motor1' else 100
            print(f"Iniciando homing de {nombre}...")
            while not final_carrera.esta_activado():
                motor.mover(direccion=direccion_inicial, pasos=1, retardo=velocidad)
            print(f"{nombre} alcanzó el final de carrera.")
            time.sleep(0.5)
            direccion_opuesta = 1 - direccion_inicial
            motor.mover(direccion=direccion_opuesta, pasos=pasos_retroceso, retardo=velocidad)
            resultados_homing[nombre] = True
        except Exception as e:
            print(f"Error en homing de {nombre}: {e}")
            resultados_homing[nombre] = False
    
    thread_motor1 = threading.Thread(target=realizar_homing, args=(motor1, final1, 'motor1'))
    thread_motor2 = threading.Thread(target=realizar_homing, args=(motor2, final2, 'motor2'))

    thread_motor1.start()
    thread_motor2.start()
    thread_motor1.join()
    thread_motor2.join()

    if not all(resultados_homing.values()):
        raise Exception("Homing no completado correctamente")
    
    return True

def cm_a_pasos(coordenada_cm):
    return int(coordenada_cm * PASOS_POR_CM)

def calcular_retardo_motor(paso_actual, total_pasos, retardo_min=0.0004, retardo_max=0.001, porcentaje_aceleracion=0.1):
    umbral_aceleracion = int(total_pasos * porcentaje_aceleracion)
    umbral_desaceleracion = total_pasos - umbral_aceleracion

    if paso_actual < umbral_aceleracion:
        factor = paso_actual / umbral_aceleracion
        retardo = retardo_max - (factor * (retardo_max - retardo_min))
    elif paso_actual > umbral_desaceleracion:
        factor = (paso_actual - umbral_desaceleracion) / umbral_aceleracion
        retardo = retardo_min + (factor * (retardo_max - retardo_min))
    else:
        retardo = retardo_min

    return max(retardo, retardo_min)

def mover_motor_en_paralelo(motor, posicion_actual, posicion_objetivo_cm, rango_max_cm, sentido_giro_1, sentido_giro_2, resultado_movimiento):
    if posicion_objetivo_cm < 0 or posicion_objetivo_cm > rango_max_cm:
        print(f"Error: Coordenada fuera de rango para el motor (0-{rango_max_cm} cm).")
        resultado_movimiento['success'] = False
        return posicion_actual

    pasos_actuales = cm_a_pasos(posicion_actual)
    pasos_objetivo = cm_a_pasos(posicion_objetivo_cm)
    pasos_a_mover = abs(pasos_objetivo - pasos_actuales)
    direccion = sentido_giro_1 if pasos_objetivo > pasos_actuales else sentido_giro_2

    print(f"Moviendo desde {posicion_actual} cm a {posicion_objetivo_cm} cm ({pasos_a_mover} pasos).")

    for paso in range(pasos_a_mover):
        retardo = calcular_retardo_motor(paso, pasos_a_mover)
        motor.mover(direccion=direccion, pasos=1, retardo=retardo)

    resultado_movimiento['success'] = True
    resultado_movimiento['posicion_final'] = posicion_objetivo_cm
    return posicion_objetivo_cm

def ejecutar_recorrido(motor1, motor2, motor3, final1, final2, final3, coordenadas):
    """
    Ejecuta un recorrido completo a través de las coordenadas especificadas.
    """
    try:
        # Homing motor 3 antes de mover los otros motores
        homing_motor3(motor3, final3)

        # Luego homing de motor1 y motor2 en paralelo
        homing_en_paralelo(motor1, motor2, final1, final2, final3)

        posicion_motor1 = 0  
        posicion_motor2 = 0  

        # Optimizar la ruta
        coordenadas_optimizadas = optimizar_ruta(coordenadas)
        print("Ruta optimizada:", coordenadas_optimizadas)

        # Recorrer todas las coordenadas
        for coord_m1, coord_m2 in coordenadas_optimizadas:
            resultado_m1 = {'success': False, 'posicion_final': posicion_motor1}
            resultado_m2 = {'success': False, 'posicion_final': posicion_motor2}

            thread_motor1 = threading.Thread(target=mover_motor_en_paralelo, 
                                            args=(motor1, posicion_motor1, coord_m1, M1_RANGO_MAX_CM, 0, 1, resultado_m1))
            thread_motor2 = threading.Thread(target=mover_motor_en_paralelo, 
                                            args=(motor2, posicion_motor2, coord_m2, M2_RANGO_MAX_CM, 1, 0, resultado_m2))

            thread_motor1.start()
            thread_motor2.start()
            thread_motor1.join()
            thread_motor2.join()

            posicion_motor1 = resultado_m1['posicion_final']
            posicion_motor2 = resultado_m2['posicion_final']

            print(f"Posición alcanzada: Motor1={posicion_motor1} cm, Motor2={posicion_motor2} cm")

            # Detectar movimiento con el motor3
            detectar_movimiento_a010(motor3)
            homing_motor3(motor3, final3)
            time.sleep(1)
            homing_motor3(motor3, final3)

        return True

    except Exception as e:
        print(f"Error durante el recorrido: {e}")
        return False

def main():
    # Inicializar el sensor A010 (una sola vez)
    if not iniciar_sensor_a010():
        print("ERROR: No se pudo conectar al sensor A010.")
        return

    # Inicializar motores y finales de carrera
    motor1 = MotorNema(3, 2, "Motor1")
    motor2 = MotorNema(5, 4, "Motor2")
    motor3 = MotorNema(17, 27, "Motor3")

    final1 = FinalDeCarrera(6, "Final1")
    final2 = FinalDeCarrera(7, "Final2")
    final3 = FinalDeCarrera(8, "Final3")

    # Coordenadas predefinidas
    coordenadas = [(0, 20), (26, 45)]
    
    print("\n=== Sistema de control robótico iniciado ===")
    print("Presione Enter para iniciar un recorrido, o 'q' + Enter para salir")
    
    try:
        while True:
            # Esperar entrada del usuario
            entrada = input("\n> Presione Enter para iniciar recorrido o 'q' para salir: ")
            if entrada.lower() == 'q':
                print("Saliendo del programa...")
                break
                
            print("\n--- Iniciando nuevo recorrido ---")
            exito = ejecutar_recorrido(motor1, motor2, motor3, final1, final2, final3, coordenadas)
            
            if exito:
                print("\n¡Recorrido completado con éxito!")
            else:
                print("\nEl recorrido no se completó correctamente.")

    except KeyboardInterrupt:
        print("\n--------------Programa interrumpido manualmente.--------------")

    except Exception as e:
        print(f"Error en ejecución: {e}")

    finally:
        print("\nVolviendo a home antes de salir...")
        try:
            homing_motor3(motor3, final3)
            homing_en_paralelo(motor1, motor2, final1, final2, final3)

        except Exception as e:
            print(f"Error al volver a home: {e}")

        # Liberar recursos
        motor1.liberar()
        motor2.liberar()
        motor3.liberar()
        
        # Cerrar conexión con el sensor A010
        global SER
        if SER and SER.is_open:
            SER.close()
            print("Conexión con sensor A010 cerrada correctamente.")
            
        # Cerrar ventanas de OpenCV si están abiertas
        cv2.destroyAllWindows()
            
        print("Recursos liberados correctamente.")

if __name__ == "__main__":
    main()