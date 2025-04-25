import pyudev
import os
import time

def reset_usb_device(vendor_id='1a86', product_id='7523'):  # Ejemplo: CH340
    context = pyudev.Context()
    for device in context.list_devices(subsystem='usb', DEVTYPE='usb_device'):
        if device.get('ID_VENDOR_ID') == vendor_id and device.get('ID_MODEL_ID') == product_id:
            dev_path = device.device_node
            busnum = device.attributes.get('busnum').decode()
            devnum = device.attributes.get('devnum').decode()
            usb_path = f"/dev/bus/usb/{int(busnum):03d}/{int(devnum):03d}"
            print(f"🔌 Reiniciando dispositivo USB en {usb_path}")
            os.system(f"sudo usbreset {usb_path}")
            time.sleep(2)
            return True
    print("❌ No se encontró el dispositivo USB para reiniciar.")
    return False
