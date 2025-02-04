import cv2
import json
from tkinter import messagebox
from tkinter import Tk

# Función para cargar las coordenadas del ROI desde un archivo JSON
def cargar_roi():
    try:
        with open('roi_coordinates.json', 'r') as file:
            data = json.load(file)
            roi_coordinates = data.get("roi_coordinates", {})
            return roi_coordinates
    except FileNotFoundError:
        messagebox.showerror("Error", "El archivo JSON no se encontró.")
        return {}
    except json.JSONDecodeError:
        messagebox.showerror("Error", "Hubo un error al leer el archivo JSON.")
        return {}

# Guardar el nuevo ROI en el archivo JSON
def guardar_roi(roi,pref):
    try:
        data = {}
        data[f"x_{pref}"] = roi[0][0]
        data[f"y_{pref}"] = roi[0][1]
        data[f"ancho_{pref}"] = roi[1][0]
        data[f"alto_{pref}"] = roi[1][1]

        with open(f'roi_cam_{pref}.json', 'w') as file:
            json.dump(data, file, indent=4)

        print("Nuevo ROI guardado:", roi)
    except Exception as e:
        messagebox.showerror("Error", f"Hubo un error al guardar el archivo JSON: {str(e)}")

# Función para editar la zona de interés en tiempo real
def editar_zona_interes(self,pref):
    self.pref=pref
    cap = cv2.VideoCapture(0,cv2.CAP_V4L2)
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
    # Establecer la ventana y centrarla
    cv2.namedWindow("Definir area de interes")
    cv2.moveWindow("Definir area de interes", x_pos, y_pos)
    cv2.destroyWindow("Definir area de interes")
    aux_cam=0


    if aux_cam==0:
        # Crear ventana y centrarla
        cv2.namedWindow("Definir area de interes")
        cv2.moveWindow("Definir area de interes", x_pos, y_pos)
        aux_cam=1
        print("Entrè al if")

    if not cap.isOpened():
        print("Error: No se pudo acceder a la cámara.")
        return

    # Configurar FPS y resolución
    cap.set(cv2.CAP_PROP_FPS, 60)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    ref_point = []
    cropping = False
    roi_coordinates = None  # Almacena las coordenadas del ROI para dibujarlas


    # Función para definir el ROI
    def click_and_crop(event, x, y, flags, param):
        nonlocal ref_point, cropping, roi_coordinates

        if event == cv2.EVENT_LBUTTONDOWN:
            ref_point = [(x, y)]
            cropping = True
        elif event == cv2.EVENT_MOUSEMOVE and cropping:
            temp_image = image.copy()
            cv2.rectangle(temp_image, ref_point[0], (x, y), (0, 255, 0), 2)  # Dibuja en color verde mientras arrastras
            cv2.imshow("Definir area de interes", temp_image)
        elif event == cv2.EVENT_LBUTTONUP:
            ref_point.append((x, y))
            cropping = False
            roi_coordinates = ref_point  # Almacena las coordenadas del ROI
            guardar_roi(ref_point,self.pref)  # Guarda el ROI en el archivo JSON


    cv2.setMouseCallback("Definir area de interes", click_and_crop)

    # Captura de video en vivo y actualización de la imagen

    while True:

        ret, image = cap.read()
        if not ret:
            break

        # Si ya hay un ROI definido, dibuja el rectángulo en la imagen
        if roi_coordinates:
            cv2.rectangle(image, roi_coordinates[0], roi_coordinates[1], (0, 0, 255), 2)

        # Muestra el video en la ventana
        cv2.imshow("Definir area de interes", image)

        key = cv2.waitKey(1) & 0xFF

        # Si presionas 'r', reinicia el ROI
        if key == ord("r"):
            ref_point = []
            roi_coordinates = None
        # Si presionas 'c', confirma y termina la edición
        elif key == ord("c"):
            break

    # Liberar la cámara y cerrar la ventana de OpenCV
    cap.release()
    cv2.destroyAllWindows()


