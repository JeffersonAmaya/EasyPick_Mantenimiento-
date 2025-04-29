
import cv2
import numpy as np
import time
import threading
from gpiozero import PWMOutputDevice, DigitalInputDevice
from tkinter import Tk
from motores import MotorNema

detener_hilo= threading.Event()

def perfil_velocidad(motor3):
    """
    Realizando perfil de velocidad
    """

    while not detener_hilo.is_set():
        motor3.mover(direccion=1, pasos=1, retardo=0.0003)

def detectar_movimiento(final3,motor):
    global detener_hilo
    detener_hilo.clear()

    cap = cv2.VideoCapture("/dev/video0")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara.")
        return

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
    hilo_velocidad = threading.Thread(target=perfil_velocidad, args=(motor,))
    print("Iniciando hilo de velocidad...")
    hilo_velocidad.start()

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

        for cnt in cnts:
            if cv2.contourArea(cnt) > 500:
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                texto_estado = "Estado: Alerta Movimiento Detectado!"
                color = (0, 0, 255)
                print("Movimiento detectado: Detener eyector.")
                
                detener_hilo.set()
                hilo_velocidad.join()
                detener_hilo.clear()
                cap.release()
                cv2.destroyAllWindows()

                break  # Salta al siguiente frame para evitar múltiples detecciones seguidas

        cv2.drawContours(frame, [area_pts], -1, color, 2)
        cv2.putText(frame, texto_estado, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow('Detector de Movimiento', frame)

        if cv2.waitKey(30) & 0xFF == 27:
            break

    detener_hilo.set()
    hilo_velocidad.join()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__": 
    detectar_movimiento()
