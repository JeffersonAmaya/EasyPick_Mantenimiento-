# sensor_movimiento.py
import serial
import time
import numpy as np
import cv2
import os
import subprocess
import signal
import sys

PORT = '/dev/ttyUSB0'
BAUDRATE = 115200
TIMEOUT = 2

FRAME_WIDTH = 100
FRAME_HEIGHT = 100
FRAME_SIZE = FRAME_WIDTH * FRAME_HEIGHT
HEADER_SIZE = 16

roi_pts = np.array([(63, 47), (51, 95), (60, 93), (69, 49)], dtype=np.int32)

DIFF_THRESHOLD = 30
PIXEL_CHANGE_LIMIT = 20
STABLE_FRAMES_REQUIRED = 5

ser = None

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

class SensorMovimiento:
    def __init__(self):
        global ser
        liberar_puerto(PORT)
        ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
        send_commands(ser)
        self.ser = ser
        self.roi_mask = None
        self.ref_frame = None
        self.init_sensor()

    def init_sensor(self):
        print("⏳ Esperando que la escena esté estable...")
        stable_count = 0
        last_frame = None
        while stable_count < STABLE_FRAMES_REQUIRED:
            frame = read_depth_frame(self.ser)
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
                print(f"✅ Frame estable {stable_count}/{STABLE_FRAMES_REQUIRED}")
            else:
                print(f"⚠️ Movimiento detectado durante inicialización ({changes} cambios)")
                stable_count = 0

            last_frame = frame_blur

        self.ref_frame = last_frame
        self.roi_mask = get_mask_from_polygon(self.ref_frame.shape, roi_pts)
        print("🟢 Sensor listo para detección.")

    def detect_movement(self):
        frame = read_depth_frame(self.ser)
        frame_blur = cv2.GaussianBlur(frame, (3, 3), 0)

        roi_ref = cv2.bitwise_and(self.ref_frame, self.ref_frame, mask=self.roi_mask)
        roi_now = cv2.bitwise_and(frame_blur, frame_blur, mask=self.roi_mask)

        diff = cv2.absdiff(roi_ref, roi_now)
        _, diff_thresh = cv2.threshold(diff, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)
        num_changes = cv2.countNonZero(diff_thresh)

        movement_detected = num_changes > PIXEL_CHANGE_LIMIT

        # Mostrar imagen
        img_gray = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        color = (0, 0, 255) if movement_detected else (0, 255, 0)
        cv2.polylines(img_gray, [roi_pts], isClosed=True, color=color, thickness=2)
        if movement_detected:
            cv2.putText(img_gray, "CAMBIO DETECTADO", (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        img_display = cv2.resize(img_gray, (FRAME_WIDTH * 2, FRAME_HEIGHT * 2), interpolation=cv2.INTER_NEAREST)
        cv2.imshow("Vista Sensor", img_display)

        return movement_detected

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        cv2.destroyAllWindows()
