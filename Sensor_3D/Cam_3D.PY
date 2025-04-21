import serial
import time
import numpy as np
import cv2

PORT = '/dev/ttyUSB0'  # o '/dev/ttyACM0' según corresponda
BAUDRATE = 115200
TIMEOUT = 2

FRAME_WIDTH = 100
FRAME_HEIGHT = 100
FRAME_SIZE = FRAME_WIDTH * FRAME_HEIGHT
HEADER_SIZE = 16  # Bytes a ignorar al inicio del frame

def send_commands(ser):
    COMMANDS = [
        b'AT+BAUD=5\r',
        b'AT+PC=1\r',
        b'AT+VIDEO=1\r',
        b'AT+ISP=1\r',
        b'AT+DISP=3\r'
    ]
    for cmd in COMMANDS:
        print(f"Enviando: {cmd}")
        ser.write(cmd)
        time.sleep(0.2)
        response = ser.read_all()

def read_frame(ser):
    while True:
        header = ser.read(2)
        if header == b'\x00\xff':
            length_bytes = ser.read(2)
            frame_len = int.from_bytes(length_bytes, 'little')
            frame_data = ser.read(frame_len)

            if len(frame_data) >= HEADER_SIZE + FRAME_SIZE:
                frame_body = frame_data[HEADER_SIZE:HEADER_SIZE + FRAME_SIZE]
                img_gray = np.frombuffer(frame_body, dtype=np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH))

                # Escala para mejor visualización
                img_gray_big = cv2.resize(img_gray, (FRAME_WIDTH*4, FRAME_HEIGHT*4), interpolation=cv2.INTER_NEAREST)

                # Convertir a color (colormap)
                img_color = cv2.applyColorMap(img_gray, cv2.COLORMAP_VIRIDIS)
                img_color_big = cv2.resize(img_color, (FRAME_WIDTH*4, FRAME_HEIGHT*4), interpolation=cv2.INTER_NEAREST)

                # Mostrar ambas
                cv2.imshow("Grises - Depth Raw", img_gray_big)
                cv2.imshow("Color - Depth Colormap", img_color_big)

                key = cv2.waitKey(1)
                if key == 27:  # ESC
                    break
            else:
                print(f"⚠️ Frame incompleto: {len(frame_data)} / {frame_len}")

def main():
    with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:
        print(f"Conectado a {PORT}")
        send_commands(ser)
        print("Esperando frames...")
        read_frame(ser)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
