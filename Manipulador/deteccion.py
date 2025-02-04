import cv2
import threading
from gpiozero import PWMOutputDevice
import time
from tkinter import Tk


# Configuración de los pines
RPWM = PWMOutputDevice(18)
LPWM = PWMOutputDevice(19)
detener_hilo = threading.Event()

def homing_lineal(final_carrera):
    """
    Realiza el proceso de homing para ,motor lineal.
    """
    #print(f"Iniciando homing del motor lineal")
    RPWM.value = 0
    LPWM.value = 1
    time.sleep(0.5) 
    while not final_carrera.esta_activado():
        RPWM.value = 0
        LPWM.value = 1
        time.sleep(0.5)  
    #print(f"Motor lineal alcanzó el final de carrera.")
    RPWM.value = 0
    LPWM.value = 1
    time.sleep(1)

def perfil_velocidad():
    """
    Realizando perfil de velocidad
    """
    velocidad = 1  # Velocidad inicial
    decremento = 0.08  # Incremento por segundo

    while not detener_hilo.is_set():  # Continúa mientras no se detenga el hilo
        RPWM.value = velocidad
        LPWM.value = 0
        #print(f"Velocidad actual: {RPWM.value}")
        time.sleep(0.25)  # decrementa cada segundo
        if velocidad <= 0.2:
            velocidad=0.2
            #print("Velocidad fija en 0.2")
        else:
            velocidad -= decremento  # decrementa la velocidad



def detectar_movimiento(roi_x, roi_y, roi_ancho, roi_alto,final3):
    
    global detener_hilo
    detener_hilo.clear()
    
    # Captura de video desde la cámara
    captura = cv2.VideoCapture(0, cv2.CAP_V4L2)

    if not captura.isOpened():
        print("Error al abrir la cámara.")
        return

    # Configurar FPS y resolución
    captura.set(cv2.CAP_PROP_FPS, 60)
    captura.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    captura.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Leer el primer fotograma para referencia
    _, fotograma_inicial = captura.read()
    fotograma_inicial = cv2.cvtColor(fotograma_inicial, cv2.COLOR_BGR2GRAY)
    fotograma_inicial = cv2.GaussianBlur(fotograma_inicial, (21, 21), 0)

    roi_alto_2=roi_alto-roi_y
    roi_ancho_2=roi_ancho-roi_x

    # Definir la región de interés (ROI)
    roi_inicial = fotograma_inicial[roi_y:roi_y + (roi_alto_2), roi_x:roi_x + (roi_ancho_2)]

    try:

        # código para estabilización del enfoque
        #print("Esperando a que la cámara enfoque...")
        for _ in range(50):  # Capturar 30 fotogramas para estabilizar el enfoque
            _, _ = captura.read()
        time.sleep(1)  # Esperar 2 segundos adicionales para asegurar el enfoque
        #print("Enfoque listo. Comenzando detección de movimiento.")

        # Establecer la función de callback para el mouse
        root = Tk()
        root.withdraw()  # Ocultar la ventana
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()  # Eliminar la ventana raíz
        window_width = 640
        window_height = 480
        x_pos = (screen_width - window_width) // 2
        y_pos = (screen_height - window_height) // 2
        cv2.namedWindow("Detección de Movimiento")
        hilo_velocidad = threading.Thread(target=perfil_velocidad)
        hilo_velocidad.start()

        while True:

            _, fotograma_actual = captura.read()
            gris_actual = cv2.cvtColor(fotograma_actual, cv2.COLOR_BGR2GRAY)
            gris_actual = cv2.GaussianBlur(gris_actual, (21, 21), 0)
            roi_actual = gris_actual[roi_y:roi_y + (roi_alto_2), roi_x:roi_x + (roi_ancho_2)]#[roi_y:roi_y + (roi_alto-roi_y), roi_x:roi_x + (roi_ancho-roi_x)]
            
            # Calcular la diferencia entre la ROI inicial y la actual
            diferencia = cv2.absdiff(roi_inicial, roi_actual)
            _, umbral = cv2.threshold(diferencia, 12, 255, cv2.THRESH_BINARY)
            umbral = cv2.dilate(umbral, None, iterations=2)
            contornos, _ = cv2.findContours(umbral, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            movimiento_detectado = False
            for contorno in contornos:
                if cv2.contourArea(contorno) < 500:  # Ajustar según sea necesario
                    continue
                movimiento_detectado = True

            cv2.rectangle(fotograma_actual,  (roi_x, roi_y), (roi_x + (roi_ancho-roi_x), roi_y + (roi_alto-roi_y)), (255, 255, 0), 2)
            
            # Control del eyector basado en detección
            if movimiento_detectado:

                #print("Movimiento detectado: Detener eyector.")
                detener_hilo.set()  # Detiene el hilo
                hilo_velocidad.join()  # Espera a que termine el hilo
                #print("\nHoming del eyector...")
                homing_lineal(final3)
                homing_lineal(final3)
                homing_lineal(final3)
                break

                
            else:

                #print("No hay movimiento. Eyector en perfil de velocidad.")
                time.sleep(0.1)  # Evita un bucle muy rápido


            # Mostrar el fotograma con la detección de movimiento
            cv2.imshow("Detección de Movimiento", fotograma_actual)

            # Salir si se presiona 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Cerrando el programa...")
                break

    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario.")
    finally:
        # Liberar la captura de video y cerrar ventanas
        captura.release()
        cv2.destroyAllWindows()
        print("Recursos liberados correctamente.")

if __name__ == "__main__":
    detectar_movimiento()
