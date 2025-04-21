from motores import MotorNema
from finales_carrera import FinalDeCarrera
from deteccion import detectar_movimiento
import threading
import time
import math

PASOS_POR_CM = 100  
M1_RANGO_MAX_CM = 100
M2_RANGO_MAX_CM = 100

def calcular_distancia(punto1, punto2):
    """Calcula la distancia euclidiana entre dos puntos."""
    return math.sqrt((punto1[0] - punto2[0])**2 + (punto1[1] - punto2[1])**2)

def optimizar_ruta(coordenadas, punto_inicial=(0, 0)):
    """
    Optimiza la ruta para minimizar la distancia total recorrida.
    Usa el algoritmo del vecino más cercano.
    """
    ruta_optimizada = [punto_inicial]
    coordenadas_restantes = coordenadas.copy()

    while coordenadas_restantes:
        punto_actual = ruta_optimizada[-1]
        
        # Encontrar el punto más cercano
        punto_mas_cercano = min(coordenadas_restantes, 
                                key=lambda x: calcular_distancia(punto_actual, x))
        
        ruta_optimizada.append(punto_mas_cercano)
        coordenadas_restantes.remove(punto_mas_cercano)

    return ruta_optimizada[1:]  # Excluir el punto inicial

def homing_en_paralelo(motor1, motor2, final1, final2, final3):
    """Realiza el homing de los motores en paralelo."""
    # Resultados del homing para cada motor
    resultados_homing = {'motor1': False, 'motor2': False}
    
    # Función para realizar homing de un motor específico
    def realizar_homing(motor, final_carrera, nombre):
        try:
            direccion_inicial = 1 if nombre == 'motor1' else 0
            velocidad = 0.0008 if nombre == 'motor1' else 0.0003
            pasos_retroceso = 200 if nombre == 'motor1' else 100
            
            print(f"Iniciando homing de {nombre}...")
            
            while not final_carrera.esta_activado():
                motor.mover(direccion=direccion_inicial, pasos=1, retardo=velocidad)
            
            print(f"{nombre} alcanzó el final de carrera.")
            time.sleep(0.5)
            
            # Retroceso para salir del final de carrera
            direccion_opuesta = 1 - direccion_inicial
            motor.mover(direccion=direccion_opuesta, pasos=pasos_retroceso, retardo=velocidad)
            
            resultados_homing[nombre] = True
        except Exception as e:
            print(f"Error en homing de {nombre}: {e}")
            resultados_homing[nombre] = False
    
    # Crear y lanzar hilos para homing
    thread_motor1 = threading.Thread(target=realizar_homing, 
                                     args=(motor1, final1, 'motor1'))
    thread_motor2 = threading.Thread(target=realizar_homing, 
                                     args=(motor2, final2, 'motor2'))
    
    # Realizar homing de final3 primero
    #homing_lineal(final3)
    time.sleep(2.5)
    
    # Iniciar hilos de motores
    thread_motor1.start()
    thread_motor2.start()
    
    # Esperar a que terminen ambos
    thread_motor1.join()
    thread_motor2.join()
    
    # Verificar que ambos homing fueron exitosos
    if not all(resultados_homing.values()):
        raise Exception("Homing no completado correctamente")

def main():
    motor1 = MotorNema(3, 2, "Motor1")
    motor2 = MotorNema(5, 4, "Motor2")

    final1 = FinalDeCarrera(6, "Final1")
    final2 = FinalDeCarrera(7, "Final2")
    final3 = FinalDeCarrera(8, "Final3")

    coordenadas = [ (0, 20) , (26, 40) , (52, 60) , (78, 80)] 
                    # (26, 20), (26, 40), (26, 60), (26, 80), 
                    # (52, 20), (52, 40), (52, 60), (52, 80),
                    # (78, 20), (78, 40), (78, 60), (78, 80)]

    # Optimizar ruta
    coordenadas_optimizadas = optimizar_ruta(coordenadas)
    print("Ruta optimizada:", coordenadas_optimizadas)

    try:
        # Realizar homing en paralelo
        homing_en_paralelo(motor1, motor2, final1, final2, final3)
        
        posicion_motor1 = 0  
        posicion_motor2 = 0  

        for coord_m1, coord_m2 in coordenadas_optimizadas:
            # Diccionarios para almacenar resultados de los movimientos
            resultado_m1 = {'success': False, 'posicion_final': posicion_motor1}
            resultado_m2 = {'success': False, 'posicion_final': posicion_motor2}

            # Crear hilos para mover motores en paralelo
            thread_motor1 = threading.Thread(target=mover_motor_en_paralelo, 
                                             args=(motor1, posicion_motor1, coord_m1, M1_RANGO_MAX_CM, 0, 1, resultado_m1))
            thread_motor2 = threading.Thread(target=mover_motor_en_paralelo, 
                                             args=(motor2, posicion_motor2, coord_m2, M2_RANGO_MAX_CM, 1, 0, resultado_m2))

            # Iniciar hilos
            thread_motor1.start()
            thread_motor2.start()

            # Esperar a que ambos hilos terminen
            thread_motor1.join()
            thread_motor2.join()

            # Actualizar posiciones
            posicion_motor1 = resultado_m1['posicion_final']
            posicion_motor2 = resultado_m2['posicion_final']

            print(f"Posición alcanzada: Motor1={posicion_motor1} cm, Motor2={posicion_motor2} cm")

            # Detectar movimiento después de que ambos motores lleguen a su posición
            detectar_movimiento(final3)

    except KeyboardInterrupt:
        print("\n--------------Programa interrumpido manualmente.--------------")

    except Exception as e:
        print(f"Error en ejecución: {e}")

    finally:
        print("\nVolviendo a home...")
        try:
            homing_en_paralelo(motor1, motor2, final1, final2, final3)
        except Exception as e:
            print(f"Error al volver a home: {e}")

        motor1.liberar()
        motor2.liberar()
        print("Recursos liberados correctamente.")

# Incluir las funciones de cálculo de retardo y movimiento del script anterior
def cm_a_pasos(coordenada_cm):
    return int(coordenada_cm * PASOS_POR_CM)

def calcular_retardo_motor(paso_actual, total_pasos, retardo_min=0.0004, retardo_max=0.001, porcentaje_aceleracion=0.1):
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

def mover_motor_en_paralelo(motor, posicion_actual, posicion_objetivo_cm, rango_max_cm, sentido_giro_1, sentido_giro_2, resultado_movimiento):
    if posicion_objetivo_cm < 0 or posicion_objetivo_cm > rango_max_cm:
        print(f"Error: Coordenada fuera de rango para el motor (0-{rango_max_cm} cm).")
        resultado_movimiento['success'] = False
        return posicion_actual

    pasos_actuales = cm_a_pasos(posicion_actual)
    pasos_objetivo = cm_a_pasos(posicion_objetivo_cm)
    pasos_a_mover = abs(pasos_objetivo - pasos_actuales)
    direccion = sentido_giro_1 if pasos_objetivo > pasos_actuales else sentido_giro_2

    print(f"Moviendo desde {posicion_actual} cm a {posicion_objetivo_cm} cm ({pasos_a_mover} pasos).")

    for paso in range(pasos_a_mover):
        retardo = calcular_retardo_motor(paso, pasos_a_mover)
        motor.mover(direccion=direccion, pasos=1, retardo=retardo)

    resultado_movimiento['success'] = True
    resultado_movimiento['posicion_final'] = posicion_objetivo_cm
    return posicion_objetivo_cm

if __name__ == "__main__":
    main()