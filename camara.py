import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from tkinter import Tk


def iniciar_deteccion_movimiento(roix,roiy,ancho,alto,camara):
    # Captura de video desde la cámara
    captura = cv2.VideoCapture(camara, cv2.CAP_V4L2)

    if not captura.isOpened():
        print("Error al abrir la cámara.")
        exit()

    # Configurar FPS y resolución
    captura.set(cv2.CAP_PROP_FPS, 60)
    captura.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    captura.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Leer el primer fotograma para referencia
    _, fotograma_inicial = captura.read()
    fotograma_inicial = cv2.cvtColor(fotograma_inicial, cv2.COLOR_BGR2GRAY)
    fotograma_inicial = cv2.GaussianBlur(fotograma_inicial, (21, 21), 0)

    roi_x, roi_y, roi_ancho, roi_alto =roix,roiy,ancho,alto
    roi_alto_2=roi_alto-roi_y
    roi_ancho_2=roi_ancho-roi_x

    # Definir la región de interés (ROI)
    roi_inicial = fotograma_inicial[roi_y:roi_y + (roi_alto_2), roi_x:roi_x + (roi_ancho_2)]

    # Establecer la función de callback para el mouse
    root = Tk()
    root.withdraw()  # Ocultar la ventana
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()  # Eliminar la ventana raíz

    window_width = 640
    window_height = 480

    # Calcular posición para centrar la ventana
    x_pos = ((screen_width - window_width) // 2)
    y_pos = ((screen_height - window_height) // 2)

    # Crear ventana y centrarla
    cv2.namedWindow("Detección de Movimiento")
    cv2.moveWindow("Detección de Movimiento", x_pos, y_pos)
    cv2.destroyWindow("Detección de Movimiento")
    aux_cam=0


    while True:
        if aux_cam==0:
            # Crear ventana y centrarla
            cv2.namedWindow("Detección de Movimiento")
            cv2.moveWindow("Detección de Movimiento", x_pos, y_pos)
            aux_cam=1
            print("Entrè al if")
        
        cv2.moveWindow("Detección de Movimiento", x_pos, y_pos)
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

        cv2.rectangle(fotograma_actual,  (roi_x, roi_y), (roi_x + (roi_ancho-roi_x), roi_y + (roi_alto-roi_y)), (255, 255, 0), 4)
        
        # Crear una imagen de PIL a partir de la imagen de OpenCV
        pil_img = Image.fromarray(cv2.cvtColor(fotograma_actual, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)

        # Dibujar un círculo relleno en función del estado
        if movimiento_detectado:
            draw.ellipse((10, 400, 50, 440), fill=(231, 76, 60))  # Círculo rojo
        else:
            draw.ellipse((10, 400, 50, 440), fill=(34, 153, 84))  # Círculo verde
        
        # Convertir de nuevo a formato OpenCV
        fotograma_actual = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        # Mostrar el fotograma con la detección de movimiento
        cv2.imshow("Detección de Movimiento", fotograma_actual)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Liberar la captura de video y cerrar ventanas
    captura.release()
    cv2.destroyAllWindows()