import serial
import time
import numpy as np
import cv2

PORT = 'COM5'
BAUDRATE = 115200
TIMEOUT = 2

FRAME_WIDTH = 100
FRAME_HEIGHT = 100
FRAME_SIZE = FRAME_WIDTH * FRAME_HEIGHT
HEADER_SIZE = 16

# Escalado para visualización
SCALE = 4

class PoligonoDibujador:
    def __init__(self):
        self.puntos = []
        self.poligono_completado = False

    def click_callback(self, event, x, y, flags, param):
        x = x // SCALE
        y = y // SCALE

        if event == cv2.EVENT_LBUTTONDOWN and not self.poligono_completado:
            self.puntos.append((x, y))
            print(f"Punto añadido: ({x}, {y})")

        elif event == cv2.EVENT_RBUTTONDOWN and len(self.puntos) > 2:
            self.poligono_completado = True
            self.imprimir_formato_numpy()

    def reiniciar(self):
        self.puntos = []
        self.poligono_completado = False
        print("Polígono reiniciado")

    def imprimir_formato_numpy(self):
        print("\n--- COORDENADAS DEL POLIGONO ---")
        print("Copia este formato para tu código de detección de movimiento:")
        print(f"area_pts = np.array({self.puntos})")
        print("-----------------------------\n")

def send_commands(ser):
    COMMANDS = [
        b'AT+BAUD=5\r',
        b'AT+PC=1\r',
        b'AT+VIDEO=1\r',
        b'AT+ISP=1\r',
        b'AT+DISP=3\r'
    ]
    for cmd in COMMANDS:
        ser.write(cmd)
        time.sleep(0.2)
        ser.read_all()

def wait_for_reference_frame(ser):
    while True:
        header = ser.read(2)
        if header == b'\x00\xff':
            length_bytes = ser.read(2)
            frame_len = int.from_bytes(length_bytes, 'little')
            frame_data = ser.read(frame_len)
            if len(frame_data) >= HEADER_SIZE + FRAME_SIZE:
                frame_body = frame_data[HEADER_SIZE:HEADER_SIZE + FRAME_SIZE]
                img = np.frombuffer(frame_body, dtype=np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH))
                return img

def visualizar_con_dibujo(ser):
    dibujador = PoligonoDibujador()
    cv2.namedWindow("Sensor con Dibujo", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Sensor con Dibujo", dibujador.click_callback)

    print("Instrucciones:")
    print("- Clic izquierdo: Añadir punto al polígono")
    print("- Clic derecho: Completar polígono y mostrar coordenadas")
    print("- Tecla 'r': Reiniciar polígono")
    print("- Tecla 's': Guardar coordenadas en archivo")
    print("- Tecla 'ESC': Salir")

    while True:
        header = ser.read(2)
        if header == b'\x00\xff':
            length_bytes = ser.read(2)
            frame_len = int.from_bytes(length_bytes, 'little')
            frame_data = ser.read(frame_len)

            if len(frame_data) >= HEADER_SIZE + FRAME_SIZE:
                frame_body = frame_data[HEADER_SIZE:HEADER_SIZE + FRAME_SIZE]
                img_gray = np.frombuffer(frame_body, dtype=np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH))
                img_color = cv2.applyColorMap(img_gray, cv2.COLORMAP_TURBO)
                img_color_big = cv2.resize(img_color, (FRAME_WIDTH*SCALE, FRAME_HEIGHT*SCALE), interpolation=cv2.INTER_NEAREST)

                # Dibujar puntos y líneas del polígono
                if dibujador.puntos:
                    for i, punto in enumerate(dibujador.puntos):
                        px, py = punto
                        cv2.circle(img_color_big, (px*SCALE, py*SCALE), 5, (0, 255, 0), -1)
                        cv2.putText(img_color_big, f"{i+1}", (px*SCALE+5, py*SCALE-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

                    # Dibujar líneas entre puntos
                    for i in range(len(dibujador.puntos) - 1):
                        pt1 = tuple(np.array(dibujador.puntos[i]) * SCALE)
                        pt2 = tuple(np.array(dibujador.puntos[i+1]) * SCALE)
                        cv2.line(img_color_big, pt1, pt2, (255, 0, 0), 2)

                    # Cerrar y rellenar si ya está completo
                    if dibujador.poligono_completado:
                        pt1 = tuple(np.array(dibujador.puntos[-1]) * SCALE)
                        pt2 = tuple(np.array(dibujador.puntos[0]) * SCALE)
                        cv2.line(img_color_big, pt1, pt2, (255, 0, 0), 2)

                        overlay = img_color_big.copy()
                        puntos = np.array(dibujador.puntos, np.int32).reshape((-1, 1, 2)) * SCALE
                        cv2.fillPoly(overlay, [puntos], (0, 0, 255))
                        alpha = 0.3
                        img_color_big = cv2.addWeighted(overlay, alpha, img_color_big, 1 - alpha, 0)

                cv2.imshow("Sensor con Dibujo", img_color_big)

                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
                elif key == ord('r'):
                    dibujador.reiniciar()
                elif key == ord('s') and dibujador.poligono_completado:
                    with open('coordenadas_poligono.txt', 'w') as f:
                        f.write(f"area_pts = np.array({dibujador.puntos})\n")
                    print("Coordenadas guardadas en 'coordenadas_poligono.txt'")

    cv2.destroyAllWindows()

def main():
    with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:
        print(f"Conectado a {PORT}")
        send_commands(ser)
        print("Esperando frames para visualizar...")
        visualizar_con_dibujo(ser)

if __name__ == '__main__':
    main()
