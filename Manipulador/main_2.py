from motores import MotorNema
from finales_carrera import FinalDeCarrera
from deteccion_2 import detectar_movimiento
import threading
import time
import math
import cv2
import numpy as np

PASOS_POR_CM = 100  
M1_RANGO_MAX_CM = 100
M2_RANGO_MAX_CM = 100

detener_hilo= threading.Event()


def perfil_velocidad(motor3):
    """
    Realizando perfil de velocidad
    """

    while not detener_hilo.is_set():
        motor3.mover(direccion=1, pasos=1, retardo=0.0003)

def iniciar_camara():
    global cap
    cap = cv2.VideoCapture("/dev/video0")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
            print("Error: No se pudo abrir la cámara.")
            return

def resetear_fondo(fgbg, cap, area_pts, num_frames=30):
    for _ in range(num_frames):
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        imAux = np.zeros(shape=(frame.shape[:2]), dtype=np.uint8)
        imAux = cv2.drawContours(imAux, [area_pts], -1, (255), -1)
        image_area = cv2.bitwise_and(gray, gray, mask=imAux)
        fgbg.apply(image_area, learningRate=0.5)  # Forzamos el aprendizaje rápido

def detectar_movimiento_cam(motor):
        
        global detener_hilo
        detener_hilo.clear()

        ret, frame = cap.read()
        area_pts = np.array([(165, 193), (632, 266), (622, 362), (169, 256), (163, 195)])
        
        try:
            fgbg = cv2.bgsegm.createBackgroundSubtractorMOG()
        except AttributeError:
            try:
                fgbg = cv2.createBackgroundSubtractorMOG2()
            except:
                print("Error: No se pudo crear el sustractor de fondo.")
                return

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

        print("Detector de movimiento iniciado. Presiona 'ESC' para salir.")
        print("Detector de movimiento iniciado. Presiona 'ESC' para salir.")
        hilo_velocidad = threading.Thread(target=perfil_velocidad, args=(motor,))
        print("Iniciando hilo de velocidad...")
        hilo_velocidad.start()

        movimiento_detectado = False
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: No se pudo capturar frame.")
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
            color = (0, 255, 0)
            texto_estado = "Estado: No se ha detectado movimiento"

            imAux = np.zeros(shape=(frame.shape[:2]), dtype=np.uint8)
            imAux = cv2.drawContours(imAux, [area_pts], -1, (255), -1)
            image_area = cv2.bitwise_and(gray, gray, mask=imAux)

            fgmask = fgbg.apply(image_area)
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
            fgmask = cv2.dilate(fgmask, None, iterations=2)

            contornos = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            cnts = contornos[0] if len(contornos) == 2 else contornos[1]
            #print("contornos 1:",cnts)
            for cnt in cnts:
                if cv2.contourArea(cnt) > 500:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    print("Movimiento detectado: Detener eyector.")
                    #cap.release()
                    #cv2.destroyAllWindows()
                    movimiento_detectado = True
                    detener_hilo.set()
                    hilo_velocidad.join()
                    detener_hilo.clear()
                    break
            if movimiento_detectado:
                print("Movimiento detectado.")
                resetear_fondo(fgbg, cap, area_pts)
                return True


            cv2.drawContours(frame, [area_pts], -1, color, 2)
            cv2.putText(frame, texto_estado, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            cv2.imshow('Detector de Movimiento', frame)

            if cv2.waitKey(30) & 0xFF == 27:
                break

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

def main():

    iniciar_camara()

    motor1 = MotorNema(3, 2, "Motor1")
    motor2 = MotorNema(5, 4, "Motor2")
    motor3 = MotorNema(17, 27, "Motor3")

    final1 = FinalDeCarrera(6, "Final1")
    final2 = FinalDeCarrera(7, "Final2")
    final3 = FinalDeCarrera(8, "Final3")

    coordenadas = [(0, 20), (26, 45)]

    coordenadas_optimizadas = optimizar_ruta(coordenadas)
    print("Ruta optimizada:", coordenadas_optimizadas)

    try:
        # Homing motor 3 antes de mover los otros motores
        homing_motor3(motor3, final3)

        # Luego homing de motor1 y motor2 en paralelo
        homing_en_paralelo(motor1, motor2, final1, final2, final3)

        posicion_motor1 = 0  
        posicion_motor2 = 0  

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

            # motor3 es una instancia del controlador que ya tiene métodos girar_sentido1 y detener
            #detectar_movimiento(final3=final3, motor=motor3)
            detectar_movimiento_cam(motor3)
            homing_motor3(motor3, final3)
            time.sleep(1)
            homing_motor3(motor3, final3)

    except KeyboardInterrupt:
        print("\n--------------Programa interrumpido manualmente.--------------")

    except Exception as e:
        print(f"Error en ejecución: {e}")

    finally:
        print("\nVolviendo a home...")
        try:
            homing_motor3(motor3, final3)
            homing_en_paralelo(motor1, motor2, final1, final2, final3)

        except Exception as e:
            print(f"Error al volver a home: {e}")

        motor1.liberar()
        motor2.liberar()
        motor3.liberar()
        print("Recursos liberados correctamente.")

if __name__ == "__main__":
    main()