import serial
import time
import numpy as np
import cv2

PORT = '/dev/ttyUSB0' 
BAUDRATE = 115200
TIMEOUT = 2

FRAME_WIDTH_A = 100
FRAME_HEIGHT_A = 100
FRAME_SIZE_A = FRAME_WIDTH_A * FRAME_HEIGHT_A

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
        ser.read_all()

def read_frame(ser):
    while True:
        header = ser.read(2)
        if header == b'\x00\xff':
            length_bytes = ser.read(2)
            frame_len = int.from_bytes(length_bytes, 'little')
            frame_data = ser.read(frame_len)

            if len(frame_data) < 10016:
                print(f"⚠️ Frame muy corto: {len(frame_data)} / {frame_len}")
                continue

            try:
                img_b = np.frombuffer(frame_data[16:16+FRAME_SIZE_A], dtype=np.uint8).reshape((FRAME_HEIGHT_A, FRAME_WIDTH_A))
                img_b = cv2.resize(img_b, (400, 400), interpolation=cv2.INTER_NEAREST)

                cv2.imshow("Imagen B (ignora 16 bytes)", img_b)

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
