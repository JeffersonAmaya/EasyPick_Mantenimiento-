import gpiod
import time

class MotorNema:
    def __init__(self, dir_pin, step_pin, consumer_name):
        chip = gpiod.Chip('gpiochip0')
        self.dir_line = chip.get_line(dir_pin)
        self.step_line = chip.get_line(step_pin)

        # Configurar las líneas como salida
        self.dir_line.request(consumer=consumer_name, type=gpiod.LINE_REQ_DIR_OUT)
        self.step_line.request(consumer=consumer_name, type=gpiod.LINE_REQ_DIR_OUT)

    def mover(self, direccion, pasos, retardo):
        """
        Mueve el motor en la dirección indicada por el número de pasos especificado.
        :param direccion: 0 para CW, 1 para CCW.
        :param pasos: Cantidad de pasos a realizar.
        :param retardo: Retardo entre pasos en segundos.
        """
        self.dir_line.set_value(direccion)
        for _ in range(pasos):
            self.step_line.set_value(1)
            time.sleep(retardo)
            self.step_line.set_value(0)
            time.sleep(retardo)

    def liberar(self):
        """
        Libera los pines utilizados por el motor.
        """
        self.dir_line.release()
        self.step_line.release()
