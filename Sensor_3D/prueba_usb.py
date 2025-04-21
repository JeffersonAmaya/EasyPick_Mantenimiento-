import serial
import time
import numpy as np
import cv2
import serial.tools.list_ports

HEADER = b'\x00\xff'
FRAME_SIZE = 60 * 80  # ancho x alto de la imagen de profundidad

def reiniciar_puerto():
    print("🚀 Reiniciando puerto serial...")
    ports = serial.tools.list_ports.comports()
    available_ports = [p.device for p in ports if 'USB' in p.device]
    
    if not available_ports:
        print("❌ No se encontraron puertos USB disponibles.")
        return None

    # Intentar cada puerto disponible
    for port in available_ports:
        try:
            ser = serial.Serial(port, 115200, timeout=1)
            ser.close()  # Liberar el puerto
            print(f"🔄 Puerto liberado: {port}")
            return port
        except Exception as e:
            print(f"❌ Error al cerrar {port}: {e}")
    return None

def esperar_respuesta(ser, timeout=2):
    """Esperar respuesta con un tiempo máximo."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        data = ser.read_all()
        if data:
            print(f"📥 Respuesta: {data[:300]}...")  # Muestra los primeros 300 bytes
            return data
    print("❌ No se recibió respuesta en el tiempo esperado.")
    return None

def main():
    port = reiniciar_puerto()
    if not port:
        print("❌ No se encontró un puerto USB disponible.")
        return

    ser = serial.Serial(port, 115200, timeout=0.5)
    print(f"✅ Conectado a {port}")

    # Cambiar a 1Mbps
    cmd_baud = b'AT+BAUD=5\r'
    print(f"📤 Enviando: {cmd_baud}")
    ser.write(cmd_baud)
    if not esperar_respuesta(ser):
        ser.close()
        return

    ser.baudrate = 1000000
    time.sleep(0.1)

    # Iniciar transmisión
    cmd_start = b'AT+ISP=0\r'
    print(f"📤 Enviando: {cmd_start}")
    ser.write(cmd_start)
    if not esperar_respuesta(ser):
        ser.close()
        return

    buffer = bytearray()
    print("📡 Esperando datos...")

    while True:
        buffer += ser.read(4096)
        while HEADER in buffer:
            idx = buffer.find(HEADER)
            if len(buffer) - idx >= FRAME_SIZE + 2:
                frame = buffer[idx+2:idx+2+FRAME_SIZE]
                img = np.frombuffer(frame, dtype=np.uint8).reshape((60, 80))
                img_resized = cv2.resize(img, (320, 240), interpolation=cv2.INTER_NEAREST)
                heatmap = cv2.applyColorMap(img_resized, cv2.COLORMAP_JET)
                cv2.imshow("🟣 Profundidad", heatmap)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    ser.close()
                    cv2.destroyAllWindows()
                    return
                buffer = buffer[idx+2+FRAME_SIZE:]
            else:
                break

if __name__ == "__main__":
    main()
