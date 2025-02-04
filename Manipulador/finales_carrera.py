import gpiod

class FinalDeCarrera:
    def __init__(self, pin, nombre):
        chip = gpiod.Chip('gpiochip0')
        self.line = chip.get_line(pin)

        # Configurar el pin como entrada
        self.line.request(consumer=nombre, type=gpiod.LINE_REQ_DIR_IN)

    def esta_activado(self):
        """
        Verifica si el final de carrera está activado (envía un 0).
        :return: True si está activado, False en caso contrario.
        """
        return self.line.get_value() == 0
