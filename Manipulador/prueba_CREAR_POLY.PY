import cv2
import numpy as np
import os

# Forzar el uso de X11 en lugar de Wayland
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class PoligonoDibujador:
    def __init__(self):
        self.puntos = []
        self.poligono_completado = False
        
    def click_callback(self, event, x, y, flags, param):
        # Cuando se hace clic izquierdo, añadir un punto
        if event == cv2.EVENT_LBUTTONDOWN:
            if not self.poligono_completado:
                self.puntos.append((x, y))
                print(f"Punto añadido: ({x}, {y})")
                
        # Cuando se hace clic derecho, cerrar el polígono
        elif event == cv2.EVENT_RBUTTONDOWN:
            if len(self.puntos) > 2 and not self.poligono_completado:
                self.poligono_completado = True
                self.imprimir_formato_numpy()
    
    def reiniciar(self):
        self.puntos = []
        self.poligono_completado = False
        print("Polígono reiniciado")
    
    def imprimir_formato_numpy(self):
        print("\n--- COORDENADAS DEL POLIGONO ---")
        print("Copia este formato para tu código de detección de movimiento:")
        print(f"area_pts = np.array({self.puntos})")
        print("-----------------------------\n")

def main():
    # Crear la ventana antes de capturar la cámara
    cv2.namedWindow("Dibujar Poligono", cv2.WINDOW_NORMAL)
    
    # Reducir resolución para mejor rendimiento en Raspberry Pi
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Verificar si la cámara se abrió correctamente
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara.")
        return
    
    # Establecer el callback para el mouse
    dibujador = PoligonoDibujador()
    cv2.setMouseCallback("Dibujar Poligono", dibujador.click_callback)
    
    print("Instrucciones:")
    print("- Clic izquierdo: Añadir punto al polígono")
    print("- Clic derecho: Completar polígono y mostrar coordenadas")
    print("- Tecla 'r': Reiniciar polígono")
    print("- Tecla 'q': Salir")
    print("- Tecla 's': Guardar coordenadas en archivo")
    
    while True:
        # Leer un frame de la cámara
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo capturar frame.")
            break
        
        # Mostrar dimensiones del frame
        alto, ancho = frame.shape[:2]
        cv2.putText(frame, f"Dimensiones: {ancho}x{alto}", (10, alto-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Dibujar los puntos y líneas del polígono
        if len(dibujador.puntos) > 0:
            # Dibujar todos los puntos
            for i, punto in enumerate(dibujador.puntos):
                cv2.circle(frame, punto, 5, (0, 255, 0), -1)
                # Mostrar coordenadas junto a cada punto
                cv2.putText(frame, f"{i+1}: {punto}", punto, 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Dibujar líneas entre los puntos
            if len(dibujador.puntos) > 1:
                for i in range(len(dibujador.puntos) - 1):
                    cv2.line(frame, dibujador.puntos[i], dibujador.puntos[i+1], (255, 0, 0), 2)
            
            # Si el polígono está completo, dibujar la línea de cierre
            if dibujador.poligono_completado and len(dibujador.puntos) > 2:
                cv2.line(frame, dibujador.puntos[-1], dibujador.puntos[0], (255, 0, 0), 2)
                
                # Dibujar el polígono relleno con transparencia
                overlay = frame.copy()
                puntos = np.array(dibujador.puntos, np.int32)
                puntos = puntos.reshape((-1, 1, 2))
                cv2.fillPoly(overlay, [puntos], (0, 0, 255))
                alpha = 0.3  # Transparencia: 0 invisible, 1 opaco
                frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        # Mostrar el frame
        cv2.imshow("Dibujar Poligono", frame)
        
        # Capturar la tecla presionada
        tecla = cv2.waitKey(1) & 0xFF
        
        # Si se presiona 'q', salir
        if tecla == ord('q'):
            break
        # Si se presiona 'r', reiniciar el polígono
        elif tecla == ord('r'):
            dibujador.reiniciar()
        # Si se presiona 's', guardar coordenadas en un archivo
        elif tecla == ord('s') and dibujador.poligono_completado:
            with open('coordenadas_poligono.txt', 'w') as f:
                f.write(f"area_pts = np.array({dibujador.puntos})\n")
            print("Coordenadas guardadas en 'coordenadas_poligono.txt'")
    
    # Liberar recursos
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()