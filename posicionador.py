import time
import gpiod
from tkinter import messagebox

class MotorNema:
    def __init__(self, pin_1, pin_2, nombre):
        chip = gpiod.Chip('gpiochip0')
        self.dir_pin = chip.get_line(pin_1)
        self.step_pin = chip.get_line(pin_2)
        self.nombre = nombre

        # Configurar los pines como salida
        self.dir_pin.request(consumer=nombre, type=gpiod.LINE_REQ_DIR_OUT)
        self.step_pin.request(consumer=nombre, type=gpiod.LINE_REQ_DIR_OUT)

        # Inicializar la posición actual en 0
        self.posicion_actual = 0

    def mover(self, direccion, pasos, retardo):
        """
        Mueve el motor el número de pasos indicado en la dirección especificada.
        :param direccion: Dirección de movimiento (0 para CW, 1 para CCW)
        :param pasos: Número de pasos a mover
        :param retardo: Tiempo de retardo entre pasos
        """
        self.dir_pin.set_value(direccion)
        for _ in range(pasos):
            self.step_pin.set_value(1)
            time.sleep(retardo)
            self.step_pin.set_value(0)
            time.sleep(retardo)
        # Actualizar la posición después del movimiento
        if direccion == 0:
            self.posicion_actual += pasos
        else:
            self.posicion_actual -= pasos

    def obtener_posicion(self):
        return self.posicion_actual

    def liberar_pines(self):
        """
        Libera los pines al finalizar el proceso.
        """
        self.dir_pin.release()
        self.step_pin.release()


class FinalDeCarrera:
    def __init__(self, pin, nombre):
        chip = gpiod.Chip('gpiochip0')
        self.line = chip.get_line(pin)
        self.nombre = nombre

        # Configurar el pin como entrada
        self.line.request(consumer=nombre, type=gpiod.LINE_REQ_DIR_IN)

    def esta_activado(self):
        """
        Verifica si el final de carrera está activado (envía un 0).
        :return: True si está activado, False en caso contrario.
        """
        return self.line.get_value() == 0

    def liberar_pin(self):
        """
        Libera el pin de entrada al finalizar el proceso.
        """
        self.line.release()


def homing_motor(motor, final_carrera, direccion_inicial, velocidad, pasos_retroceso):
    """
    Realiza el proceso de homing para un motor.
    """
    print(f"Iniciando homing para {motor.nombre}...")
    motor.mover(direccion=direccion_inicial, pasos=1, retardo=velocidad)
    while final_carrera.esta_activado():
        motor.mover(direccion=direccion_inicial, pasos=1, retardo=velocidad)
    time.sleep(0.5)

    # Retroceder un poco
    direccion_opuesta = 1 - direccion_inicial
    print(f"Retrocediendo {motor.nombre}")
    motor.mover(direccion=direccion_opuesta, pasos=pasos_retroceso, retardo=velocidad)
    time.sleep(0.5)

    # Restablecer la posición del motor a 0 después del homing
    motor.posicion_actual = 0
    print(f"Posición de {motor.nombre} restablecida a 0.")


# Función para mover motores con coordenadas absolutas
def mover_motores(coordenadas, detener_callback,fc1,fc2,fc3,ejecutar):
    
    global detener_ejecucion
    
    # Crear instancias de los motores y finales de carrera
    motor1 = MotorNema(3, 2, "Motor1")
    motor2 = MotorNema(5, 4, "Motor2")
    final1 = fc1
    final2 = fc2
    final3 = fc3

    # Filtrar las coordenadas para eliminar (0, 0)
    coordenadas = [coord for coord in coordenadas if coord != (0, 0)]
    print(f"Coordenadas después de filtrar (0, 0): {coordenadas}")

    # Realizar homing de los motores
    homing_motor(motor2, final2, direccion_inicial=0, velocidad=0.0005, pasos_retroceso=500)
    homing_motor(motor1, final1, direccion_inicial=0, velocidad=0.0005, pasos_retroceso=500)
    
    time.sleep(0.5)
    
    # Supongamos que 100 pasos es el valor correcto por cada centímetro, ajústalo si es necesario.
    pasos_por_cm = 100  
    contador = 1
    # Mover los motores según las coordenadas absolutas
    for x, z in coordenadas:
        print(f"Movimiento {contador}")
        
        if not ejecutar[0]:  # Si la ejecución no está activa
            print("Se detuvo el hilo encargado de detener motores.")
            return

        # Calcular la diferencia de posición en pasos (usando coordenadas absolutas)
        pasos_x = abs((x - motor1.obtener_posicion()) * pasos_por_cm)
        pasos_z = abs((z - motor2.obtener_posicion()) * pasos_por_cm)

        # Evitar mover si la posición objetivo es igual a la actual
        if pasos_x == 0 and pasos_z == 0:
            print("Posición ya alcanzada, no se moverán los motores.")
            continue

        # Determinar la dirección para el motor X
        direccion_x = 1 if x > motor1.obtener_posicion() else 0  # Mueve hacia adelante si x es mayor

        # Determinar la dirección para el motor Z
        direccion_z = 1 if z > motor2.obtener_posicion() else 0  # Mueve hacia adelante si z es mayor

        # Mover motor 1 (X)
        print(f"Moviendo motor 1 (X) de {motor1.obtener_posicion()} cm a {x} cm ({abs(pasos_x)} pasos).")
        motor1.mover(direccion=direccion_x, pasos=abs(pasos_x), retardo=0.0005)
        time.sleep(1)

        # Actualizar la posición del motor 1 después de moverse
        motor1.posicion_actual = x

        # Mover motor 2 (Z)
        print(f"Moviendo motor 2 (Z) de {motor2.obtener_posicion()} cm a {z} cm ({abs(pasos_z)} pasos).")
        motor2.mover(direccion=direccion_z, pasos=abs(pasos_z), retardo=0.0005)
        time.sleep(1)

        # Actualizar la posición del motor 2 después de moverse
        motor2.posicion_actual = z

        contador += 1

    print("Movimiento completado.")
    contador = 0

    # Liberar los pines de los motores
    motor1.liberar_pines()
    motor2.liberar_pines()

    print("Pines liberados.")

# Función para mover motores con coordenadas absolutas
def mover_motores_manual(x,z,direccion):
    global detener_ejecucion
    # Crear instancias de los motores y finales de carrera
    motor1 = MotorNema(2, 3, "Motor1")
    motor2 = MotorNema(4, 5, "Motor2")

    pasos_por_cm = 100

    # Calcular la diferencia de posición en pasos (usando coordenadas absolutas)
    pasos_x = abs((x) * pasos_por_cm)
    pasos_z = abs((z) * pasos_por_cm)

    # Mover motor 1 (z)
    motor1.mover(direccion=direccion, pasos=abs(pasos_z), retardo=0.0005)
    time.sleep(1)

    # Mover motor 2 (x)
    motor2.mover(direccion=direccion, pasos=abs(pasos_x), retardo=0.0005)
    time.sleep(1)


    print("Movimiento completado.")

    # Liberar los pines de los motores
    motor1.liberar_pines()
    motor2.liberar_pines()

    print("Pines liberados.")
