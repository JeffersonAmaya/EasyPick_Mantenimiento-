# main.py
import time
import cv2
from sensor_movimiento import SensorMovimiento

def main():
    sensor = SensorMovimiento()

    try:
        print("🟢 Comenzando monitoreo... (ESC para salir)")
        while True:
            movimiento = sensor.detect_movement()

            if movimiento:
                print("🚨 Movimiento detectado -> ACCIONAR MOTOR")
                # Aquí puedes colocar tu control de motor (activar motor, empujar, etc)
                
                # Pausa para evitar múltiples activaciones
                time.sleep(1.0)

            if cv2.waitKey(1) & 0xFF == 27:  # ESC para salir
                print("🛑 ESC presionado. Cerrando.")
                break

            time.sleep(0.01)

    finally:
        sensor.close()

if __name__ == "__main__":
    main()
