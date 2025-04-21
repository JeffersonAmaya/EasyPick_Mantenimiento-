import os
import time
import subprocess

USB_BUS_ID = "1-1"  # Este es el bus donde está tu dispositivo
DEVICE_PATH = "/dev/ttyUSB0"
TIMEOUT = 20  # Segundos para esperar a que aparezca el dispositivo

def reiniciar_usb(bus_id):
    print(f"🔌 Reiniciando USB en {bus_id}...")
    try:
        with open('/sys/bus/usb/drivers/usb/unbind', 'w') as f:
            f.write(bus_id)
        time.sleep(2)
        with open('/sys/bus/usb/drivers/usb/bind', 'w') as f:
            f.write(bus_id)
        print("✅ USB reiniciado.")
    except Exception as e:
        print(f"❌ Error al reiniciar el USB: {e}")

def esperar_puerto(path, timeout):
    print(f"⏳ Esperando que aparezca {path}...")
    for _ in range(timeout):
        if os.path.exists(path):
            print(f"✅ Puerto detectado: {path}")
            return True
        time.sleep(1)
    print("❌ Tiempo de espera agotado. El puerto no apareció.")
    return False

def main():
    if not os.path.exists(DEVICE_PATH):
        print(f"⚠️ {DEVICE_PATH} no está disponible.")
        reiniciar_usb(USB_BUS_ID)
        if esperar_puerto(DEVICE_PATH, TIMEOUT):
            print("🚀 Listo para continuar con la ejecución del programa.")
            # Aquí podrías importar tu script de cámara o continuar con la lógica
        else:
            print("❌ No se pudo recuperar el dispositivo.")
    else:
        print(f"✅ {DEVICE_PATH} ya está disponible.")

if __name__ == "__main__":
    main()
