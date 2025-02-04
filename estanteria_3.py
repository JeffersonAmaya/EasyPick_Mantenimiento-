import tkinter as tk
from tkinter import messagebox

class ShelfApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1000x1300")  # Tamaño de la ventana
        self.title("MultiSlider Shelf")  # Título de la ventana
        self.configure(bg="white")  # Cambiar el fondo de la ventana principal a blanco


        self.shelves = []  # Lista de estanterías añadidas
        self.buttons = {}  # Diccionario de botones (óvalos)

        # Crear el lienzo de guías
        self.guides_canvas = tk.Canvas(self, width=80, height=600, bg="white",highlightthickness=0)
        self.guides_canvas.pack(side=tk.LEFT, fill=tk.Y)

        self.create_vertical_guides()  # Crear las guías verticales

    def create_vertical_guides(self):
        # Crear los botones óvalos en la columna de la izquierda
        for y in range(0, 105 + 1, 15):
            y_pos = 50 + (y * 10)  # Calcular la posición Y de los óvalos
            button = tk.Button(self.guides_canvas, text=f"{y} cm >",font=("Arial", 10, "bold"), width=6, height=2, bg="red")
            button.place(x=20, y=y_pos)
            button.config(command=lambda y_pos=y_pos: self.toggle_shelf(y_pos))

            self.buttons[y_pos] = button  # Guardar el botón en el diccionario

    def toggle_shelf(self, y_pos):
        # Verificar si ya existe una estantería en esa posición
        for shelf in self.shelves:
            if shelf["y_pos"] == y_pos:
                # Si hay una estantería, preguntamos si está seguro de eliminarla
                self.confirm_delete_shelf(y_pos)
                return
        # Si no existe, agregamos una estantería
        self.add_shelf(y_pos)

    def add_shelf(self, y_pos):
        # Verifica si ya existe una estantería en esa posición
        for shelf in self.shelves:
            if shelf["y_pos"] == y_pos:
                messagebox.showwarning("Advertencia", "Ya existe una estantería en esta posición.")
                return  # No agrega una estantería si ya hay una en esa posición

        # Crear una nueva estantería
        shelf_canvas = tk.Canvas(self, width=900, height=150, bg="white",highlightthickness=0)
        shelf_canvas.place(x=80, y=y_pos - 45)

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
            divider = shelf_canvas.create_rectangle(x - 5, 10, x + 5, 80, fill="black", outline="black")
            shelf_data["dividers"].append(divider)

        # Crear guías y etiquetas
        self.create_guides(shelf_data)
        self.update_positions(shelf_data)
        self.create_labels(shelf_data)

        # Asignar eventos
        shelf_canvas.bind("<Double-Button-1>", lambda event, data=shelf_data: self.add_divider(event, data))
        shelf_canvas.bind("<Button-3>", lambda event, data=shelf_data: self.remove_divider(event, data))

        # Cambiar el color del botón a verde cuando haya una estantería
        self.buttons[y_pos].config(bg="green")

    def delete_shelf(self, y_pos):
        # Buscar si hay estantería en la posición y_pos
        for shelf in self.shelves:
            if shelf["y_pos"] == y_pos:
                shelf["canvas"].destroy()
                self.shelves.remove(shelf)

                # Cambiar el color del botón a rojo cuando no haya estantería
                self.buttons[y_pos].config(bg="red")
                return

        # Si no hay estantería en esa posición
        messagebox.showwarning("Advertencia", "No existe una estantería en esta posición para eliminar.")

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
            shelf_data["canvas"].coords(shelf_data["dividers"][i], x - 5, 10, x + 5, 90)# Acá modifico la altura del divisor 
        self.update_labels(shelf_data)
        self.update_space_ids(shelf_data)

    def add_divider(self, event, shelf_data):
        # Agregar un divisor en la posición del clic
        x = event.x
        value = self.x_to_value(x)
        if value in shelf_data["values"]:
            messagebox.showwarning("Advertencia", f"Ya existe un divisor en {value} cm")
            return  
        shelf_data["values"].append(value)
        shelf_data["values"].sort()
        index = shelf_data["values"].index(value)
        divider = shelf_data["canvas"].create_rectangle(0, 0, 10, 80, fill="brown", outline="black")
        shelf_data["dividers"].insert(index, divider)
        self.update_positions(shelf_data)
        self.create_labels(shelf_data)

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
                return
        messagebox.showwarning("Advertencia", "No se encontró un divisor en esta posición para eliminar")

    def create_labels(self, shelf_data):
        # Crear las etiquetas de los valores de los divisores
        for label in shelf_data["labels"]:
            label.destroy()
        shelf_data["labels"].clear()

    def update_labels(self, shelf_data):
        # Actualizar las etiquetas de los valores de los divisores
        for i, val in enumerate(shelf_data["values"]):
            y_pos = 130 if val not in [0, 105] else 150
            label = tk.Label(shelf_data["canvas"], text=f"{val} cm", bg="white")
            label.place(x=self.value_to_x(val, shelf_data) - 15, y=y_pos)
            shelf_data["labels"].append(label)

    def create_guides(self, shelf_data):
        # Crear guías de 1 cm en 1 cm
        for i in range(0, 105 + 1, 5):
            x = self.value_to_x(i, shelf_data)
            shelf_data["canvas"].create_oval(x - 2, 72, x + 2, 75, fill="black")

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

if __name__ == "__main__":
    app = ShelfApp()
    app.mainloop()
