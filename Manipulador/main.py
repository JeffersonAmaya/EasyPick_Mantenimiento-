from motores import MotorNema
from finales_carrera import FinalDeCarrera
from deteccion import detectar_movimiento, homing_lineal
import time

PASOS_POR_CM = 100  
M1_RANGO_MAX_CM = 100
M2_RANGO_MAX_CM = 100

def cm_a_pasos(coordenada_cm):
    return int(coordenada_cm * PASOS_POR_CM)

# Funciones para los perfiles de velocidad
def calcular_retardo_motor1(paso_actual, total_pasos, retardo_min=0.0003, retardo_max=0.001, porcentaje_aceleracion=0.2):
    umbral_aceleracion = int(total_pasos * porcentaje_aceleracion)
    umbral_desaceleracion = total_pasos - umbral_aceleracion

    if paso_actual < umbral_aceleracion:
        factor = paso_actual / umbral_aceleracion
        retardo = retardo_max - (factor * (retardo_max - retardo_min))
    elif paso_actual > umbral_desaceleracion:
        factor = (paso_actual - umbral_desaceleracion) / umbral_aceleracion
        retardo = retardo_min + (factor * (retardo_max - retardo_min))
    else:
        retardo = retardo_min

    return max(retardo, retardo_min)

def calcular_retardo_motor2(paso_actual, total_pasos, retardo_min=0.0004, retardo_max=0.001, porcentaje_aceleracion=0.1):
    umbral_aceleracion = int(total_pasos * porcentaje_aceleracion)
    umbral_desaceleracion = total_pasos - umbral_aceleracion

    if paso_actual < umbral_aceleracion:
        factor = paso_actual / umbral_aceleracion
        retardo = retardo_max - (factor * (retardo_max - retardo_min))
    elif paso_actual > umbral_desaceleracion:
        factor = (paso_actual - umbral_desaceleracion) / umbral_aceleracion
        retardo = retardo_min + (factor * (retardo_max - retardo_min))
    else:
        retardo = retardo_min

    return max(retardo, retardo_min)

# Función para realizar el homing
def homing_motor(motor, final_carrera, direccion_inicial, velocidad, pasos_retroceso):
    print(f"Iniciando homing del ...")
    motor.mover(direccion=direccion_inicial, pasos=1, retardo=velocidad)
    while not final_carrera.esta_activado():
        motor.mover(direccion=direccion_inicial, pasos=1, retardo=velocidad)
    print(f" alcanzó el final de carrera.")

    time.sleep(0.5)

    # Retroceso para salir del final de carrera
    direccion_opuesta = 1 - direccion_inicial
    print(f"Retrocediendo ...")
    motor.mover(direccion=direccion_opuesta, pasos=pasos_retroceso, retardo=velocidad)
    time.sleep(0.5)

def mover_motor_a_posicion(motor, posicion_actual, posicion_objetivo_cm, rango_max_cm, sentido_giro_1, sentido_giro_2, calcular_retardo):
    if posicion_objetivo_cm < 0 or posicion_objetivo_cm > rango_max_cm:
        print(f"Error: Coordenada fuera de rango para el motor (0-{rango_max_cm} cm).")
        return posicion_actual

    pasos_actuales = cm_a_pasos(posicion_actual)
    pasos_objetivo = cm_a_pasos(posicion_objetivo_cm)
    pasos_a_mover = abs(pasos_objetivo - pasos_actuales)
    direccion = sentido_giro_1 if pasos_objetivo > pasos_actuales else sentido_giro_2

    print(f"Moviendo desde {posicion_actual} cm a {posicion_objetivo_cm} cm ({pasos_a_mover} pasos).")

    for paso in range(pasos_a_mover):
        retardo = calcular_retardo(paso, pasos_a_mover)
        motor.mover(direccion=direccion, pasos=1, retardo=retardo)

    return posicion_objetivo_cm

def main():
    motor1 = MotorNema(3, 2, "Motor1")
    motor2 = MotorNema(5, 4, "Motor2")

    final1 = FinalDeCarrera(6, "Final1")
    final2 = FinalDeCarrera(7, "Final2")
    final3 = FinalDeCarrera(8, "Final3")

    posicion_motor1 = 0  
    posicion_motor2 = 0  

    try:
        while True:
            homing_lineal(final3)
            time.sleep(2.5)
            homing_motor(motor2, final2, direccion_inicial=0, velocidad=0.0003, pasos_retroceso=100)
            time.sleep(1)
            homing_motor(motor1, final1, direccion_inicial=1, velocidad=0.0006, pasos_retroceso=200)
            time.sleep(1)

            try:
                coordenadas = [ (0,20), 
                                (26,10)]

                coordenadas_ordenadas = sorted(coordenadas)

                print(f"Coordenadas ordenadas: {coordenadas_ordenadas}")

                for coord_m1, coord_m2 in coordenadas_ordenadas:
                    posicion_motor1 = mover_motor_a_posicion(motor1, posicion_motor1, coord_m1, M1_RANGO_MAX_CM, 0, 1, calcular_retardo_motor1)
                    time.sleep(1)
                    posicion_motor2 = mover_motor_a_posicion(motor2, posicion_motor2, coord_m2, M2_RANGO_MAX_CM, 1, 0, calcular_retardo_motor2)
                    time.sleep(1)
                    print(f"Posición alcanzada: Motor1={posicion_motor1} cm, Motor2={posicion_motor2} cm")
                    
                    for coord in coordenadas:
                        #print(f"Procesando coordenada: x={coord_m1}, y={coord_m2}")
                        z=coord_m1
                        x=coord_m2
                        
                        # Tomar decisiones según las coordenadas
                        if x == 1:       #MADERA ARRIBA
                            print("Acción 1: MADERA ARRIBA.")
                            roi_x, roi_y, roi_ancho, roi_alto = 97, 263, 256, 332
                            detectar_movimiento(roi_x, roi_y, roi_ancho, roi_alto,final3)
                            break
                        elif x == 2:  #Lupa
                            print("Acción 3: Lupa.")
                            roi_x, roi_y, roi_ancho, roi_alto = 85, 209, 462, 240
                            detectar_movimiento(roi_x, roi_y, roi_ancho, roi_alto,final3)
                            break
                        elif x == 3:          #Caja RASPBERRY
                            print("Acción 2: Caja RASPBERRY.")
                            roi_x, roi_y, roi_ancho, roi_alto = 151, 267, 270, 319
                            detectar_movimiento(roi_x, roi_y, roi_ancho, roi_alto,final3)
                            break
                        
                        elif x == 4:       # Madera abajo
                            print("Acción 4: Madera abajo.")
                            roi_x, roi_y, roi_ancho, roi_alto = 194, 216, 489, 302
                            detectar_movimiento(roi_x, roi_y, roi_ancho, roi_alto,final3)
                            break
                        
                        else:
                            print("Accion por defecto: Coordenada fuera de rango.")
                            roi_x, roi_y, roi_ancho, roi_alto = 112, 207, 414, 257
                            detectar_movimiento(roi_x, roi_y, roi_ancho, roi_alto,final3)
                            break
                return posicion_motor1, posicion_motor2

            except Exception as e:
                print(f"Error al procesar las coordenadas: {e}")
        

    except KeyboardInterrupt:
        print("\n--------------Programa interrumpido manualmente.--------------")

    finally:
        print("\nVolviendo a home...")
        homing_motor(motor2, final2, direccion_inicial=0, velocidad=0.0003, pasos_retroceso=100)
        homing_motor(motor1, final1, direccion_inicial=1, velocidad=0.0006, pasos_retroceso=200)
        motor1.liberar()
        motor2.liberar()
        print("Recursos liberados.")

if __name__ == "__main__":
    main()
