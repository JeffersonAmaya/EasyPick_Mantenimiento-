from gpiozero import PWMOutputDevice
from time import sleep

class ActuadorLineal:
    def __init__(self, rpwm_pin, lpwm_pin):
        # Configura los pines como dispositivos PWM
        self.rpwm = PWMOutputDevice(rpwm_pin)
        self.lpwm = PWMOutputDevice(lpwm_pin)

    def extender(self, duracion, velocidad=1.0):
        """
        Extiende el actuador con una velocidad específica.
        :param duracion: Duración de la extensión en segundos.
        :param velocidad: Velocidad (0.0 a 1.0).
        """
        print(f"Extendiendo actuador a {velocidad*100}% de velocidad")
        self.rpwm.value = velocidad  # Configura la velocidad (PWM)
        self.lpwm.value = 0  # Asegura que el pin LPWM esté apagado
        sleep(duracion)
        self.parar()

    def retraer(self, duracion, velocidad=1.0):
        """
        Retrae el actuador con una velocidad específica.
        :param duracion: Duración de la retracción en segundos.
        :param velocidad: Velocidad (0.0 a 1.0).
        """
        print(f"Retrayendo actuador a {velocidad*100}% de velocidad")
        self.rpwm.value = 0  # Asegura que el pin RPWM esté apagado
        self.lpwm.value = velocidad  # Configura la velocidad (PWM)
        sleep(duracion)
        self.parar()

    def parar(self):
        """
        Detiene el actuador.
        """
        print("Deteniendo actuador")
        self.rpwm.value = 0
        self.lpwm.value = 0
