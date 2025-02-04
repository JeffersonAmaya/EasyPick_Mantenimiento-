import tkinter as tk
from tkinter import PhotoImage
from PIL import Image, ImageTk


class EasyPickApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EasyPick - Mantenimiento")
        self.root.geometry("1200x700")  # Tamaño de la ventana

        # Variable para almacenar la referencia de la imagen central
        self.imagen_label = None

        # Barra superior
        self.crear_barra_superior()

        # Menú de botones
        self.crear_menu_botones()

        # Área central
        self.crear_area_central()
        

    def crear_barra_superior(self):
        # Crear la barra superior
        barra_superior = tk.Frame(self.root, bg="white", height=50)
        barra_superior.pack(fill="x", side="top")

        # Ruta de las imágenes
        ruta_imagen_1 = "C:/Users/ingeniero.id01/EnterDrive/Desktop/Interfaz_manipulador/img/titulo.png"
        ruta_imagen_2 = "C:/Users/ingeniero.id01/EnterDrive/Desktop/Interfaz_manipulador/img/LogoColsein.png"

        # Cargar y redimensionar la primera imagen
        imagen_original_1 = Image.open(ruta_imagen_1)
        imagen_redimensionada_1 = imagen_original_1.resize((180, 50))  # Ajusta el tamaño (ancho, alto)
        logo_1 = ImageTk.PhotoImage(imagen_redimensionada_1)

        # Cargar y redimensionar la segunda imagen
        imagen_original_2 = Image.open(ruta_imagen_2)
        imagen_redimensionada_2 = imagen_original_2.resize((140, 50))  # Ajusta el tamaño (ancho, alto)
        logo_2 = ImageTk.PhotoImage(imagen_redimensionada_2)

        # Crear el Label para la primera imagen
        logo_label_1 = tk.Label(barra_superior, image=logo_1, bg="white")
        logo_label_1.image = logo_1  # Prevenir que el recolector de basura elimine la imagen
        logo_label_1.pack(side="left")  # Posicionar la primera imagen a la izquierda

        # Crear el Label para la segunda imagen
        logo_label_2 = tk.Label(barra_superior, image=logo_2, bg="white")
        logo_label_2.image = logo_2  # Prevenir que el recolector de basura elimine la imagen
        logo_label_2.pack(side="right")  # Posicionar la segunda imagen a la derecha

    def crear_menu_botones(self):
        menu_botones = tk.Frame(self.root, bg="#00AADA", height=50)
        menu_botones.pack(fill="x", side="top")

        # Botones
        botones = [
            ("Posicionador", self.accion_posicionador),
            ("Eyector", self.accion_eyector),
            ("Cámara", self.accion_camara),
            ("Salir", self.salir_app),
        ]

        for texto, comando in botones:
            boton = tk.Button(
                menu_botones,
                text=texto,
                font=("Times New Roman", 12, "bold"),  # Cambia la fuente y tamaño
                fg="white",                # Color del texto
                bg="#00AADA",              # Color de fondo
                activebackground="#031C3A",  # Color de fondo al hacer clic
                activeforeground="white",    # Color del texto al hacer clic
                borderwidth=2,             # Ancho del borde
                relief="flat",           # Estilo del borde (opciones: "flat", "raised", "sunken", "groove", "ridge")
                command=comando
            )
            boton.pack(side="left", padx=10, pady=5)

    def crear_area_central(self):
        self.area_central = tk.Frame(self.root, bg="white")
        self.area_central.pack(fill="both", expand=True)

        # Imagen de muestra
        ruta_imagen = "C:/Users/ingeniero.id01/EnterDrive/Desktop/Interfaz_manipulador/img/LogoColsein.png"
        imagen = PhotoImage(file=ruta_imagen)  # Cambia "maquina.png" por tu imagen
        self.imagen_label = tk.Label(self.area_central, image=imagen, bg="white")
        self.imagen_label.image = imagen
        self.imagen_label.pack(expand=True)

    # Funciones para los botones
    def accion_posicionador(self):
        # Ocultar la imagen central
        if self.imagen_label:
            self.imagen_label.destroy()
            self.imagen_label = None

        # Crear una interfaz para ingresar valores
        self.mostrar_formulario_posicionador()

    def mostrar_formulario_posicionador(self):
        # Crear un nuevo formulario
        self.formulario = tk.Frame(self.area_central, bg="white")
        self.formulario.pack(anchor="w", padx=10, pady=10)  # Anclar el formulario a la izquierda

        # Etiqueta y entrada para el valor X alineada a la izquierda
        tk.Label(self.formulario, text="Ingrese el valor X:", bg="white", font=("Times New Roman", 12)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entrada_x = tk.Entry(self.formulario, width=10, justify="center")
        self.entrada_x.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        #Espacio en blanco
        tk.Label(self.formulario, text="                 ", bg="white",font=("Times New Roman", 12)).grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Etiqueta y entrada para el valor Z alineada a la izquierda
        tk.Label(self.formulario, text="Ingrese el valor Z:", bg="white",font=("Times New Roman", 12)).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.entrada_z = tk.Entry(self.formulario, width=10, justify="center")
        self.entrada_z.grid(row=0, column=4, padx=5, pady=5, sticky="e")

        #Espacio en blanco
        tk.Label(self.formulario, text="                 ", bg="white",font=("Times New Roman", 12)).grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # Botón para enviar los datos
        tk.Button(self.formulario, text="Aceptar", command=self.ejecutar_funcion,font=("Times New Roman", 12)).grid(row=0, column=6, columnspan=2, pady=5, sticky="n")


    def ejecutar_funcion(self):
        # Función vacía para el momento
        x = self.entrada_x.get()
        z = self.entrada_z.get()
        print(f"Valores ingresados: X={x}, Z={z}")
        # Aquí puedes procesar los valores o realizar una acción

    def accion_eyector(self):
        print("Eyector activado")

    def accion_camara(self):
        print("Cámara activada")

    def salir_app(self):
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = EasyPickApp(root)
    root.mainloop()
