import serial
import time
import numpy as np
import cv2
import os
import subprocess

# Configuración del puerto
PORT = '/dev/ttyUSB1'
BAUDRATE = 115200
TIMEOUT = 2

FRAME_WIDTH = 100
FRAME_HEIGHT = 100
FRAME_SIZE = FRAME_WIDTH * FRAME_HEIGHT
HEADER_SIZE = 16

# Región de interés (polígono)
roi_pts = np.array([(62, 98), (72, 97), (85, 51), (77, 51)], dtype=np.int32)

# Sensibilidad
DIFF_THRESHOLD = 30
PIXEL_CHANGE_LIMIT = 20
STABLE_FRAMES_REQUIRED = 5

def liberar_puerto(port):
    try:
        output = subprocess.check_output(['lsof', port])
        lines = output.decode().split('\n')[1:]
        for line in lines:
            if line:
                pid = int(line.split()[1])
                print(f"🔴 Matando proceso que usa {port} con PID {pid}")
                os.kill(pid, 9)
        print(f"✅ Puerto {port} liberado.")
    except subprocess.CalledProcessError:
        print(f"✅ Puerto {port} no está en uso.")

def send_commands(ser):
    commands = [
        b'AT+BAUD=5\r',
        b'AT+PC=1\r',
        b'AT+VIDEO=1\r',
        b'AT+ISP=1\r',
        b'AT+DISP=3\r'
    ]
    for cmd in commands:
        ser.write(cmd)
        time.sleep(0.2)
        ser.read_all()

def get_mask_from_polygon(shape, polygon):
    mask = np.zeros(shape, dtype=np.uint8)
    return cv2.fillPoly(mask, [polygon], 255)

def read_depth_frame(ser):
    while True:
        header = ser.read(2)
        if header == b'\x00\xff':
            length_bytes = ser.read(2)
            if len(length_bytes) < 2:
                continue
            frame_len = int.from_bytes(length_bytes, 'little')
            frame_data = ser.read(frame_len)
            if len(frame_data) >= HEADER_SIZE + FRAME_SIZE:
                frame_body = frame_data[HEADER_SIZE:HEADER_SIZE + FRAME_SIZE]
                return np.frombuffer(frame_body, dtype=np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH))
    return None

def main():
    liberar_puerto(PORT)  # 🔧 Intentar liberar el puerto antes de abrirlo

    try:
        with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:
            print("Iniciando sensor de profundidad...")
            send_commands(ser)

            print("Esperando que la escena esté estable...")

            stable_count = 0
            last_frame = None

            while stable_count < STABLE_FRAMES_REQUIRED:
                frame = read_depth_frame(ser)
                frame_blur = cv2.GaussianBlur(frame, (3, 3), 0)

                if last_frame is None:
                    last_frame = frame_blur
                    continue

                diff = cv2.absdiff(last_frame, frame_blur)
                diff_mask = get_mask_from_polygon(diff.shape, roi_pts)
                diff_roi = cv2.bitwise_and(diff, diff, mask=diff_mask)
                _, diff_thresh = cv2.threshold(diff_roi, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)
                changes = cv2.countNonZero(diff_thresh)

                if changes < PIXEL_CHANGE_LIMIT:
                    stable_count += 1
                    print(f"Frame estable {stable_count}/{STABLE_FRAMES_REQUIRED}")
                else:
                    print(f"⚠️ Movimiento detectado durante inicialización ({changes} cambios)")
                    stable_count = 0

                last_frame = frame_blur

            ref_frame = last_frame
            mask_roi = get_mask_from_polygon(ref_frame.shape, roi_pts)

            print("Monitoreando movimiento... (ESC para salir)")

            while True:
                frame = read_depth_frame(ser)
                frame_blur = cv2.GaussianBlur(frame, (3, 3), 0)

                roi_ref = cv2.bitwise_and(ref_frame, ref_frame, mask=mask_roi)
                roi_now = cv2.bitwise_and(frame_blur, frame_blur, mask=mask_roi)

                diff = cv2.absdiff(roi_ref, roi_now)
                _, diff_thresh = cv2.threshold(diff, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)
                num_changes = cv2.countNonZero(diff_thresh)

                movement_detected = num_changes > PIXEL_CHANGE_LIMIT

                img_color = cv2.applyColorMap(frame, cv2.COLORMAP_TURBO)
                cv2.polylines(img_color, [roi_pts], isClosed=True, color=(0, 255, 0), thickness=1)

                if movement_detected:
                    cv2.putText(img_color, "CAMBIO DETECTADO", (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                    cv2.polylines(img_color, [roi_pts], isClosed=True, color=(0, 0, 255), thickness=2)

                img_display = cv2.resize(img_color, (FRAME_WIDTH * 4, FRAME_HEIGHT * 4), interpolation=cv2.INTER_NEAREST)
                cv2.imshow("Vista con Poligono", img_display)

                if cv2.waitKey(1) & 0xFF == 27:
                    break

            cv2.destroyAllWindows()

    except Exception as e:
        print(f"❌ Error al abrir el puerto serial: {e}")

if __name__ == "__main__":
    main()
