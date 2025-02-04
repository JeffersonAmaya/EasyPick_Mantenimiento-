import tkinter as tk
from tkinter import messagebox, simpledialog

class EstanteriaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Estantería Interactiva")

        # Configuración inicial
        self.total_length = 105  # Longitud total de la fila en cm
        self.min_spacing = 5    # Espaciado mínimo entre divisores en cm
        self.rows = 6           # Número de filas
        self.divisiones_por_fila = {i: [0, 15, 30, 45, 60, 75, 90, 105] for i in range(self.rows)}

        # Canvas para dibujar la estantería
        self.canvas = tk.Canvas(self.root, width=900, height=700, bg="white")
        self.canvas.pack(pady=20)

        # Crear un frame para los botones
        self.boton_frame = tk.Frame(self.root, bg="white", bd=0, relief="solid")
        self.boton_frame.place(x=200, y=680)  # Coloca el frame dentro del canvas

        # Botones dentro del frame
        self.boton_agregar = tk.Button(self.boton_frame, text="Agregar Divisor", command=self.agregar_divisor)
        self.boton_eliminar = tk.Button(self.boton_frame, text="Eliminar Divisor", command=self.eliminar_divisor)
        self.boton_modificar = tk.Button(self.boton_frame, text="Modificar Divisor", command=self.modificar_divisor)

        # Colocar los botones dentro del frame
        self.boton_agregar.pack(side=tk.LEFT, padx=10)
        self.boton_eliminar.pack(side=tk.LEFT, padx=10)
        self.boton_modificar.pack(side=tk.LEFT, padx=10)

        self.dibujar_estanteria()

    def dibujar_estanteria(self):
        """Dibuja la estantería y sus divisores."""
        self.canvas.delete("all")
        espacio_entre_estanterias = 40  # Espacio adicional entre las estanterías
        contador = 1  # Contador para numerar los espacios
        for row, divisiones in self.divisiones_por_fila.items():
            y_offset = 50 + row * (70 + espacio_entre_estanterias)  # Ajustamos el offset de y para crear el espacio
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
                letra_fila = chr(65 + row)  # Genera A, B, C, etc.
                self.canvas.create_text(x, y_offset + 30, text=f"{letra_fila}{i + 1}", fill="black",font=("Arial", 8))

                # Mostrar números de espacio como 001, 002, 003, etc. entre los divisores
                if i > 0:
                    x_text = 50 + ((divisor + divisiones[i - 1]) / 2 / self.total_length) * 800
                    numero_espacio = f"ID {contador:03d}"  # Formatea el número con 3 dígitos
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
        except ValueError:
            messagebox.showerror("Error", "Valor inválido. Inténtalo de nuevo.")

    def eliminar_divisor(self):
        """Elimina un divisor de la estantería por índice (A1, A2, B1, B2, etc.)."""
        fila = self.solicitar_fila()
        if fila is None:
            return

        # Solicitar el índice del divisor a eliminar (Ejemplo: A1, B2)
        divisor_indice = simpledialog.askstring("Eliminar Divisor", "Introduce el índice del divisor :")
        if divisor_indice is None:
            return

        try:
            letra_fila = divisor_indice[0].upper()  # Letra de la fila (A, B, C...)
            num_divisor = int(divisor_indice[1:]) - 1  # El número del divisor (1, 2, 3...) -> índice 0, 1, 2

            # Verificar que la letra de la fila sea válida
            if letra_fila < 'A' or letra_fila > chr(ord('A') + self.rows - 1):
                messagebox.showerror("Error", "Fila inválida.")
                return

            if num_divisor < 0 or num_divisor >= len(self.divisiones_por_fila[fila]):
                messagebox.showerror("Error", "Índice de divisor fuera de rango.")
                return

            # Obtener el valor real del divisor
            divisor = self.divisiones_por_fila[fila][num_divisor]

            if divisor in [0, self.total_length]:
                messagebox.showerror("Error", "No puedes eliminar los divisores de los extremos.")
                return

            # Eliminar el divisor
            self.divisiones_por_fila[fila].remove(divisor)
            self.dibujar_estanteria()

        except (ValueError, IndexError):
            messagebox.showerror("Error", "Índice inválido. Inténtalo de nuevo.")


    def modificar_divisor(self):
        """Modifica un divisor de la estantería por índice (A1, A2, B1, B2, etc.)."""
        fila = self.solicitar_fila()
        if fila is None:
            return

        # Solicitar el índice del divisor a modificar (Ejemplo: A1, B2)
        divisor_indice = simpledialog.askstring("Modificar Divisor", "Introduce el índice del divisor :")
        if divisor_indice is None:
            return

        try:
            letra_fila = divisor_indice[0].upper()  # Letra de la fila (A, B, C...)
            num_divisor = int(divisor_indice[1:]) - 1  # El número del divisor (1, 2, 3...) -> índice 0, 1, 2

            # Verificar que la letra de la fila sea válida
            if letra_fila < 'A' or letra_fila > chr(ord('A') + self.rows - 1):
                messagebox.showerror("Error", "Fila inválida.")
                return

            if num_divisor < 0 or num_divisor >= len(self.divisiones_por_fila[fila]):
                messagebox.showerror("Error", "Índice de divisor fuera de rango.")
                return

            # Obtener el valor real del divisor
            divisor = self.divisiones_por_fila[fila][num_divisor]

            if divisor in [0, self.total_length]:
                messagebox.showerror("Error", "No puedes modificar los divisores de los extremos.")
                return

            # Solicitar la nueva posición del divisor
            nuevo = int(simpledialog.askstring("Nueva Posición", "Introduce la nueva posición del divisor (en cm):"))
            if nuevo <= 0 or nuevo >= self.total_length:
                messagebox.showerror("Error", "No puedes mover divisores a los extremos.")
                return
            if any(abs(nuevo - d) < self.min_spacing for d in self.divisiones_por_fila[fila] if d != divisor):
                messagebox.showerror("Error", f"El divisor debe estar al menos a {self.min_spacing} cm de otro.")
                return

            # Modificar el divisor
            self.divisiones_por_fila[fila][self.divisiones_por_fila[fila].index(divisor)] = nuevo
            self.divisiones_por_fila[fila].sort()
            self.dibujar_estanteria()

        except (ValueError, IndexError):
            messagebox.showerror("Error", "Índice inválido. Inténtalo de nuevo.")


# Crear ventana principal
root = tk.Tk()
estanteria_app = EstanteriaApp(root)
root.mainloop()
