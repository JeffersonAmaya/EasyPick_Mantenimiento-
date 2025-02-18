import threading
import tkinter as tk
import tkinter.ttk as ttk
import time
import json
import os
import string
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
        self.root.configure(bg="white")  # Cambiar el fondo de la ventana principal a blanco

        
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
        print(f"Motor lineal alcanzó el final de carrera.")
        time.sleep(1)
        return
    
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
                if not self.fc1_monitoreo.esta_activado():  # Usar esta_activado() en lugar de is_pressed
                    #print("FC1 activado")
                    imagen_original = Image.open("img/fc2.PNG")
                elif not self.fc2_monitoreo.esta_activado():
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

        # Limpiar toda la información de la pantalla
        self.detener_hilo_limpiar()

        self.shelves = []  # Lista de estanterías añadidas
        self.buttons = {}  # Diccionario de botones (óvalos)
        self.move_x = 30

        # Crear el lienzo de guías
        self.guides_canvas = tk.Canvas(self.area_central, width=80, height=600, bg="white",highlightthickness=0)
        self.guides_canvas.pack(side=tk.LEFT, fill=tk.Y)

        self.image_mas = tk.PhotoImage(file="img/mas.png")
        self.image_menos = tk.PhotoImage(file="img/menos.png")

        # Ajustar el tamaño de la imagen
        self.image_mas = self.image_mas.subsample(10, 10)  # Reduce el tamaño de la imagen (por ejemplo, 3x más pequeña)
        self.image_menos = self.image_menos.subsample(10, 10)  # Reduce el tamaño de la imagen (por ejemplo, 3x más pequeña)
        
        self.create_vertical_guides() 
        self.load_config()
        self.vertical_profile()

    def create_vertical_guides(self):
        step = 5  # Espaciado cada 5 cm
        min_spacing = 15+5  # Mínimo de 15 cm entre estanterías

        for y in range(0, 105 + 1, step):  # Ahora iteramos cada 5 cm
            y_pos = 50 + (y * 15)  # Calcular la posición en píxeles
            
            button = tk.Button(self.guides_canvas, 
                            image=self.image_mas, 
                            width=50, 
                            height=50, 
                            bg="white",
                            relief="flat", 
                            borderwidth=0)
            button.place(x=20, y=y_pos)
            
            # Configurar comando para verificar la distancia antes de agregar estantería
            button.config(command=lambda y_pos=y_pos: self.check_and_toggle_shelf(y_pos, min_spacing))
            
            self.buttons[y_pos] = button  # Guardar el botón en el diccionario
    
    def check_and_toggle_shelf(self, y_pos, min_spacing):
        existing_shelf = None
        
        for shelf in self.shelves:
            if abs(shelf["y_pos"] - y_pos) < 10:  # Si ya existe en la posición
                existing_shelf = shelf
                break

        if existing_shelf:
            self.confirm_delete_shelf(y_pos)  # Si la estantería ya existe, permitir eliminarla
        else:
            # Verificar distancia mínima solo al agregar
            for shelf in self.shelves:
                if abs(shelf["y_pos"] - y_pos) < min_spacing * 10:  # Convertir 15 cm a píxeles
                    messagebox.showwarning("Advertencia", "Debe haber al menos 15 cm entre estanterías.")
                    return
            
            self.add_shelf(y_pos)  # Si pasa la validación, agregar la estantería

    def toggle_shelf(self, y_pos):
        # Buscar una estantería con margen de tolerancia debido al espaciado extra
        for shelf in self.shelves:
            if abs(shelf["y_pos"] - y_pos) < 10:  # Permite pequeña diferencia en píxeles
                self.confirm_delete_shelf(shelf["y_pos"])
                return
        
        self.add_shelf(y_pos)

    def delete_shelf(self, y_pos):
        for shelf in self.shelves:
            if abs(shelf["y_pos"] - y_pos) < 10:  # Permite margen de error
                shelf["canvas"].destroy()
                self.shelves.remove(shelf)
                self.buttons[y_pos].config(image=self.image_mas)
                self.save_config()
                self.save_coordinates()
                return


    def add_shelf(self, y_pos):
        # Verifica si ya existe una estantería en esa posición
        for shelf in self.shelves:
            if shelf["y_pos"] == y_pos:
                #messagebox.showwarning("Advertencia", "Ya existe una estantería en esta posición.")
                return  # No agrega una estantería si ya hay una en esa posición

        # Crear una nueva estantería
        shelf_canvas = tk.Canvas(self.area_central, width=900, height=150, bg="white",highlightthickness=0)
        shelf_canvas.place(x=+80+self.move_x, y=y_pos )

        # Configurar la estantería
        shelf_data = {
            "canvas": shelf_canvas,
            "y_pos": y_pos,
            "dividers": [],
            "values": [0, 105],
            "labels": [],
            "space_labels": {},
            "space_ids": {},
            "next_id": 1,
        }
        self.shelves.append(shelf_data)

        # Dibujar la base de la estantería
        shelf_canvas.create_rectangle(20, 65, 880, 85, fill="gray", outline="black")
        

        # Dibujar los divisores iniciales
        for val in shelf_data["values"]:
            x = self.value_to_x(val, shelf_data)
            divider = shelf_canvas.create_rectangle(x - 5, 10, x + 5, 80, fill="gray", outline="gray")
            shelf_data["dividers"].append(divider)

        # Crear guías y etiquetas
        self.create_guides(shelf_data)
        self.update_positions(shelf_data)
        self.create_labels(shelf_data)
        self.vertical_profile()
        
        # Asignar eventos
        shelf_canvas.bind("<Double-Button-1>", lambda event, data=shelf_data: self.add_divider(event, data))
        shelf_canvas.bind("<Button-3>", lambda event, data=shelf_data: self.remove_divider(event, data))

        # Cambiar el color del botón a verde cuando haya una estantería
        self.buttons[y_pos].config(image=self.image_menos)
        self.save_coordinates()

    def vertical_profile(self):

        # Crear el lienzo principal para los soportes
        self.main_canvas_1 = tk.Canvas(self.area_central, width=11, height=1800, bg="gray", highlightthickness=0)
        self.main_canvas_1.place(x=95+self.move_x, y=50)
        self.main_canvas_2 = tk.Canvas(self.area_central, width=11, height=1800, bg="gray", highlightthickness=0)
        self.main_canvas_2.place(x=955+self.move_x, y=50)

        self.save_config()

    def confirm_delete_shelf(self, y_pos):
        # Mostrar un cuadro de diálogo de confirmación antes de eliminar la estantería
        response = messagebox.askyesno(
            "Confirmación", 
            "¿Está seguro de que desea eliminar esta estantería? Se perderán todos los cambios realizados en esta estantería."
        )
        if response:
            self.delete_shelf(y_pos)

    def value_to_x(self, val, shelf_data):
        # Convertir valor a posición x en la interfaz
        return 20 + (val - 0) / (105 - 0) * (900 - 40)

    def x_to_value(self, x):
        # Convertir posición x a valor correspondiente
        raw_value = 0 + ((x - 20) / (900 - 40)) * (105 - 0)
        return round(raw_value / 5) * 5  

    def update_positions(self, shelf_data):
        # Actualizar las posiciones de los divisores
        for i, val in enumerate(shelf_data["values"]):
            x = self.value_to_x(val, shelf_data)
            if i < len(shelf_data["dividers"]):
                shelf_data["canvas"].coords(shelf_data["dividers"][i], x - 5, 10, x + 5, 90)
                self.update_labels(shelf_data)
                self.update_space_ids(shelf_data)

    def add_divider(self, event, shelf_data):
        # Agregar un divisor en la posición del clic
        x = event.x
        value = self.x_to_value(x)
        if value in shelf_data["values"]:
            #messagebox.showwarning("Advertencia", f"Ya existe un divisor en {value} cm")
            return  
        shelf_data["values"].append(value)
        shelf_data["values"].sort()
        index = shelf_data["values"].index(value)
        divider = shelf_data["canvas"].create_rectangle(0, 0, 10, 80, fill="brown", outline="black")
        shelf_data["dividers"].insert(index, divider)
        self.update_positions(shelf_data)
        self.create_labels(shelf_data)
        self.save_config()
        self.save_coordinates()
        self.vertical_profile()

    def remove_divider(self, event, shelf_data):
        # Eliminar un divisor al hacer clic derecho
        if len(shelf_data["values"]) <= 2:
            return
        x_clicked = event.x
        for i in range(1, len(shelf_data["values"]) - 1):
            if abs(self.value_to_x(shelf_data["values"][i], shelf_data) - x_clicked) < 10:
                del shelf_data["values"][i]
                shelf_data["canvas"].delete(shelf_data["dividers"][i])  
                del shelf_data["dividers"][i]
                self.update_space_ids(shelf_data)
                self.save_config()
                self.save_coordinates()
                return
        #messagebox.showwarning("Advertencia", "No se encontró un divisor en esta posición para eliminar")

    def create_labels(self, shelf_data):
        # Crear las etiquetas de los valores de los divisores
        for label in shelf_data["labels"]:
            label.destroy()
        shelf_data["labels"].clear()

    def update_labels(self, shelf_data):
        # Actualizar las etiquetas de los valores de los divisores
        for i, val in enumerate(shelf_data["values"]):
            y_pos = 130 if val not in [0, 105] else 150
            label = tk.Label(shelf_data["canvas"], text=f"{val} cm", bg="black")
            label.place(x=self.value_to_x(val, shelf_data) - 15, y=y_pos)
            shelf_data["labels"].append(label)

    def create_guides(self, shelf_data):
        # Crear guías de 1 cm en 1 cm
        for i in range(5, 100 + 1, 5):
            x = self.value_to_x(i, shelf_data)
            shelf_data["canvas"].create_oval(x - 2, 72, x + 2, 75, fill="black")
            
            # Formatear el número para que siempre tenga dos dígitos
            guide_label = tk.Label(shelf_data["canvas"], text=f"{i:03d}", font=("Arial", 8))
            guide_label.place(x=x-10, y=72+20)

    def update_space_ids(self, shelf_data):
        # Actualizar los identificadores de los espacios entre divisores
        for label in shelf_data["space_labels"].values():
            label.destroy()
        shelf_data["space_labels"].clear()
        shelf_data["space_ids"].clear()
        shelf_data["next_id"] = 1

        for i in range(len(shelf_data["values"]) - 1):
            start = shelf_data["values"][i]
            end = shelf_data["values"][i + 1]
            space_id = f"{shelf_data['next_id']}"
            shelf_data["space_ids"][(start, end)] = space_id

            x_start = self.value_to_x(start, shelf_data)
            x_end = self.value_to_x(end, shelf_data)
            x_center = (x_start + x_end) / 2

            label = tk.Label(shelf_data["canvas"], text=space_id, font=("Arial", 10, "bold"), bg="white")
            label.place(x=x_center - 5, y=30)  
            shelf_data["space_labels"][(start, end)] = label

            shelf_data["next_id"] += 1

    def save_config(self):
        config = {"shelves": []}

        for shelf in self.shelves:
            
            shelf_data = {
                "y_pos": shelf["y_pos"],  # Guardar el valor modificado
                "values": shelf["values"]
            }

            config["shelves"].append(shelf_data)

        # Ordenar las estanterías por y_pos antes de guardar
        config["shelves"].sort(key=lambda shelf: shelf["y_pos"])

        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)

        print("Configuración guardada en 'config.json'")


    def load_config(self):
        if not os.path.exists("config.json"):
            return

        with open("config.json", "r") as f:
            config = json.load(f)

        # Limpiar estanterías actuales
        for shelf in self.shelves:
            shelf["canvas"].destroy()
        self.shelves.clear()

        # Restaurar estanterías desde la configuración guardada
        for shelf_data in config["shelves"]:
            self.add_shelf(shelf_data["y_pos"])
            shelf = self.shelves[-1]  # Última estantería agregada
            shelf["values"] = shelf_data["values"]

            # Eliminar cualquier divisor que pueda haberse creado antes
            for divider in shelf["dividers"]:
                shelf["canvas"].delete(divider)
            shelf["dividers"].clear()

            # Dibujar de nuevo los divisores en marrón excepto los extremos
            for val in shelf["values"]:
                x = self.value_to_x(val, shelf)
                color = "gray" if val in [0, 105] else "brown"  # Extremos en gris, internos en marrón
                divider = shelf["canvas"].create_rectangle(x - 5, 10, x + 5, 80, fill=color, outline="black")
                shelf["dividers"].append(divider)

            self.update_positions(shelf)
            self.create_labels(shelf)
            self.update_space_ids(shelf)

    def save_coordinates(self):
        coordinates = {"shelves": {}}

        # Ordenar estanterías de arriba hacia abajo según la coordenada Z (y_pos)
        sorted_shelves = sorted(self.shelves, key=lambda s: s["y_pos"])

        # Generar letras A, B, C... para cada fila de estantería
        row_labels = string.ascii_uppercase  # "A", "B", "C", ..., "Z"

        for index, shelf in enumerate(sorted_shelves):  # Ahora está ordenado correctamente
            row_letter = row_labels[index]  # Asigna A, B, C... en orden de arriba hacia abajo

            #print(f"Imprimo y_pos {shelf['y_pos']}")


            # Recalcular la posición Z correctamente para cada estantería
            z_position = (15 + ((shelf["y_pos"] - 50) / (1625 - 50)) * (120 - 15))-7.5

            coordinates["shelves"][row_letter] = {}

            for i in range(len(shelf["values"]) - 1):
                start = shelf["values"][i]
                end = shelf["values"][i + 1]

                # Calcular la coordenada X como la mitad entre dos separadores
                x_center = (start + end) / 2

                # Nombre del espacio: "A1", "A2", ..., "B1", "B2"...
                space_name = f"{row_letter}{i + 1}"
                coordinates["shelves"][row_letter][space_name] = {
                    "x": x_center,
                    "z": z_position
                }

        # Guardar en "coordinates.json"
        with open("coordinates.json", "w") as f:
            json.dump(coordinates, f, indent=4)

        print("Coordenadas guardadas en 'coordinates.json'")
        self.vertical_profile()

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


if __name__ == "__main__":
    root = tk.Tk()

    # Configuración de pantalla completa
    root.attributes("-fullscreen", True)  # Inicia en pantalla completa
    root.bind("<F11>", lambda event: root.attributes("-fullscreen",not root.attributes("-fullscreen")))  # Alterna con F11
    root.bind("<Escape>", lambda event: root.attributes("-fullscreen", False))  # Sale con Escape

    app = EasyPickApp(root)
    root.mainloop()
