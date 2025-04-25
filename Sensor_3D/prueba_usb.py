import serial
import numpy as np
import serial.tools.list_ports

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


def main():
    port = reiniciar_puerto()
    if not port:
        print("❌ No se encontró un puerto USB disponible.")
        return


if __name__ == "__main__":
    main()
