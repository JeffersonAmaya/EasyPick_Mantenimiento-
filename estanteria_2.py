import tkinter as tk
import json
import os
from PIL import Image, ImageTk
from tkinter import messagebox, simpledialog

class EstanteriaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Estantería Interactiva")

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

        # Canvas para dibujar la estantería
        self.canvas = tk.Canvas(self.root, width=900, height=700, bg="white")
        self.canvas.pack(pady=20)

        # Crear un frame para los botones
        self.boton_frame = tk.Frame(self.root, bg="white", bd=0, relief="solid")
        self.boton_frame.place(x=200, y=680)

        # Botones
        self.boton_agregar = tk.Button(self.boton_frame, text="Agregar Divisor", command=self.agregar_divisor)
        self.boton_eliminar = tk.Button(self.boton_frame, text="Eliminar Divisor", command=self.eliminar_divisor)
        self.boton_modificar = tk.Button(self.boton_frame, text="Modificar Divisor", command=self.modificar_divisor)
        self.boton_restaurar = tk.Button(self.boton_frame, text="Restaurar Valores", command=self.restaurar_valores_defecto)

        # Colocar los botones
        self.boton_agregar.pack(side=tk.LEFT, padx=10)
        self.boton_eliminar.pack(side=tk.LEFT, padx=10)
        self.boton_modificar.pack(side=tk.LEFT, padx=10)
        self.boton_restaurar.pack(side=tk.LEFT, padx=10)

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
        espacio_entre_estanterias = 40
        contador = 1
        for row, divisiones in self.divisiones_por_fila.items():
            # Convertir row a entero para evitar problemas de tipo
            row = int(row)
            y_offset = 50 + row * (70 + espacio_entre_estanterias)
            self.canvas.create_rectangle(50, y_offset + 20, 850, y_offset , fill="gainsboro")

            for i, divisor in enumerate(divisiones):
                x = 50 + (divisor / self.total_length) * 800
                self.canvas.create_line(x, y_offset - 40, x, y_offset + 20, fill="black", width=5)

                # Mostrar etiquetas de distancia
                if i > 0:
                    distancia = divisor - divisiones[i - 1]
                    x_text = 50 + ((divisor + divisiones[i - 1]) / 2 / self.total_length) * 800
                    self.canvas.create_text(x_text, y_offset + 10 , text=f"{distancia} cm", fill="steel blue",font=("Arial", 8))

                # Mostrar etiquetas A1, A2, A3, etc. en los divisores
                letra_fila = chr(65 + row)
                self.canvas.create_text(x, y_offset + 30, text=f"{letra_fila}{i + 1}", fill="black",font=("Arial", 8))

                # Mostrar números de espacio
                if i > 0:
                    x_text = 50 + ((divisor + divisiones[i - 1]) / 2 / self.total_length) * 800
                    numero_espacio = f"ID {contador:03d}"
                    self.canvas.create_text(x_text, y_offset - 30, text=numero_espacio, fill="#00AADA", font=("Arial", 8))
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

# Crear ventana principal
root = tk.Tk()
estanteria_app = EstanteriaApp(root)
root.mainloop()