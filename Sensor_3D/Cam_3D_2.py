import serial
import time
import numpy as np
import cv2

PORT = '/dev/ttyUSB0' 
BAUDRATE = 115200
TIMEOUT = 2

# Interpretación A y B (100x100 = 10000 bytes)
FRAME_WIDTH_A = 100
FRAME_HEIGHT_A = 100
FRAME_SIZE_A = FRAME_WIDTH_A * FRAME_HEIGHT_A

# Interpretación C (112x90 = 10080 bytes)
FRAME_WIDTH_C = 112
FRAME_HEIGHT_C = 90
FRAME_SIZE_C = FRAME_WIDTH_C * FRAME_HEIGHT_C

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
        # print(f"Respuesta: {response}")

def auto_center(img, offset=20):
    return np.roll(img, -offset, axis=1)

def read_frame(ser):
    while True:
        header = ser.read(2)
        if header == b'\x00\xff':
            length_bytes = ser.read(2)
            frame_len = int.from_bytes(length_bytes, 'little')
            frame_data = ser.read(frame_len)

            if len(frame_data) < 10000:
                print(f"⚠️ Frame muy corto: {len(frame_data)} / {frame_len}")
                continue

            try:
                # A: Imagen directa (0:10000)
                img_a = np.frombuffer(frame_data[:FRAME_SIZE_A], dtype=np.uint8).reshape((FRAME_HEIGHT_A, FRAME_WIDTH_A))
                img_a = cv2.resize(img_a, (400, 400), interpolation=cv2.INTER_NEAREST)

                # B: Ignora primeros 16 bytes
                if len(frame_data) >= 10016:
                    img_b = np.frombuffer(frame_data[16:16+FRAME_SIZE_A], dtype=np.uint8).reshape((FRAME_HEIGHT_A, FRAME_WIDTH_A))
                    img_b = cv2.resize(img_b, (400, 400), interpolation=cv2.INTER_NEAREST)
                else:
                    img_b = np.zeros((400, 400), dtype=np.uint8)

                # C: Imagen 112x90
                if len(frame_data) >= FRAME_SIZE_C:
                    img_c = np.frombuffer(frame_data[:FRAME_SIZE_C], dtype=np.uint8).reshape((FRAME_HEIGHT_C, FRAME_WIDTH_C))
                    img_c = cv2.resize(img_c, (400, 320), interpolation=cv2.INTER_NEAREST)
                else:
                    img_c = np.zeros((320, 400), dtype=np.uint8)

                # Centrada (opcional)
                img_centered = auto_center(img_a, offset=20)

                # Mostrar todo
                cv2.imshow("A - Desde inicio (100x100)", img_a)
                cv2.imshow("B - Ignora 16 bytes", img_b)
                cv2.imshow("C - 112x90", img_c)
                cv2.imshow("A centrada", img_centered)

                key = cv2.waitKey(1)
                if key == 27:  # ESC
                    break
            except Exception as e:
                print("❌ Error procesando frame:", e)

def main():
    with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:
        print(f"Conectado a {PORT}")
        send_commands(ser)
        print("Esperando frames...")
        read_frame(ser)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
