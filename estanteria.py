import tkinter as tk
from tkinter import messagebox
import json
import os
import string

class ShelfApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1000x1300")  # Tamaño de la ventana
        self.title("MultiSlider Shelf")  # Título de la ventana
        self.configure(bg="white")  # Cambiar el fondo de la ventana principal a blanco

        self.attributes("-fullscreen", True)  # Iniciar en pantalla completa
        self.bind("<F11>", lambda event: self.attributes("-fullscreen", not self.attributes("-fullscreen")))  # Alternar con F11
        self.bind("<Escape>", lambda event: self.attributes("-fullscreen", False))  # Salir con Escape

        self.shelves = []  # Lista de estanterías añadidas
        self.buttons = {}  # Diccionario de botones (óvalos)
        self.move_x = 30

        # Crear el lienzo de guías
        self.guides_canvas = tk.Canvas(self, width=80, height=1800, bg="white", highlightthickness=0)
        self.guides_canvas.place(x=35, y=50)  # Mueve el panel de guías más a la derecha

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
        shelf_canvas = tk.Canvas(self, width=900, height=150, bg="white",highlightthickness=0)
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
        self.main_canvas_1 = tk.Canvas(self, width=11, height=1800, bg="gray", highlightthickness=0)
        self.main_canvas_1.place(x=95+self.move_x, y=50)
        self.main_canvas_2 = tk.Canvas(self, width=11, height=1800, bg="gray", highlightthickness=0)
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

                
if __name__ == "__main__":
    
    app = ShelfApp()
    app.mainloop()

