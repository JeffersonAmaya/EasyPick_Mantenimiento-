from gpiozero import Button
import time

# Crear los finales de carrera
fc1 = Button(6, pull_up=True)
fc2 = Button(7, pull_up=True)
fc3 = Button(8, pull_up=True)

try:
    while True:
        # Imprimir el estado de cada uno por separado
        if fc1.is_pressed:
            print("FC1 activado")
        if fc2.is_pressed:
            print("FC2 activado")
        if fc3.is_pressed:
            print("FC3 activado")
            
        if not (fc1.is_pressed or fc2.is_pressed or fc3.is_pressed):
            print("Ninguno activado")
        print("-------------------")
        time.sleep(0.5)

except KeyboardInterrupt:
    pass