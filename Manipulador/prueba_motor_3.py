import RPi.GPIO as GPIO
import time

# Pines GPIO
DIR = 17    # Dirección
STEP = 27    # Pulso
ENA = 22     # Habilitación

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)

# Activar driver
GPIO.output(ENA, GPIO.LOW)

# Función para mover el motor
def mover_motor(pasos, direccion, retardo):
    GPIO.output(DIR, direccion)
    for _ in range(pasos):
        GPIO.output(STEP, GPIO.HIGH)
        time.sleep(retardo)
        GPIO.output(STEP, GPIO.LOW)
        time.sleep(retardo)

# Movimiento hacia un lado (más pasos, más lento)
mover_motor(pasos=2500, direccion=GPIO.HIGH, retardo=0.001)

# Espera
time.sleep(1)

# Movimiento de regreso (menos pasos, más rápido si quieres)
mover_motor(pasos=2500, direccion=GPIO.LOW, retardo=0.001)

# Desactivar driver
GPIO.output(ENA, GPIO.HIGH)
GPIO.cleanup()
