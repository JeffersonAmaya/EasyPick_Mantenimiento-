# Archivo: motion_detector.py
# Detector de movimiento usando el polígono definido

import cv2
import numpy as np
import time
import threading
from gpiozero import PWMOutputDevice
from tkinter import Tk


# Configuración de los pines
RPWM = PWMOutputDevice(18)
LPWM = PWMOutputDevice(19)
detener_hilo = threading.Event()

def homing_lineal(final_carrera):
    """
    Realiza el proceso de homing para ,motor lineal.
    """
    print(f"Iniciando homing del motor lineal")
    RPWM.value = 0
    LPWM.value = 1
    time.sleep(0.5) 
    while not final_carrera.esta_activado():
        RPWM.value = 0
        LPWM.value = 1
        time.sleep(0.5)  
    print(f"Motor lineal alcanzó el final de carrera.")
    time.sleep(1)

def perfil_velocidad():
    """
    Realizando perfil de velocidad
    """
    velocidad = 1  # Velocidad inicial
    decremento = 0.1  # Incremento por segundo

    while not detener_hilo.is_set():  # Continúa mientras no se detenga el hilo
        RPWM.value = velocidad
        LPWM.value = 0
        #print(f"Velocidad actual: {RPWM.value}")
        time.sleep(1)  # decrementa cada segundo
        if velocidad <= 0.3:
            velocidad=0.3
            #print("Velocidad fija en 0.2")
        else:
            velocidad -= decremento  # decrementa la velocidad

def detectar_movimiento():

    global detener_hilo
    detener_hilo.clear()
    
    # Reducir resolución para mejor rendimiento en Raspberry Pi
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Verificar si la cámara se abrió correctamente
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara.")
        return
    
    # Obtener un frame para determinar las dimensiones
    ret, frame = cap.read()
    if not ret:
        print("Error: No se pudo capturar frame inicial.")
        return
        
    # Área predeterminada (ajustar según tu cámara)
    area_pts = np.array([(1, 304), (524, 223), (429, 211), (0, 257), (3, 302)])
    
    # Crear el sustractor de fondo
    try:
        # Primero intentar con cv2.bgsegm
        fgbg = cv2.bgsegm.createBackgroundSubtractorMOG()
    except AttributeError:
        try:
            # Si no funciona, intentar con la versión estándar
            fgbg = cv2.createBackgroundSubtractorMOG2()
        except:
            print("Error: No se pudo crear el sustractor de fondo.")
            return
    
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    
    # Contador de FPS
    fps_start_time = time.time()
    fps_counter = 0
    fps = 0
    
    print("Detector de movimiento iniciado. Presiona 'ESC' para salir.")
    hilo_velocidad = threading.Thread(target=perfil_velocidad)
    hilo_velocidad.start()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo capturar frame.")
            break
        
        # Actualizar FPS
        fps_counter += 1
        if (time.time() - fps_start_time) > 1:
            fps = fps_counter
            fps_counter = 0
            fps_start_time = time.time()
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Dibujar un rectángulo negro para mostrar estado
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
        color = (0, 255, 0)
        texto_estado = "Estado: No se ha detectado movimiento"
        
        # Crear máscara con el área seleccionada
        imAux = np.zeros(shape=(frame.shape[:2]), dtype=np.uint8)
        imAux = cv2.drawContours(imAux, [area_pts], -1, (255), -1)
        image_area = cv2.bitwise_and(gray, gray, mask=imAux)
        
        # Aplicar sustracción de fondo
        fgmask = fgbg.apply(image_area)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
        fgmask = cv2.dilate(fgmask, None, iterations=2)
        
        # Encontrar contornos de los objetos detectados
        contornos = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Compatibilidad con diferentes versiones de OpenCV
        cnts = contornos[0] if len(contornos) == 2 else contornos[1]
        
        for cnt in cnts:
            if cv2.contourArea(cnt) > 500:
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                texto_estado = "Estado: Alerta Movimiento Detectado!"
                color = (0, 0, 255)
                #print("Movimiento detectado: Detener eyector.")
                detener_hilo.set()  # Detiene el hilo
                hilo_velocidad.join()  # Espera a que termine el hilo
                #print("\nHoming del eyector...")
                homing_lineal(final3)
                homing_lineal(final3)
                homing_lineal(final3)
                break
        
        # Dibujar contorno del área de interés
        cv2.drawContours(frame, [area_pts], -1, color, 2)
        cv2.putText(frame, texto_estado, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Mostrar FPS
        cv2.putText(frame, f"FPS: {fps}", (frame.shape[1] - 120, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Mostrar imágenes
        cv2.imshow('Detector de Movimiento', frame)
        
        # Presionar 'ESC' para salir
        k = cv2.waitKey(30) & 0xFF
        if k == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detectar_movimiento()