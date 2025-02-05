import threading
import tkinter as tk
import tkinter.ttk as ttk
import time
import json
import os
from gpiozero import PWMOutputDevice
from tkinter import messagebox,simpledialog
from tkinter import ttk, filedialog, simpledialog
from PIL import Image, ImageTk
from posicionador import mover_motores, mover_motores_manual,FinalDeCarrera
from editar_area import editar_zona_interes
from camara import iniciar_deteccion_movimiento

# Variable global para el evento de control
evento_detener = threading.Event()

class EasyPickApp:

    def __init__(self, root):

        self.root = root
        self.root.title("EasyPick - Mantenimiento")
        
        # Obtener el tamaño de la pantalla
        screen_width = self.root.winfo_screenwidth()-20
        screen_height = self.root.winfo_screenheight()-110

        # Configurar la ventana para ocupar toda la pantalla
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        
        
        # Mostrar los botones de minimizar, maximizar y cerrar
        self.root.resizable(True, True)
        
        # Variable para almacenar la imagen original y el Label central
        self.imagen_original = None
        self.imagen_label = None
        
        # Barra superior
        self.crear_barra_superior()
        
        # Menú principal
        self.crear_menu_desplegable()
        
        # Área central
        self.crear_area_central()

        self.hilo_fc = None
        self.ejecutar_hilo_fc = [True]

        self.hilo_movimiento = None
        self.ejecutar_hilo_movimiento = [True]


        # Crear los finales de carrera
        self.fc1 = FinalDeCarrera(6, "Final1")
        self.fc2 = FinalDeCarrera(7, "Final2")
        self.fc3 = FinalDeCarrera(8, "Final3")

    def detener_hilo_limpiar(self):
        # Detener los hilos
        if self.ejecutar_hilo_fc:
            self.ejecutar_hilo_fc[0] = False

        if self.ejecutar_hilo_movimiento:
            self.ejecutar_hilo_movimiento[0] = False

        # Limpiar toda la información de la pantalla
        for widget in self.area_central.winfo_children():
            widget.destroy()

    def crear_barra_superior(self):
        # Crear la barra superior
        barra_superior = tk.Frame(self.root, bg="white", height=80)
        barra_superior.pack(fill="x", side="top")

        # Ruta de las imágenes
        ruta_imagen_1 = "img/easyPick_2.png"
        ruta_imagen_2 = "img/LogoColsein.png"

        # Cargar y redimensionar la primera imagen
        imagen_original_1 = Image.open(ruta_imagen_1)
        imagen_redimensionada_1 = imagen_original_1.resize((180,70))# Ajusta el tamaño (ancho, alto)
        logo_1 = ImageTk.PhotoImage(imagen_redimensionada_1)

        # Cargar y redimensionar la segunda imagen
        imagen_original_2 = Image.open(ruta_imagen_2)
        imagen_redimensionada_2 = imagen_original_2.resize((200, 70))  # Ajusta el tamaño (ancho, alto)
        logo_2 = ImageTk.PhotoImage(imagen_redimensionada_2)

        # Crear el Label para la primera imagen
        logo_label_1 = tk.Label(barra_superior, image=logo_1, bg="white")
        logo_label_1.image = logo_1  # Prevenir que el recolector de basura elimine la imagen
        logo_label_1.pack(side="left")  # Posicionar la primera imagen a la izquierda

        # Crear el Label para la segunda imagen
        logo_label_2 = tk.Label(barra_superior, image=logo_2, bg="white")
        logo_label_2.image = logo_2  # Prevenir que el recolector de basura elimine la imagen
        logo_label_2.pack(side="right")  # Posicionar la segunda imagen a la derecha

    def crear_menu_desplegable(self):

        self.fuente=("Open Sans", 14)
        self.fuente_2=("Open Sans", 14, "bold")

        # Fuente de todos los menús
        self.root.option_add("*Menu.font", self.fuente)

        # Crear la barra de menús
        menu_principal = tk.Menu(self.root)

        #Separador
        separador_menu = 0

        # Crear el submenú Posicionador
        menu_posicionador = tk.Menu(menu_principal, tearoff=separador_menu)
        menu_posicionador.add_command(label="Coordenadas", command=self.accion_posicionador_coordenadas)
        menu_posicionador.add_command(label="Manual", command=self.accion_posicionador_manual)

        # Crear el submenú Eyector
        menu_eyector = tk.Menu(menu_principal, tearoff=separador_menu)
        menu_eyector.add_command(label="General", command=self.accion_eyector)

        # Crear el submenú cámara
        menu_camara = tk.Menu(menu_principal, tearoff=separador_menu)
        menu_camara.add_command(label="Área", command=self.accion_area_deteccion)

        # Crear el submenú finales de carrera
        menu_finales_carrera = tk.Menu(menu_principal, tearoff=separador_menu)
        menu_finales_carrera.add_command(label="General", command=self.accion_finales_carrera)

        # Crear el submenú estantería
        menu_estanteria = tk.Menu(menu_principal, tearoff=separador_menu)
        menu_estanteria.add_command(label="Separadores", command=self.accion_estanteria)


        # Crear un menú vacío como separador para empujar "Salir" al extremo derecho
        menu_separador = tk.Menu(menu_principal, tearoff=separador_menu)

        # Agregar submenús al menú principal
        menu_principal.add_cascade(label="Posicionador", menu=menu_posicionador)
        menu_principal.add_cascade(label="Eyector", menu=menu_eyector)
        menu_principal.add_cascade(label="Cámara", menu=menu_camara)
        menu_principal.add_cascade(label="Finales de carrera", menu=menu_finales_carrera)
        menu_principal.add_cascade(label="Estantería", menu=menu_estanteria)
        menu_principal.add_command(label="Inventario", command=self.accion_inventario)

        #Espacio 
        menu_principal.add_cascade(label="                                                    ", 
                                    menu=menu_separador)  # Menú vacío como espacio

        # Agregar la opción "Salir" directamente al menú principal
        menu_principal.add_command(label="Salir", command=self.root.destroy)
        

        # Configurar el menú en la ventana raíz
        self.root.config(menu=menu_principal)

    def crear_area_central(self):
        self.area_central = tk.Frame(self.root, bg="white")
        self.area_central.pack(fill="both", expand=True)

        # Obtener el tamaño de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        ancho_canvas =screen_width-125
        alto_canvas  =screen_height-300

        self.canvas = tk.Canvas(self.area_central, width=ancho_canvas, height=alto_canvas, bg="white", bd=5, highlightthickness=5)
        self.canvas.place(x=(screen_width/2)-500, y=(screen_height/2)-900)  # Coloca el Canvas a 50px del borde izquierdo y 100px del borde superior
        
        imagen_original = Image.open("img/LogoPrincipal.png")

        # Redimensionar la imagen
        imagen_redimensionada = imagen_original.resize((650, 650))
        self.imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)

        # Limpiar la imagen actual del Canvas si es necesario
        self.canvas.delete("all")

        # Colocar la nueva imagen en el Canvas
        self.canvas.create_image((ancho_canvas/2), (alto_canvas/2), image=self.imagen_tk, anchor="center")
        self.canvas.imagen_ref = self.imagen_tk  # Mantener una referencia para que no se elimine la imagen

    # Funciones para los movimientos por coordenadas

    def accion_posicionador_coordenadas(self):
        #print("Posicionador por coordenadas activado")

        # Detener los hilos
        if self.ejecutar_hilo_fc:
            self.ejecutar_hilo_fc[0] = False

        if self.ejecutar_hilo_movimiento:
            self.ejecutar_hilo_movimiento[0] = False
        
        # Limpiar toda la información de la pantalla
        for widget in self.area_central.winfo_children():
            widget.destroy()

        # Obtener el tamaño de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Crear un Canvas con tamaño fijo y borde
        self.canvas = tk.Canvas(
            self.area_central,
            width=700,
            height=700,
            bg="white",
            bd=5,
            highlightthickness=5
        )
        self.canvas.place(
            x=(screen_width / 2)- 350, 
            y=(screen_height / 2) - 100
        )  # Centrar el canvas en la pantalla

        self.canvas_img = tk.Canvas(
            self.area_central,
            width=700,
            height=700,
            bg="white",
            bd=5,
            highlightthickness=5
        )
        self.canvas_img.place(
            x=(screen_width / 2)- 350,
            y=(screen_height / 2) - 900
        )  # Centrar el canvas en la pantalla

        # Cargar la imagen
        imagen_original = Image.open("img/mov_coor.PNG")  # Cambia esto a la ruta de tu imagen
        imagen_redimensionada = imagen_original.resize((600, 600))  # Opcional: Redimensionar la imagen
        imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)
        
        # Colocar la imagen en el Canvas
        self.canvas_img.create_image(350, 350, 
                                        image=imagen_tk, 
                                        anchor="center")  # Coordenadas x=200, y=200
        self.canvas_img.imagen_ref = imagen_tk  # Mantener una referencia para que no se elimine la imagen
        

        # Crear entradas directamente sobre el Canvas
        self.entradas = []  # Lista para almacenar las entradas X y Z
        max_coordenadas = 15  # Máximo de coordenadas permitidas

        # Coordenadas iniciales en el Canvas
        x_inicial = 100
        y_inicial = 50
        espacio_vertical = 40

        for i in range(max_coordenadas):
            y_pos = y_inicial + (i * espacio_vertical)

            # Unicode para subíndices (i+1 → como subíndice)
            subindice = ''.join(chr(8320 + int(digito)) for digito in str(i + 1))


            # Etiqueta y entrada para el valor X
            label_x = tk.Label(self.canvas, 
                                        text=f"Coordenada X{subindice}: ", 
                                        bg="white", 
                                        font=self.fuente)

            self.canvas.create_window(x_inicial, y_pos, 
                                        window=label_x, 
                                        anchor="w")

            entrada_x = tk.Entry(self.canvas, 
                                        width=5, 
                                        justify="center",
                                        font=self.fuente)

            entrada_x.insert(0, "0")
            self.canvas.create_window(x_inicial + 180, y_pos, 
                                        window=entrada_x, 
                                        anchor="w")

            # Etiqueta y entrada para el valor Z
            label_z = tk.Label(self.canvas, 
                                        text=f"Coordenada Z{subindice}: ", 
                                        bg="white", 
                                        font=self.fuente)

            self.canvas.create_window(x_inicial + 275, y_pos, 
                                        window=label_z, 
                                        anchor="w")

            entrada_z = tk.Entry(self.canvas, 
                                        width=5, 
                                        justify="center",
                                        font=self.fuente)

            entrada_z.insert(0, "0")
            self.canvas.create_window(x_inicial + 450, y_pos, 
                                        window=entrada_z, 
                                        anchor="w")

            # Almacenar las entradas en una lista como tuplas (entrada_x, entrada_z)
            self.entradas.append((entrada_x, entrada_z))

        # Botón para detener el movimiento
        boton_detener = tk.Button(self.canvas, 
                                        text="Detener", 
                                        command=self.detener_posicionador, 
                                        font=self.fuente_2)
        self.canvas.create_window(260, y_inicial + (max_coordenadas * espacio_vertical) + 20, window=boton_detener)

        # Botón para enviar los datos
        boton_aceptar = tk.Button(self.canvas, 
                                        text="Aceptar", 
                                        command=self.activar_posicionador, 
                                        font=self.fuente_2)
        self.canvas.create_window(400, y_inicial + (max_coordenadas * espacio_vertical) + 20, window=boton_aceptar)

        # Botón Home
        boton_home = tk.Button(self.canvas, 
                                        text="Home", 
                                        command=self.mover_motores_home, 
                                        font=self.fuente_2)
        self.canvas.create_window(540, y_inicial + (max_coordenadas * espacio_vertical) + 20, window=boton_home)

    def activar_posicionador(self):
        #print("Iniciar función por medio de coordenadas")

        # Lista para almacenar las coordenadas ingresadas
        coordenadas = []

        # Recorrer cada par de entradas (X, Z) y obtener sus valores
        for entrada_x, entrada_z in self.entradas:
            valor_x = int(entrada_x.get())  # Obtener valor de X como entero
            valor_z = int(entrada_z.get())  # Obtener valor de Z como entero
            coordenadas.append((valor_z,valor_x))  # Agregar como tupla a la lista

        # Imprimir todas las coordenadas
        #print("las coordenadas enviadas posicionador son :",coordenadas)

        self.homing_lineal(self.fc3)
        self.detener_ejecucion = False
        self.ejecutar_hilo_movimiento = [True]
        self.hilo_movimiento = threading.Thread(
            target=mover_motores, 
            args=(coordenadas, lambda: self.detener_ejecucion, self.fc1, self.fc2, self.fc3, self.ejecutar_hilo_movimiento)
        )
        self.hilo_movimiento.daemon = True
        self.hilo_movimiento.start()

    def detener_posicionador(self):
        # Detener los hilos
        if self.ejecutar_hilo_movimiento:
            self.ejecutar_hilo_movimiento[0] = False
            #print("Detención activada. Los motores se detendrán.")
    
    # Funciones para los movimientos manuales

    # Inicializar atributos requeridos
    coordenada_actual = [(0, 0)]  # Formato inicial: [(x, y)]
    rango_x = [0,50]  # Rango permitido en el eje X
    rango_z = [0,60]  # Rango permitido en el eje Z

    def accion_posicionador_manual(self):
        #print("Posicionador manual activado")

        # Detener los hilos
        if self.ejecutar_hilo_fc:
            self.ejecutar_hilo_fc[0] = False

        if self.ejecutar_hilo_movimiento:
            self.ejecutar_hilo_movimiento[0] = False

        # Limpiar toda la información de la pantalla
        for widget in self.area_central.winfo_children():
            widget.destroy()

        # Obtener el tamaño de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(self.area_central, width=700, height=700, bg="white", bd=5, highlightthickness=5)
        self.canvas.place(
            x=(screen_width/2)-350, 
            y=(screen_height/2)-100)  # Coloca el Canvas a 50px del borde izquierdo y 100px del borde superior

        self.canvas_img = tk.Canvas(
            self.area_central,
            width=700,
            height=700,
            bg="white",
            bd=5,
            highlightthickness=5
        )
        self.canvas_img.place(
            x=(screen_width / 2)-350, 
            y=(screen_height / 2) - 900
        )  # Centrar el canvas en la pantalla

        # Cargar la imagen
        imagen_original = Image.open("img/mov_man.PNG")  # Cambia esto a la ruta de tu imagen
        imagen_redimensionada = imagen_original.resize((600, 600))  # Opcional: Redimensionar la imagen
        imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)
        
        # Colocar la imagen en el Canvas
        self.canvas_img.create_image(350, 350, 
                                            image=imagen_tk, 
                                            anchor="center") 
        self.canvas_img.imagen_ref = imagen_tk  # Mantener una referencia para que no se elimine la imagen
        

        # Crear y ubicar una etiqueta y entrada dentro del Canvas
        movimiento_label = tk.Label(self.canvas, 
                                            text="Movimiento en cm:", 
                                            bg="white", 
                                            font=self.fuente_2)
        self.canvas.create_window(350, 250, window=movimiento_label)  # Posición de la etiqueta en el Canvas

        self.entrada = tk.Entry(self.canvas, 
                                            width=10, 
                                            justify="center")
        self.entrada.insert(0, "10")  # Valor inicial
        self.canvas.create_window(350, 300, window=self.entrada) 

        boton_home = tk.Button(self.canvas, 
                                            text="Home", 
                                            command=self.mover_motores_home,  # Función al presionar el botón
                                            bg="#00AADA", 
                                            fg="black", 
                                            font=self.fuente_2)
        self.canvas.create_window(350, 350, window=boton_home)  # Posición del botón en el Canvas

        # Flecha hacia arriba (posición 350, 150)
        arriba = [
            350, 100,  # Punta superior
            375, 150,  # Derecha
            365, 150,  # Bajo derecha
            365, 200,  # Base derecha
            335, 200,  # Base izquierda
            335, 150,  # Bajo izquierda
            325, 150   # Izquierda
        ]
        self.canvas.create_polygon(arriba, 
                                            fill="#00AADA", 
                                            outline="black", 
                                            width=2, 
                                            tags="arriba")

        # Flecha hacia abajo (posición 350, 450)
        abajo = [
            350, 500,  # Punta inferior
            375, 450,  # Derecha
            365, 450,  # Alto derecha
            365, 400,  # Base derecha
            335, 400,  # Base izquierda
            335, 450,  # Alto izquierda
            325, 450   # Izquierda
        ]
        self.canvas.create_polygon(abajo, 
                                            fill="#00AADA", 
                                            outline="black", 
                                            width=2, 
                                            tags="abajo")

        # Flecha hacia la derecha (posición 500, 300)
        derecha = [
            550, 300,  # Punta derecha
            500, 325,  # Arriba
            500, 315,  # Medio arriba
            450, 315,  # Base arriba
            450, 285,  # Base abajo
            500, 285,  # Medio abajo
            500, 275   # Abajo
        ]
        self.canvas.create_polygon(derecha, 
                                            fill="#00AADA", 
                                            outline="black", 
                                            width=2, 
                                            tags="derecha")

        # Flecha hacia la izquierda (posición 200, 300)
        izquierda = [
            150, 300,   # Punta izquierda
            200, 325,   # Abajo
            200, 315,   # Medio abajo
            240, 315,   # Base abajo
            240, 285,   # Base arriba
            200, 285,   # Medio arriba
            200, 275    # Arriba
        ]
        self.canvas.create_polygon(izquierda, 
                                            fill="#00AADA", 
                                            outline="black", 
                                            width=2, 
                                            tags="izquierda")

        # Asociar eventos de clic
        self.canvas.tag_bind("arriba", "<Button-1>", lambda e: self.procesar_evento("arriba"))
        self.canvas.tag_bind("abajo", "<Button-1>", lambda e: self.procesar_evento("abajo"))
        self.canvas.tag_bind("derecha", "<Button-1>", lambda e: self.procesar_evento("derecha"))
        self.canvas.tag_bind("izquierda", "<Button-1>", lambda e: self.procesar_evento("izquierda"))

        self.root.after(100, self.mover_motores_home)  # Ejecutar después de 100 ms

    def procesar_evento(self, direccion):
        if direccion == "arriba":
            self.actualizar_img(img="img/mani_sube.PNG")
            self.root.update()  # Forzar a Tkinter a actualizar la pantalla
            self.movimiento_arriba()
        elif direccion == "abajo":
            self.actualizar_img(img="img/mani_baja.PNG")
            self.root.update()
            self.movimiento_abajo()
        elif direccion == "derecha":
            self.actualizar_img(img="img/mani_der.PNG")
            self.root.update()
            self.movimiento_derecha()
        elif direccion == "izquierda":
            self.actualizar_img(img="img/mani_izq.PNG")
            self.root.update()
            self.movimiento_izquierda()

    def movimiento_arriba(self):
        # Movimiento hacia arriba (disminuye Y)
        distancia = self.entrada.get()
        distancia = int(distancia)
        #print("los pasos son:",distancia)
        if self.coordenada_actual[0][1] - distancia >= self.rango_z[0]:
            nueva_y = self.coordenada_actual[0][1] - distancia
            self.coordenada_actual = [(self.coordenada_actual[0][0], nueva_y)]

            x = 0
            z = distancia
            direccion=0

            # Ejecutar la función de movimiento en un hilo separado
            mover_motores_manual(x,z,direccion)
        else:
            #print("Movimiento hacia arriba no permitido.")
            messagebox.showerror(title="Error de movimiento", message=" No se puede realizar este movimiento ")

    def movimiento_abajo(self):
        # Movimiento hacia abajo (aumenta Y)
        distancia = self.entrada.get()
        distancia = int(distancia)
        #print("los pasos son:",distancia)
        if self.coordenada_actual[0][1] + distancia <= self.rango_z[1]:
            nueva_y = self.coordenada_actual[0][1] + distancia
            self.coordenada_actual = [(self.coordenada_actual[0][0], nueva_y)]

            x = 0
            z = distancia
            direccion=1

            # Ejecutar la función de movimiento en un hilo separado
            mover_motores_manual(x,z,direccion)

        else:
            #print("Movimiento hacia arriba no permitido.")
            messagebox.showerror(title="Error de movimiento", message=" No se puede realizar este movimiento ")

    def movimiento_derecha(self):
        # Movimiento hacia la derecha (aumenta X)
        distancia = self.entrada.get()
        distancia = int(distancia)
        #print("los pasos son:",distancia)
        if self.coordenada_actual[0][0] + distancia <= self.rango_x[1]:
            nueva_x = self.coordenada_actual[0][0] + distancia
            self.coordenada_actual = [(nueva_x, self.coordenada_actual[0][1])]

            z = 0
            x = distancia
            direccion=1
            # Ejecutar la función de movimiento en un hilo separado
            mover_motores_manual(x,z,direccion)
        else:
            #print("Movimiento hacia arriba no permitido.")
            messagebox.showerror(title="Error de movimiento", message=" No se puede realizar este movimiento ")

    def movimiento_izquierda(self):
        # Movimiento hacia la izquierda (disminuye X)
        distancia = self.entrada.get()
        distancia = int(distancia)
        #print("los pasos son:",distancia)
        if self.coordenada_actual[0][0] - distancia >= self.rango_x[0]:
            nueva_x = self.coordenada_actual[0][0] - distancia
            self.coordenada_actual = [(nueva_x, self.coordenada_actual[0][1])]

            z = 0
            x = distancia
            direccion=0
            # Ejecutar la función de movimiento en un hilo separado
            mover_motores_manual(x,z,direccion)
        else:
            #print("Movimiento hacia arriba no permitido.")
            messagebox.showerror(title="Error de movimiento", message=" No se puede realizar este movimiento ")
    
    def mover_motores_home(self):
        #print("Moviendo motores a la posición de home...")
        # Detener los hilos
        if self.ejecutar_hilo_fc:
            self.ejecutar_hilo_fc[0] = False

        if self.ejecutar_hilo_movimiento:
            self.ejecutar_hilo_movimiento[0] = False
        
        self.coordenada_actual = [(0, 0)]  # Formato inicial: [(x, y)]
        coordenadas=[]
        self.homing_lineal(self.fc3)
        mover_motores(coordenadas, lambda: self.detener_ejecucion,self.fc1,self.fc2,self.fc3,ejecutar=[True])
        #print("Motores en la posición home.")

    def actualizar_img(self,img):

        # Limpiar la imagen actual del Canvas si es necesario
        self.canvas_img.delete("all")

        # Obtener el tamaño de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        self.canvas_img = tk.Canvas(
        self.area_central,
        width=700,
        height=700,
        bg="white",
        bd=5,
        highlightthickness=5
        )
        self.canvas_img.place(
            x=(screen_width / 2)-350, 
            y=(screen_height / 2) - 900
        )  # Centrar el canvas en la pantalla

        # Cargar la imagen
        imagen_original = Image.open(img)  # Cambia esto a la ruta de tu imagen
        imagen_redimensionada = imagen_original.resize((600, 600))  # Opcional: Redimensionar la imagen
        imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)
        
        # Colocar la imagen en el Canvas
        self.canvas_img.create_image(350, 350, image=imagen_tk, anchor="center")  # Coordenadas x=200, y=200
        self.canvas_img.imagen_ref = imagen_tk  # Mantener una referencia para que no se elimine la imagen

    # Funciones de la opcion de la camara 

    def accion_area_deteccion(self):

        #print("Ejecutando área de detección")
        
        # Limpiar toda la información de la pantalla
        for widget in self.area_central.winfo_children():
            widget.destroy()

        # Obtener el tamaño de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(self.area_central, width=700, height=700, bg="white", bd=5, highlightthickness=5)
        self.canvas.place(
            x=(screen_width/2)-350, 
            y=(screen_height/2)-500)  # Coloca el Canvas a 50px del borde izquierdo y 100px del borde superior

        # Cargar la imagen
        imagen_original = Image.open("img/iconocam.png")  # Cambia esto a la ruta de tu imagen
        imagen_redimensionada = imagen_original.resize((300, 300))  # Opcional: Redimensionar la imagen
        imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)
        
        # Colocar la imagen en el Canvas
        self.canvas.create_image(350, 350, image=imagen_tk, anchor="center")  # Coordenadas x=200, y=200
        self.canvas.imagen_ref = imagen_tk  # Mantener una referencia para que no se elimine la imagen

        # Lista desplegable (Combobox)
        opciones = ["Cámara 1", "Cámara 2", "Cámara 3"]  # Lista de opciones
        self.combobox = ttk.Combobox(self.area_central, 
                                        values=opciones, 
                                        state="readonly", 
                                        font=self.fuente)

        self.combobox.set("Cámara 1")  # Texto inicial
        self.canvas.create_window(350, 550, window=self.combobox)  # Posición del Combobox en el Canvas

        boton_area = tk.Button(self.canvas, 
                                        text="Definir área de detección", 
                                        command=self.editar_area,  # Función al presionar el botón
                                        bg="#00AADA", 
                                        fg="#031C3A", 
                                        font=self.fuente)

        self.canvas.create_window(350, 600, window=boton_area)  # Posición del botón en el Canvas
    
    def editar_area(self):

        seleccion = self.combobox.get()  # Obtén la opción seleccionada
        #print(f"Seleccionaste: {seleccion}")
        
        # Ejecutar acción según la opción seleccionada
        if seleccion == "Cámara 1":
            self.mostrar_roi(num_cam=0)
        elif seleccion == "Cámara 2":
            self.mostrar_roi(num_cam=1)
        elif seleccion == "Cámara 3":
            self.mostrar_roi(num_cam=2)
        else:
            print("No se ha seleccionado una opción válida")
    
    def mostrar_roi(self,num_cam):

        #print("Mostrar area de interes")

        # Limpiar toda la información de la pantalla
        self.detener_hilo_limpiar()

        # Obtener el tamaño de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(self.area_central, 
                                        width=700, 
                                        height=700, 
                                        bg="white", 
                                        bd=5, 
                                        highlightthickness=5)

        self.canvas.place(x=(screen_width/2)-350, y=(screen_height/2)-500) 

        # Leer el archivo JSON
        with open(f'roi_cam_1.json', 'r') as archivo:
            datos_cam_1 = json.load(archivo)  # Cargar el contenido como un diccionario
        with open(f'roi_cam_2.json', 'r') as archivo:
            datos_cam_2 = json.load(archivo)  # Cargar el contenido como un diccionario
        with open(f'roi_cam_3.json', 'r') as archivo:
            datos_cam_3 = json.load(archivo)  # Cargar el contenido como un diccionario

        

        # Acceder a los valores
        x_1     = datos_cam_1['x_1']
        y_1     = datos_cam_1['y_1']
        ancho_1 = datos_cam_1['ancho_1']
        alto_1  = datos_cam_1['alto_1']

        x_2     = datos_cam_2['x_2']
        y_2     = datos_cam_2['y_2']
        ancho_2 = datos_cam_2['ancho_2']
        alto_2  = datos_cam_2['alto_2']

        x_3     = datos_cam_3['x_3']
        y_3     = datos_cam_3['y_3']
        ancho_3 = datos_cam_3['ancho_3']
        alto_3  = datos_cam_3['alto_3']

        # Usar los valores (por ejemplo, imprimirlos)
        print(f"x: {x_1},{y_1},{ancho_1},{alto_1}")

        # Variables de coordenadas para cada cámara
        coordenadas = [
            {"x": x_1, "y": y_1, "ancho": ancho_1, "alto": alto_1},  # Cámara 1
            {"x": x_2, "y": y_2, "ancho": ancho_2, "alto": alto_2},  # Cámara 2
            {"x": x_3, "y": y_3, "ancho": ancho_3, "alto": alto_3}   # Cámara 3
        ]

        # Desplazamiento vertical entre filas
        desplazamiento_y = 200

        # Crear elementos para cada cámara
        self.crear_elementos(num_cam, coordenadas[num_cam], desplazamiento_y * 1)

    def crear_elementos(self, cam_index, coords, offset_y):
        # Etiqueta de la cámara
        cam_label = tk.Label(self.canvas, 
                                        text=f"Cámara {cam_index + 1}", 
                                        bg="white", 
                                        font=self.fuente_2)

        self.canvas.create_window(350, 50 + offset_y, 
                                        window=cam_label)

        # Etiquetas de las coordenadas
        labels = ["X", "Y", "Ancho", "Alto"]
        pos_x = [150, 300, 450, 600]
        for j, label in enumerate(labels):
            lbl = tk.Label(self.canvas, 
                                        text=label, 
                                        bg="white", 
                                        font=self.fuente_2)
            self.canvas.create_window(pos_x[j], 100 + offset_y, window=lbl)

        # Entradas con valores iniciales
        entradas = [coords['x'], coords['y'], coords['ancho'], coords['alto']]
        for j, valor in enumerate(entradas):
            entrada = tk.Entry(self.canvas, 
                                        width=10, 
                                        justify="center")
            entrada.insert(0, valor)
            self.canvas.create_window(pos_x[j], 150 + offset_y, 
                                        window=entrada)

        boton_area = tk.Button(self.canvas, 
                                        text=f"Definir ROI de cam {cam_index + 1}",
                                        command=lambda:self.procesar_area_cam(estado_area=f"acam {cam_index + 1}"),
                                        bg="#00AADA", 
                                        fg="#031C3A", 
                                        font=self.fuente_2
        )
        # Posición del botón justo debajo de las entradas
        self.canvas.create_window(250, 200 + offset_y, window=boton_area) 

        boton_prueba = tk.Button(self.canvas, 
                                        text=f"Probar cam {cam_index + 1}",
                                        command=lambda:self.procesar_prueba_cam(estado_prueba=f"pcam {cam_index + 1}"),
                                        bg="#00AADA", 
                                        fg="#031C3A", 
                                        font=self.fuente_2)
        # Posición del botón justo debajo de las entradas
        self.canvas.create_window(450, 200 + offset_y, window=boton_prueba) 

    def procesar_area_cam(self, estado_area):
        # Crear la barra superior solo si es la dirección 'arriba'
        if estado_area == "acam 1":
            #print("acam 1")
            messagebox.showinfo(title="Información", 
                                        message=" Para reiniciar el area demarcada presione 'r' y para confirmar la seleción presione 'c' ")
            editar_zona_interes(self,pref=1)
            self.mostrar_roi(num_cam=0)
        elif estado_area == "acam 2":
            #print("acam 2")
            messagebox.showinfo(title="Información", 
                                        message=" Para reiniciar el area demarcada presione 'r' y para confirmar la seleción presione 'c' ")
            editar_zona_interes(self,pref=2)
            self.mostrar_roi(num_cam=1)
        elif estado_area == "acam 3":
            #print("acam 3")
            messagebox.showinfo(title="Información", 
                                        message=" Para reiniciar el area demarcada presione 'r' y para confirmar la seleción presione 'c' ")
            editar_zona_interes(self,pref=3)
            self.mostrar_roi(num_cam=2)

    def procesar_prueba_cam(self, estado_prueba):
        # Crear la barra superior solo si es la dirección 'arriba'
        if estado_prueba == "pcam 1":
            #print("pcam 1")
            # Abre el archivo JSON
            messagebox.showinfo(title="Información", message=" Presione la tecla 'q' para finalizar la prueba.")
            with open('roi_cam_1.json', 'r') as file:
                # Cargar los datos desde el archivo JSON
                data = json.load(file)
                # Obtener los parámetros específicos
                x_1 = data.get("x_1", None)
                y_1 = data.get("y_1", None)
                ancho_1 = data.get("ancho_1", None)
                alto_1 = data.get("alto_1", None)
                camara=0
                iniciar_deteccion_movimiento(x_1,y_1,ancho_1,alto_1,camara)
        elif estado_prueba == "pcam 2":
            #print("pcam 2")
            # Abre el archivo JSON
            messagebox.showinfo(title="Información", message=" Presione la tecla 'q' para finalizar la prueba.")
            with open('roi_cam_2.json', 'r') as file:
                # Cargar los datos desde el archivo JSON
                data = json.load(file)
                # Obtener los parámetros específicos
                x_2 = data.get("x_2", None)
                y_2 = data.get("y_2", None)
                ancho_2 = data.get("ancho_2", None)
                alto_2 = data.get("alto_2", None)
                camara=0
                iniciar_deteccion_movimiento(x_2,y_2,ancho_2,alto_2,camara)
        elif estado_prueba == "pcam 3":
            #print("pcam 3")
            # Abre el archivo JSON
            messagebox.showinfo(title="Información", message=" Presione la tecla 'q' para finalizar la prueba.")
            with open('roi_cam_3.json', 'r') as file:
                # Cargar los datos desde el archivo JSON
                data = json.load(file)
                # Obtener los parámetros específicos
                x_3 = data.get("x_3", None)
                y_3 = data.get("y_3", None)
                ancho_3 = data.get("ancho_3", None)
                alto_3 = data.get("alto_3", None)
                camara=0
                iniciar_deteccion_movimiento(x_3,y_3,ancho_3,alto_3,camara)

    # Funciones de la opción del eyector

    def accion_eyector(self):

        #print("Ejecutando accion de eyector")
        
        # Limpiar toda la información de la pantalla
        self.detener_hilo_limpiar()

        # Obtener el tamaño de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(self.area_central, 
                                        width=700, 
                                        height=700, 
                                        bg="white", 
                                        bd=5, 
                                        highlightthickness=5)
        self.canvas.place(x=(screen_width/2)-350, y=(screen_height/2)-500)  # Coloca el Canvas a 50px del borde izquierdo y 100px del borde superior

        
        # Cargar la imagen
        imagen_original = Image.open("img/eyec.PNG")  # Cambia esto a la ruta de tu imagen
        imagen_redimensionada = imagen_original.resize((500, 500))  # Opcional: Redimensionar la imagen
        imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)
        
        # Colocar la imagen en el Canvas
        self.canvas.create_image(350, 200, 
                                        image=imagen_tk, 
                                        anchor="center") 
        self.canvas.imagen_ref = imagen_tk  # Mantener una referencia para que no se elimine la imagen
        
        # Crear y ubicar la etiqueta
        tk.Label(self.canvas,
                                        text=f"Velocidad:  ",
                                        bg="white",
                                        font=self.fuente_2
                                        ).place(x=150, y=450)  # Coordenadas absolutas dentro del frame

        # Crear y ubicar la entrada
        self.entrada_v = tk.Entry(self.canvas, 
                                        width=10, 
                                        justify="center")
        self.entrada_v.insert(0, "0.5") 
        self.entrada_v.place(x=250, y=450)  # Coordenadas absolutas dentro del frame

        # Crear y ubicar la etiqueta
        tk.Label(
                                        self.canvas,
                                        text=f"Tiempo:  ",
                                        bg="white",
                                        font=self.fuente_2).place(x=350, y=450)  # Coordenadas absolutas dentro del frame

        # Crear y ubicar la entrada
        self.entrada_t = tk.Entry(self.canvas, 
                                        width=10, 
                                        justify="center")
        self.entrada_t.insert(0, "0.5") 
        self.entrada_t.place(x=450, y=450)  # Coordenadas absolutas dentro del frame

        boton_expandir = tk.Button(self.canvas, 
                                        text="Expandir", 
                                        command=self.expandir_alineal,  # Función al presionar el botón
                                        bg="#00AADA", 
                                        fg="#031C3A", 
                                        font=self.fuente_2)
        self.canvas.create_window(233, 550, window=boton_expandir)  # Posición del botón en el Canvas

        boton_retraer = tk.Button(self.canvas, 
                                        text="Retraer", 
                                        command=self.retraer_alineal,  # Función al presionar el botón
                                        bg="#00AADA", 
                                        fg="#031C3A", 
                                        font=self.fuente_2)
        self.canvas.create_window(466, 550, window=boton_retraer)  # Posición del botón en el Canvas

    def expandir_alineal(self):

        RPWM = PWMOutputDevice(18)
        LPWM = PWMOutputDevice(19)
        velocidad= float(self.entrada_v.get())
        tiempo= float(self.entrada_t.get())
        if 0<velocidad<=1: 
            if 0.1<tiempo<=10:   
                #print("Expandir")
                RPWM.value = velocidad
                LPWM.value = 0
                time.sleep(tiempo)
            else:
                print("error con el valor de tiempo")
                messagebox.showerror(title="Error de movimiento", message="El valor de tiempo  debe estar entre 0.1 y 10")
        else:
            print("error con el valor de la velocidad")
            messagebox.showerror(title="Error de movimiento", message="El valor de velocidad  debe estar entre 0.1 y 1")

    def retraer_alineal (self):
        #print("Retraer")
        # Configuración de los pines
        RPWM = PWMOutputDevice(18)
        LPWM = PWMOutputDevice(19)
        velocidad= float(self.entrada_v.get())
        tiempo= float(self.entrada_t.get())
        if 0<velocidad<=1: 
            if 0.1<tiempo<=10:   
                #print("Expandir")
                RPWM.value = 0
                LPWM.value = velocidad
                time.sleep(tiempo) 
            else:
                print("error con el valor de tiempo")
                messagebox.showerror(title="Error de movimiento", message="El valor de tiempo  debe estar entre 0.1 y 10")
        else:
            print("error con el valor de la velocidad")
            messagebox.showerror(title="Error de movimiento", message="El valor de velocidad  debe estar entre 0.1 y 1")

    def homing_lineal(self,final_carrera):
        """
        Realiza el proceso de homing para ,motor lineal.
        """
        #print(f"Iniciando homing del motor lineal")

        RPWM = PWMOutputDevice(18)
        LPWM = PWMOutputDevice(19)

        RPWM.value = 0
        LPWM.value = 1
        time.sleep(0.5) 
        while not final_carrera.esta_activado():
            RPWM.value = 0
            LPWM.value = 1
            time.sleep(0.5)  
        #print(f"Motor lineal alcanzó el final de carrera.")
        time.sleep(1)
    
    # Funciones de la opción finales de carrera

    def accion_finales_carrera(self):

        #print("Monitoreo de finales de carrera")

        # Detener los hilos
        if self.ejecutar_hilo_fc:
            self.ejecutar_hilo_fc[0] = False

        if self.ejecutar_hilo_movimiento:
            self.ejecutar_hilo_movimiento[0] = False

        # Limpiar toda la información de la pantalla
        for widget in self.area_central.winfo_children():
            widget.destroy()

        # Obtener el tamaño de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(self.area_central, width=700, height=700, bg="white", bd=5, highlightthickness=5)
        self.canvas.place(x=(screen_width/2)-350, y=(screen_height/2)-500)  # Coloca el Canvas a 50px del borde izquierdo y 100px del borde superior


        # Activamos la bandera y creamos el nuevo hilo*-
        self.ejecutar_hilo_fc = [True]
        self.hilo_fc = threading.Thread(target=self.monitorear_finales_de_carrera, args=(self.ejecutar_hilo_fc,))
        self.hilo_fc.daemon = True
        self.hilo_fc.start()

    def monitorear_finales_de_carrera(self, ejecutar):

        self.fc1_monitoreo = self.fc1  
        self.fc2_monitoreo = self.fc2
        self.fc3_monitoreo = self.fc3

        try:
            # Función que actualiza la imagen sin parpadeo
            def actualizar_imagen():
                # Comprobar el estado de los finales de carrera usando el método `esta_activado()`
                if self.fc1_monitoreo.esta_activado():  # Usar esta_activado() en lugar de is_pressed
                    #print("FC1 activado")
                    imagen_original = Image.open("img/fc2.PNG")
                elif self.fc2_monitoreo.esta_activado():
                    #print("FC2 activado")
                    imagen_original = Image.open("img/fc1.PNG")
                elif self.fc3_monitoreo.esta_activado():
                    #print("FC3 activado")
                    imagen_original = Image.open("img/fc3.PNG")
                else:
                    #print("Ninguno activado")
                    imagen_original = Image.open("img/fc.PNG")

                # Redimensionar la imagen
                imagen_redimensionada = imagen_original.resize((650, 650))
                self.imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)

                # Limpiar la imagen actual del Canvas si es necesario
                self.canvas.delete("all")

                # Colocar la nueva imagen en el Canvas
                self.canvas.create_image(350, 350, image=self.imagen_tk, anchor="center")
                self.canvas.imagen_ref = self.imagen_tk  # Mantener una referencia para que no se elimine la imagen

                # Reprogramar la próxima actualización en 500 ms
                if ejecutar[0]:  # Si la ejecución sigue activa
                    #print("-------------------")
                    self.canvas.after(500, actualizar_imagen)  # Llama a la función de actualización después de 500ms

            # Iniciar el proceso de actualización de imágenes
            actualizar_imagen()

            #print("Monitoreo iniciado...")

        except Exception as e:
            print(f"Error durante el monitoreo: {e}")

    def liberar_pines(self):
        # Liberar los pines de los finales de carrera
        self.fc1.liberar_pin()
        self.fc2.liberar_pin()
        self.fc3.liberar_pin()
        
    # Funciones de la opción Estanterìa

    def accion_estanteria(self):

        self.detener_hilo_limpiar()

        print("Accion estanterìa")

        # Configuración inicial y archivo de configuración
        self.config_file = 'estanteria_config.json'
        self.coordenadas_file = 'coordenadas_estanteria.json'
        self.total_length = 105  # Longitud total de la fila en cm
        self.min_spacing = 5    # Espaciado mínimo entre divisores en cm
        self.rows = 6           # Número de filas

        # Configuración por defecto
        self.configuracion_defecto = {i: [0, 15, 30, 45, 60, 75, 90, 105] for i in range(self.rows)}

        # Cargar configuración previa o usar configuración por defecto
        self.cargar_configuracion()

        # Obtener el tamaño de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        ancho_canvas =screen_width-200
        alto_canvas  =screen_height-700

        ancho_canvas_2 =screen_width - 100
        alto_canvas_2  =screen_height - 200

        #print(f"ancho canvas = {ancho_canvas_2} & alto canvas = {alto_canvas_2}")

        self.canvas_img = tk.Canvas(self.area_central,
                                    width=ancho_canvas_2,
                                    height=alto_canvas_2,
                                    bg="black",bd=5,highlightthickness=5)
        self.canvas_img.place(x=(screen_width/2)-500, y=(screen_height/2)-960)   # Centrar el canvas en la pantalla

        # Cargar la imagen
        imagen_original = Image.open("img/borde.png")  # Cambia esto a la ruta de tu imagen
        imagen_redimensionada = imagen_original.resize((980,1760))  # Opcional: Redimensionar la imagen
        imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)
        
        # Colocar la imagen en el Canvas
        self.canvas_img.create_image(500,850, image=imagen_tk, anchor="center")  # Coordenadas x=200, y=200
        self.canvas_img.imagen_ref = imagen_tk  # Mantener una referencia para que no se elimine la imagen
        
        self.canvas = tk.Canvas(self.area_central, 
                                width=ancho_canvas, 
                                height=alto_canvas, 
                                bg="#d2d2d2", 
                                bd=5,
                                highlightbackground="#000000", 
                                highlightthickness=5)
        
        self.canvas.place(x=(screen_width/2)-450,y=(screen_height/2)-920)  # Coloca el Canvas a 50px del borde izquierdo y 100px del borde superior
        
        # Crear un frame para los botones
        self.boton_frame = tk.Frame(self.area_central, 
                                        bg="#d2d2d2", 
                                        bd=0, 
                                        relief="solid")
        self.boton_frame.place(x=125, y=alto_canvas-20)

        # Botones
        self.boton_agregar = tk.Button(self.boton_frame, 
                                        text="Agregar Divisor", 
                                        font=self.fuente_2,
                                        command=self.agregar_divisor)
        self.boton_eliminar = tk.Button(self.boton_frame, 
                                        text="Eliminar Divisor", 
                                        font=self.fuente_2,
                                        command=self.eliminar_divisor)
        self.boton_modificar = tk.Button(self.boton_frame, 
                                        text="Modificar Divisor", 
                                        font=self.fuente_2,
                                        command=self.modificar_divisor)
        self.boton_restaurar = tk.Button(self.boton_frame, 
                                        text="Restaurar Valores", 
                                        font=self.fuente_2,
                                        command=self.restaurar_valores_defecto)

        # Colocar los botones
        self.boton_agregar.pack(side=tk.RIGHT, padx=5)
        self.boton_eliminar.pack(side=tk.RIGHT, padx=5)
        self.boton_modificar.pack(side=tk.RIGHT, padx=5)
        self.boton_restaurar.pack(side=tk.RIGHT, padx=5)

        try:
            # Open and resize image
            original_image = Image.open("img/LogoPrincipal.png")  # Replace with your image path
            resized_image = original_image.resize((900, 700), Image.LANCZOS)
            self.background_photo = ImageTk.PhotoImage(resized_image)
            
            # Create image on canvas (behind other elements)
            self.canvas.create_image(450, 350, image=self.background_photo)
        except Exception as e:
            print(f"Error loading background image: {e}")

        # Generar coordenadas iniciales
        self.generar_coordenadas()
        self.dibujar_estanteria()

    def cargar_configuracion(self):
        """Carga la configuración desde un archivo JSON o usa valores por defecto."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.divisiones_por_fila = {int(k): v for k, v in config.get('divisiones', {}).items()}
            except (json.JSONDecodeError, IOError):
                self.divisiones_por_fila = self.configuracion_defecto.copy()
        else:
            self.divisiones_por_fila = self.configuracion_defecto.copy()

    def guardar_configuracion(self):
        """Guarda la configuración actual en un archivo JSON."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'divisiones': self.divisiones_por_fila}, f, indent=4)
        except IOError:
            messagebox.showerror("Error", "No se pudo guardar la configuración.")

    def generar_coordenadas(self):
        """Genera coordenadas Z, X para cada ID de espacio."""
        coordenadas = {}
        contador = 1
        for row, divisiones in self.divisiones_por_fila.items():
            for i in range(1, len(divisiones)):
                # Calcular coordenadas X (ancho total 105 cm)
                x = (divisiones[i-1] + divisiones[i]) / 2
                
                # Coordenada Z basada en la fila
                z = row

                # Generar ID con 3 dígitos
                id_espacio = f"ID {contador:03d}"
                
                # Guardar coordenadas
                coordenadas[id_espacio] = {
                    'z': round(z, 2),  # Coordenada Z
                    'x': round(x, 2)   # Coordenada X
                }
                
                contador += 1

        # Guardar en archivo JSON
        try:
            with open(self.coordenadas_file, 'w') as f:
                json.dump(coordenadas, f, indent=4)
        except IOError:
            messagebox.showerror("Error", "No se pudo guardar las coordenadas.")

    def dibujar_estanteria(self):
        """Dibuja la estantería y sus divisores."""
        self.canvas.delete("all")
        espacio_entre_estanterias = 100
        contador = 1
        for row, divisiones in self.divisiones_por_fila.items():
            # Convertir row a entero para evitar problemas de tipo
            row = int(row)
            y_offset = 200 + row * (70 + espacio_entre_estanterias)
            self.canvas.create_rectangle(50, y_offset + 20, 850, y_offset , 
                                                fill="gainsboro")

            for i, divisor in enumerate(divisiones):
                x = 50 + (divisor / self.total_length) * 800
                self.canvas.create_line(x, y_offset - 40, x, y_offset + 20, 
                                                fill="black", 
                                                width=5)

                # Mostrar etiquetas de distancia
                if i > 0:
                    distancia = divisor - divisiones[i - 1]
                    x_text = 50 + ((divisor + divisiones[i - 1]) / 2 / self.total_length) * 800
                    self.canvas.create_text(x_text, y_offset + 10 , 
                                            text=f"{distancia}", 
                                            fill="#CA3519",
                                            font=self.fuente_2)

                # Mostrar etiquetas A1, A2, A3, etc. en los divisores
                letra_fila = chr(65 + row)
                self.canvas.create_text(x, y_offset + 30, 
                                                text=f"{letra_fila}{i + 1}", 
                                                fill="black",
                                                font=self.fuente_2)

                # Mostrar números de espacio
                if i > 0:
                    x_text = 50 + ((divisor + divisiones[i - 1]) / 2 / self.total_length) * 800
                    numero_espacio = f" ID \n{contador:03d}"
                    self.canvas.create_text(x_text, y_offset - 30, 
                                                text=numero_espacio, 
                                                fill="#000000", 
                                                font=(self.fuente),
                                                anchor="center" )
                    contador += 1

    def solicitar_fila(self):
        """Solicita al usuario el número de fila."""
        try:
            fila = int(simpledialog.askstring("Seleccionar Fila", "Introduce el número de fila (1-7):")) - 1
            if fila not in self.divisiones_por_fila:
                raise ValueError("Fila fuera de rango.")
            return fila
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Fila inválida. Inténtalo de nuevo.")
            return None

    def restaurar_valores_defecto(self):
        """Restaura los valores por defecto con confirmación."""
        respuesta = messagebox.askyesno("Restaurar Valores", 
                                        "¿Está seguro de que desea restaurar los valores predeterminados?\n"
                                        "Todos los cambios actuales se perderán.")
        
        if respuesta:
            # Restaurar configuración por defecto
            self.divisiones_por_fila = self.configuracion_defecto.copy()
            
            # Dibujar estantería con nuevos valores
            self.dibujar_estanteria()
            
            # Guardar configuración restaurada
            self.guardar_configuracion()
            
            # Regenerar coordenadas
            self.generar_coordenadas()
            
            # Mensaje de confirmación
            messagebox.showinfo("Restauración Completa", "Se han restaurado los valores predeterminados.")

    def agregar_divisor(self):
        """Agrega un nuevo divisor a la estantería."""
        fila = self.solicitar_fila()
        if fila is None:
            return

        try:
            nuevo = int(simpledialog.askstring("Agregar Divisor", "Introduce la posición del nuevo divisor (en cm):"))
            divisiones = self.divisiones_por_fila[fila]

            if nuevo in divisiones:
                messagebox.showerror("Error", "El divisor ya existe en esa posición.")
                return
            if nuevo <= 0 or nuevo >= self.total_length:
                messagebox.showerror("Error", "No puedes agregar divisores en los extremos.")
                return

            # Verificar espaciado mínimo
            for divisor in divisiones:
                if abs(divisor - nuevo) < self.min_spacing:
                    messagebox.showerror("Error", f"El divisor debe estar al menos a {self.min_spacing} cm de otro.")
                    return

            divisiones.append(nuevo)
            divisiones.sort()
            self.dibujar_estanteria()
            self.guardar_configuracion()
            self.generar_coordenadas()
        except ValueError:
            messagebox.showerror("Error", "Valor inválido. Inténtalo de nuevo.")

    def eliminar_divisor(self):
        """Elimina un divisor de la estantería por índice."""
        fila = self.solicitar_fila()
        if fila is None:
            return

        divisor_indice = simpledialog.askstring("Eliminar Divisor", "Introduce el índice del divisor:")
        if divisor_indice is None:
            return

        try:
            letra_fila = divisor_indice[0].upper()
            num_divisor = int(divisor_indice[1:]) - 1

            if letra_fila < 'A' or letra_fila > chr(ord('A') + self.rows - 1):
                messagebox.showerror("Error", "Fila inválida.")
                return

            if num_divisor < 0 or num_divisor >= len(self.divisiones_por_fila[fila]):
                messagebox.showerror("Error", "Índice de divisor fuera de rango.")
                return

            divisor = self.divisiones_por_fila[fila][num_divisor]

            if divisor in [0, self.total_length]:
                messagebox.showerror("Error", "No puedes eliminar los divisores de los extremos.")
                return

            self.divisiones_por_fila[fila].remove(divisor)
            self.dibujar_estanteria()
            self.guardar_configuracion()
            self.generar_coordenadas()
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Índice inválido. Inténtalo de nuevo.")

    def modificar_divisor(self):
        """Modifica un divisor de la estantería por índice."""
        fila = self.solicitar_fila()
        if fila is None:
            return

        divisor_indice = simpledialog.askstring("Modificar Divisor", "Introduce el índice del divisor:")
        if divisor_indice is None:
            return

        try:
            letra_fila = divisor_indice[0].upper()
            num_divisor = int(divisor_indice[1:]) - 1

            if letra_fila < 'A' or letra_fila > chr(ord('A') + self.rows - 1):
                messagebox.showerror("Error", "Fila inválida.")
                return

            if num_divisor < 0 or num_divisor >= len(self.divisiones_por_fila[fila]):
                messagebox.showerror("Error", "Índice de divisor fuera de rango.")
                return

            divisor = self.divisiones_por_fila[fila][num_divisor]

            if divisor in [0, self.total_length]:
                messagebox.showerror("Error", "No puedes modificar los divisores de los extremos.")
                return

            nuevo = int(simpledialog.askstring("Nueva Posición", "Introduce la nueva posición del divisor (en cm):"))
            if nuevo <= 0 or nuevo >= self.total_length:
                messagebox.showerror("Error", "No puedes mover divisores a los extremos.")
                return
            if any(abs(nuevo - d) < self.min_spacing for d in self.divisiones_por_fila[fila] if d != divisor):
                messagebox.showerror("Error", f"El divisor debe estar al menos a {self.min_spacing} cm de otro.")
                return

            self.divisiones_por_fila[fila][self.divisiones_por_fila[fila].index(divisor)] = nuevo
            self.divisiones_por_fila[fila].sort()
            self.dibujar_estanteria()
            self.guardar_configuracion()
            self.generar_coordenadas()

        except (ValueError, IndexError):
            messagebox.showerror("Error", "Índice inválido. Inténtalo de nuevo.")

    #Funciones de la opcion inventario 

    def accion_inventario(self):

        print("Accion inventario")

        self.detener_hilo_limpiar()

        self.ARCHIVO_COORDENADAS = "coordenadas_estanteria.json"
        self.ARCHIVO_INVENTARIO = "inventario_productos.json"
        self.RUTA_IMAGEN_DEFECTO = "img/easyPickR.jpg"
        self.entradas = {}
        self.ventana_imagen_grande = None
        

        self.guardar_datos

        self.coordenadas_inventario = self.cargar_coordenadas()
        self.inventario = self.cargar_inventario()

        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()

        #print (f"ancho={ancho_pantalla} alto={alto_pantalla}")

        ancho_canvas = ancho_pantalla-50 #ancho_pantalla-450
        alto_canvas = alto_pantalla-400 #alto_pantalla-550

        x_pos = ((ancho_pantalla - ancho_canvas) // 2)-12
        y_pos = 10


        frame_central = tk.Frame(self.area_central, width=ancho_canvas, height=alto_canvas,
                                bg="black",bd=2,highlightthickness=5)
                                
        frame_central.place(x=x_pos, y=y_pos)

        canvas = tk.Canvas(frame_central, width=ancho_canvas, height=alto_canvas)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_central, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        frame_contenido = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame_contenido, anchor="nw")

        encabezado = ["ID", "Imagen", "Proveedor", "Cantidad", "Precio", "Unidad"]
        for col, texto in enumerate(encabezado):
            tk.Label(frame_contenido, text=texto, font=self.fuente_2, 
                    borderwidth=1, relief="solid").grid(row=0, column=col, padx=5, 
                    pady=5, sticky="nsew")

        for idx, (id_producto, coord) in enumerate(self.coordenadas_inventario.items(), start=1):
            tk.Label(frame_contenido, text=id_producto, font=self.fuente_2, borderwidth=1, 
                    relief="solid").grid(row=idx, column=0, padx=5, pady=5, sticky="nsew")

            etiqueta_imagen = tk.Label(frame_contenido, width=30, height=10, relief="solid")
            etiqueta_imagen.grid(row=idx, column=1, padx=5, pady=5, sticky="nsew")
            
            self.mostrar_imagen_defecto(etiqueta_imagen)
            imagen_path = self.inventario.get(id_producto, {}).get("imagen", "")
            
            if imagen_path:
                self.mostrar_imagen(etiqueta_imagen, imagen_path)

            etiqueta_imagen.bind("<Button-1>", 
                            lambda event, imagen_path=imagen_path: 
                            self.mostrar_imagen_grande(imagen_path))

            proveedor_entry = tk.Entry(frame_contenido, width=20, font=self.fuente)
            proveedor_entry.grid(row=idx, column=2, padx=5, pady=5, sticky="nsew")
            proveedor_entry.insert(0, self.inventario.get(id_producto, {}).get("proveedor", ""))

            cantidad_entry = tk.Entry(frame_contenido, width=15, font=self.fuente)
            cantidad_entry.grid(row=idx, column=3, padx=5, pady=5, sticky="nsew")
            cantidad_entry.insert(0, self.inventario.get(id_producto, {}).get("cantidad", ""))

            precio_entry = tk.Entry(frame_contenido, width=20, font=self.fuente)
            precio_entry.grid(row=idx, column=4, padx=5, pady=5, sticky="nsew")
            precio_entry.insert(0, self.inventario.get(id_producto, {}).get("precio", ""))

            unidad_combo = ttk.Combobox(frame_contenido, 
                                    values=["UND", "Metro", "Bolsa"], 
                                    state="readonly", width=10, font=self.fuente)
            unidad_combo.grid(row=idx, column=5, padx=5, pady=5, sticky="nsew")
            unidad_combo.set(self.inventario.get(id_producto, {}).get("unidad", "UND"))

            self.entradas[id_producto] = {
                "imagen": etiqueta_imagen,
                "proveedor": proveedor_entry,
                "cantidad": cantidad_entry,
                "precio": precio_entry,
                "unidad": unidad_combo,
            }

        frame_bajos = tk.Frame(self.area_central, width=ancho_canvas+5, height=50,
                                bg="black",bd=5,highlightthickness=5)
        frame_bajos.place(x=x_pos, y=alto_pantalla - 350)

        canvas_bajos = tk.Canvas(frame_bajos, width=ancho_canvas, height=50)
        canvas_bajos.pack(side="left", fill="both", expand=True)

        btn_guardar = tk.Button(canvas_bajos, text="Guardar Inventario", font=self.fuente_2, 
                            command=self.guardar_datos)
        btn_guardar.place(relx=0.15, rely=0.5, anchor="center")

        btn_cargar_imagen = tk.Button(canvas_bajos, text="Cargar Imagen", font=self.fuente_2, 
                            command=self.cargar_imagen_id)
        btn_cargar_imagen.place(relx=0.5, rely=0.5, anchor="center")
        
        btn_mover_id = tk.Button(canvas_bajos, text="Mover ID", font=self.fuente_2, command=self.mover_id)
        btn_mover_id.place(relx=0.9, rely=0.5, anchor="center")

        # btn_mover_grupo = tk.Button(canvas_bajos, text="Mover Grupo", command=self.abrir_mover_grupo)
        # btn_mover_grupo.place(relx=0.75, rely=0.5, anchor="center")


        frame_contenido.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def cargar_coordenadas(self):
        if os.path.exists(self.ARCHIVO_COORDENADAS):
            with open(self.ARCHIVO_COORDENADAS, "r") as archivo:
                return json.load(archivo)
        return {}

    def guardar_inventario(self, datos):
        with open(self.ARCHIVO_INVENTARIO, "w") as archivo:
            json.dump(datos, archivo, indent=4)

    def cargar_inventario(self):
        if os.path.exists(self.ARCHIVO_INVENTARIO):
            with open(self.ARCHIVO_INVENTARIO, "r") as archivo:
                return json.load(archivo)
        return {}

    def cargar_imagen(self, id_producto, etiqueta_imagen):
        ruta_completa = filedialog.askopenfilename(
            filetypes=[("Todos los archivos", "*.*"), 
                        ("Imágenes JPG y PNG", "*.jpg;*.jpeg;*.png"), 
                        ("Imágenes GIF", "*.gif")]
        )
        
        if ruta_completa:
            ruta_relativa = os.path.relpath(ruta_completa, "img")
            
            imagen = Image.open(ruta_completa)
            imagen = imagen.resize((20, 20), Image.Resampling.LANCZOS)
            imagen_tk = ImageTk.PhotoImage(imagen)

            etiqueta_imagen.config(image=imagen_tk)
            etiqueta_imagen.image = imagen_tk

            inventario = self.cargar_inventario()
            if id_producto not in inventario:
                inventario[id_producto] = {}
            
            inventario[id_producto]["imagen"] = "img/" + ruta_relativa
            self.guardar_inventario(inventario)
            messagebox.showinfo("Imagen Cargada", "Imagen cargada y guardada exitosamente")

    def mostrar_imagen_defecto(self, etiqueta_imagen):
        imagen = Image.open(self.RUTA_IMAGEN_DEFECTO)
        imagen = imagen.resize((20, 20), Image.Resampling.LANCZOS)
        imagen_tk = ImageTk.PhotoImage(imagen)
        
        etiqueta_imagen.config(image=imagen_tk)
        etiqueta_imagen.image = imagen_tk

    def guardar_datos(self):
        inventario = self.cargar_inventario()
        datos = {}
        
        for id_producto, widgets in self.entradas.items():
            imagen_path = inventario.get(id_producto, {}).get("imagen", "")
            
            datos[id_producto] = {
                "imagen": imagen_path,
                "proveedor": widgets["proveedor"].get(),
                "cantidad": widgets["cantidad"].get(),
                "precio": widgets["precio"].get(),
                "unidad": widgets["unidad"].get(),
            }
        
        self.guardar_inventario(datos)
        self.coordenadas = self.cargar_coordenadas()
        self.inventario = self.cargar_inventario()
        messagebox.showinfo("Guardado", "Inventario guardado exitosamente")
        self.accion_inventario()

    def cargar_imagen_id(self):
        id_producto = simpledialog.askstring("ID Producto", 
                                            "Ingrese el ID del producto para cargar la imagen:")
        if id_producto and id_producto in self.entradas:
            self.cargar_imagen(id_producto, self.entradas[id_producto]["imagen"])

    def mostrar_imagen(self, etiqueta_imagen, imagen_path):
        imagen = Image.open(imagen_path)
        imagen = imagen.resize((20, 20), Image.Resampling.LANCZOS)
        imagen_tk = ImageTk.PhotoImage(imagen)
        
        etiqueta_imagen.config(image=imagen_tk)
        etiqueta_imagen.image = imagen_tk

    def mostrar_imagen_grande(self, imagen_path):
        # Si existe una ventana abierta, la cerramos
        if self.ventana_imagen_grande is not None:
            self.ventana_imagen_grande.destroy()

        # Creamos la nueva ventana
        self.ventana_imagen_grande = tk.Toplevel(self.root)
        self.ventana_imagen_grande.title("Imagen Grande")
        
        # Centrar la ventana en la pantalla
        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()
        x = (ancho_pantalla - 400) // 2  # 400 es el ancho de la imagen
        y = (alto_pantalla - 400) // 2   # 400 es el alto de la imagen
        self.ventana_imagen_grande.geometry(f"400x400+{x}+{y}")

        try:
            imagen = Image.open(imagen_path)
            imagen = imagen.resize((400, 400), Image.Resampling.LANCZOS)
            imagen_tk = ImageTk.PhotoImage(imagen)

            etiqueta_imagen_grande = tk.Label(self.ventana_imagen_grande, image=imagen_tk)
            etiqueta_imagen_grande.image = imagen_tk  # Mantener referencia
            etiqueta_imagen_grande.pack(expand=True, fill="both")
            
            # Agregar botón de cerrar
            btn_cerrar = tk.Button(self.ventana_imagen_grande, text="Cerrar", 
                                    command=self.ventana_imagen_grande.destroy)
            btn_cerrar.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen: {str(e)}")
            self.ventana_imagen_grande.destroy()

    def mover_id(self):
        # Pedimos el ID del producto que se quiere mover
        id_origen = simpledialog.askstring("Mover ID", "Ingrese el ID del producto que desea mover:")
        if not id_origen or id_origen not in self.entradas:
            messagebox.showerror("Error", "ID no encontrado.")
            return

        # Pedimos el ID de destino, debajo del cual se moverá el ID
        id_destino = simpledialog.askstring("Mover ID", "Ingrese el ID debajo del cual desea colocar el producto:")
        if not id_destino or id_destino not in self.entradas:
            messagebox.showerror("Error", "ID de destino no encontrado.")
            return
        
        # Obtener las coordenadas actuales de los productos
        coordenadas = self.cargar_coordenadas()

        # Obtenemos el índice del ID origen y el ID destino
        idx_origen = list(coordenadas.keys()).index(id_origen)
        idx_destino = list(coordenadas.keys()).index(id_destino)

        # Reordenamos los IDs
        ids = list(coordenadas.keys())
        ids.remove(id_origen)  # Elimina el ID origen
        ids.insert(idx_destino + 1, id_origen)  # Inserta el ID origen debajo del destino

        # Ahora actualizamos los IDs en las coordenadas
        nuevas_coordenadas = {id_: coordenadas[id_] for id_ in ids}
        self.guardar_coordenadas(nuevas_coordenadas)

        # Reordenamos también el inventario
        inventario = self.cargar_inventario()
        nuevo_inventario = {id_: inventario[id_] for id_ in ids}
        self.guardar_inventario(nuevo_inventario)

        # Actualizamos la interfaz
        self.accion_inventario()
        messagebox.showinfo("Éxito", f"El ID {id_origen} se movió debajo de {id_destino}.")

    def guardar_coordenadas(self, coordenadas):
        with open(self.ARCHIVO_COORDENADAS, "w") as archivo:
            json.dump(coordenadas, archivo, indent=4)

    # def abrir_mover_grupo(self):
    #     # Ventana emergente para mover grupo
    #     ventana_mover = tk.Toplevel(self.root)
    #     ventana_mover.title("Mover Grupo de Productos")
    #     ventana_mover.geometry("400x300")
        
    #     # Entrada para ID inicial
    #     tk.Label(ventana_mover, text="ID Inicio:").pack(pady=5)
    #     id_inicio_entry = tk.Entry(ventana_mover)
    #     id_inicio_entry.pack(pady=5)
        
    #     # Entrada para ID final
    #     tk.Label(ventana_mover, text="ID Fin:").pack(pady=5)
    #     id_fin_entry = tk.Entry(ventana_mover)
    #     id_fin_entry.pack(pady=5)
        
    #     # Entrada para ID de referencia
    #     tk.Label(ventana_mover, text="Mover debajo de ID:").pack(pady=5)
    #     id_referencia_entry = tk.Entry(ventana_mover)
    #     id_referencia_entry.pack(pady=5)
        
    #     def mover_grupo():
    #         # Obtener valores ingresados
    #         id_inicio = id_inicio_entry.get().strip()
    #         id_fin = id_fin_entry.get().strip()
    #         id_referencia = id_referencia_entry.get().strip()
            
    #         # Validaciones
    #         if id_inicio not in self.entradas or id_fin not in self.entradas:
    #             messagebox.showerror("Error", "ID de inicio o fin no válido.")
    #             return
            
    #         if id_referencia and id_referencia not in self.entradas:
    #             messagebox.showerror("Error", "ID de referencia no válido.")
    #             return
            
    #         coordenadas = self.cargar_coordenadas()
    #         ids = list(coordenadas.keys())
            
    #         idx_inicio = ids.index(id_inicio)
    #         idx_fin = ids.index(id_fin)
            
    #         if idx_inicio > idx_fin:
    #             messagebox.showerror("Error", "El ID de inicio debe ser anterior al ID de fin.")
    #             return
            
    #         grupo_ids = ids[idx_inicio:idx_fin + 1]
    #         ids_sin_grupo = [id_actual for id_actual in ids if id_actual not in grupo_ids]
            
    #         if id_referencia == "ID 000":  # Caso especial: mover al principio
    #             ids = grupo_ids + ids_sin_grupo
    #         else:
    #             idx_referencia = ids_sin_grupo.index(id_referencia)
    #             ids = ids_sin_grupo[:idx_referencia + 1] + grupo_ids + ids_sin_grupo[idx_referencia + 1:]
            
    #         # Reasignar IDs con formato
    #         nuevas_coordenadas = {}
    #         inventario = self.cargar_inventario()
    #         nuevo_inventario = {}
            
    #         for nuevo_idx, viejo_id in enumerate(ids, start=1):
    #             nuevo_id_str = f"ID {nuevo_idx:03d}"  # Formato "ID 001"
    #             nuevas_coordenadas[nuevo_id_str] = coordenadas[viejo_id]
    #             nuevo_inventario[nuevo_id_str] = inventario[viejo_id]
            
    #         # Guardar los nuevos datos
    #         self.guardar_coordenadas(nuevas_coordenadas)
    #         self.guardar_inventario(nuevo_inventario)
            
    #         # Actualizar la interfaz
    #         self.crear_interfaz()
    #         ventana_mover.destroy()
    #         messagebox.showinfo("Éxito", f"El grupo de productos se movió debajo de {id_referencia} y los IDs se actualizaron.")

    #     # Botón para confirmar movimiento
    #     btn_confirmar = tk.Button(ventana_mover, text="Mover", command=mover_grupo)
    #     btn_confirmar.pack(pady=10)

    #     # Botón para cancelar
    #     btn_cancelar = tk.Button(ventana_mover, text="Cancelar", command=ventana_mover.destroy)
    #     btn_cancelar.pack(pady=10)
if __name__ == "__main__":
    root = tk.Tk()

    # Configuración de pantalla completa
    root.attributes("-fullscreen", True)  # Inicia en pantalla completa
    root.bind("<F11>", lambda event: root.attributes("-fullscreen",not root.attributes("-fullscreen")))  # Alterna con F11
    root.bind("<Escape>", lambda event: root.attributes("-fullscreen", False))  # Sale con Escape

    app = EasyPickApp(root)
    root.mainloop()
