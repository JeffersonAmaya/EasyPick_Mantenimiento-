from motores import MotorNema
from finales_carrera import FinalDeCarrera
from deteccion import detectar_movimiento,homing_lineal
from gpiozero import PWMOutputDevice
import time

PASOS_POR_CM = 100  # 100 pasos equivalen a 1 cm
M1_RANGO_MAX_CM = 60
M2_RANGO_MAX_CM = 60

def cm_a_pasos(coordenada_cm):
    """
    Convierte una coordenada en cm a pasos.
    """
    return int(coordenada_cm * PASOS_POR_CM)

def homing_motor(motor, final_carrera, direccion_inicial, velocidad, pasos_retroceso):
    """
    Realiza el proceso de homing para un motor.
    """
    #print(f"Iniciando homing...")
    motor.mover(direccion=direccion_inicial, pasos=1, retardo=velocidad)
    while not final_carrera.esta_activado():
        motor.mover(direccion=direccion_inicial, pasos=1, retardo=velocidad)
    #print(f"Motor alcanzó el final de carrera.")

    time.sleep(0.5)

    # Retroceder un poco
    direccion_opuesta = 1 - direccion_inicial
    #print(f"Retrocediendo motor")
    motor.mover(direccion=direccion_opuesta, pasos=pasos_retroceso, retardo=velocidad)
    time.sleep(0.5)

def mover_motor_a_posicion(motor, posicion_actual, posicion_objetivo_cm, rango_max_cm):
    """
    Mueve un motor a una posición absoluta en centímetros.
    """
    if posicion_objetivo_cm < 0 or posicion_objetivo_cm > rango_max_cm:
        print(f"Error: Coordenada fuera de rango para el motor (0-{rango_max_cm} cm).")
        return posicion_actual

    pasos_actuales = cm_a_pasos(posicion_actual)
    pasos_objetivo = cm_a_pasos(posicion_objetivo_cm)
    pasos_a_mover = abs(pasos_objetivo - pasos_actuales)
    direccion = 1 if pasos_objetivo > pasos_actuales else 0

    #print(f"Moviendo desde {posicion_actual} cm a {posicion_objetivo_cm} cm ({pasos_a_mover} pasos).")
    motor.mover(direccion=direccion, pasos=pasos_a_mover, retardo=0.0003)

    return posicion_objetivo_cm

def mover_a_coordenadas(motor1, motor2, coordenadas, posicion_motor1, posicion_motor2,final3):
    """
    Mueve los motores a una lista de coordenadas absolutas en orden.
    """

    for idx, (coord_m1, coord_m2) in enumerate(coordenadas):
        #print(f"\nMoviendo a coordenada {idx + 1}: Motor1={coord_m1} cm, Motor2={coord_m2} cm")
        posicion_motor1 = mover_motor_a_posicion(motor1, posicion_motor1, coord_m1, M1_RANGO_MAX_CM)
        time.sleep(1)
        posicion_motor2 = mover_motor_a_posicion(motor2, posicion_motor2, coord_m2, M2_RANGO_MAX_CM)
        #print(f"Coordenada {idx + 1} alcanzada: Motor1={posicion_motor1} cm, Motor2={posicion_motor2} cm")
        for coord in coordenadas:
            #print(f"Procesando coordenada: x={coord_m1}, y={coord_m2}")
            z=coord_m1
            x=coord_m2
            
            # Tomar decisiones según las coordenadas
            if x == 31:       #MADERA ARRIBA
                print("Acción 1: MADERA ARRIBA.")
                roi_x, roi_y, roi_ancho, roi_alto = 97, 263, 256, 332
                detectar_movimiento(roi_x, roi_y, roi_ancho, roi_alto,final3)
                break
            elif x == 30:  #Lupa
                print("Acción 3: Lupa.")
                roi_x, roi_y, roi_ancho, roi_alto = 85, 209, 462, 240
                detectar_movimiento(roi_x, roi_y, roi_ancho, roi_alto,final3)
                break
            elif x == 45:          #Caja RASPBERRY
                print("Acción 2: Caja RASPBERRY.")
                roi_x, roi_y, roi_ancho, roi_alto = 151, 267, 270, 319
                detectar_movimiento(roi_x, roi_y, roi_ancho, roi_alto,final3)
                break
            
            elif x == 50:       # Madera abajo
                print("Acción 4: Madera abajo.")
                roi_x, roi_y, roi_ancho, roi_alto = 194, 216, 489, 302
                detectar_movimiento(roi_x, roi_y, roi_ancho, roi_alto,final3)
                break
            
            else:
                print("Acción por defecto: Coordenada fuera de rango.")
                roi_x, roi_y, roi_ancho, roi_alto = 108, 297, 305, 376
                detectar_movimiento(roi_x, roi_y, roi_ancho, roi_alto,final3)
                break
    return posicion_motor1, posicion_motor2

def main():
    # Crear instancias de los motores
    motor1 = MotorNema(2, 3, "Motor1")
    motor2 = MotorNema(4, 5, "Motor2")

    # Crear instancias de los finales de carrera
    final1 = FinalDeCarrera(6, "Final1")
    final2 = FinalDeCarrera(7, "Final2")
    final3 = FinalDeCarrera(8, "Final3")

    # Posiciones actuales de los motores
    posicion_motor1 = 0  # Posición inicial en cm
    posicion_motor2 = 0  # Posición inicial en cm

    try:
        while True:


            # Realizar homing inicial
            #print("\nHoming del eyector...")
            homing_lineal(final3)

            #print("\nHoming del motor horizontal...")
            homing_motor(motor2, final2, direccion_inicial=0, velocidad=0.0005, pasos_retroceso=500)

            #print("\nHoming del motor vertical...")
            homing_motor(motor1, final1, direccion_inicial=0, velocidad=0.0005, pasos_retroceso=100)

            # Solicitar lista de coordenadas
            # print("\nIngrese las coordenadas absolutas para mover los motores en el formato '[(m1, m2), (m1, m2), ...]'.")
            # coordenadas_input = input(">> ").strip()
            # Usar coordenadas por defecto

            try:
                #coordenadas = eval(coordenadas_input)  # Convertir la entrada en una lista de coordenadas
                coordenadas = [(26, 31),(46, 30),(26, 45),(46, 50)]#(31, 31),(52, 30),(31, 45),(52, 50)
                #print(f"\nUsando coordenadas por defecto: {coordenadas}")

                # Ordenar las coordenadas por z y luego por x
                coordenadas_ordenadas = sorted(coordenadas)


                print(f"Coordenadas ordenadas: {coordenadas_ordenadas}")


                posicion_motor1, posicion_motor2 = mover_a_coordenadas(motor1, motor2, coordenadas_ordenadas, posicion_motor1, posicion_motor2,final3)

                # Volver a home después de completar las coordenadas
                #print("\nVolviendo a home...")
                homing_motor(motor2, final2, direccion_inicial=0, velocidad=0.0005, pasos_retroceso=500)
                homing_motor(motor1, final1, direccion_inicial=0, velocidad=0.0005, pasos_retroceso=100)
                break
            except Exception as e:
                print(f"Error al procesar las coordenadas: {e}")

    except KeyboardInterrupt:
        print("\n--------------Programa interrumpido manualmente.--------------")
        # Realizar homing inicial
        # print("\nHoming del eyector...")
        # homing_lineal(final3)

        # print("\nHoming del motor horizontal...")
        # homing_motor(motor2, final2, direccion_inicial=0, velocidad=0.0005, pasos_retroceso=500)

        # print("\nHoming del motor vertical...")
        # homing_motor(motor1, final1, direccion_inicial=0, velocidad=0.0005, pasos_retroceso=100)


    finally:
        # Liberar recursos
        motor1.liberar()
        motor2.liberar()
        print("Recursos liberados.")

if __name__ == "__main__":
    main()
