import tkinter as tk
from tkinter import messagebox

class MultiSlider(tk.Canvas):
    def __init__(self, parent, width=900, height=150, min_val=0, max_val=105):
        super().__init__(parent, width=width, height=height, bg="white")
        self.min_val = min_val
        self.max_val = max_val
        self.width = width
        self.height = height
        self.step = 5  # Los divisores solo pueden ubicarse cada 5 cm
        
        self.values = [min_val, max_val]
        self.labels = []  # Etiquetas para los valores de los separadores
        self.space_labels = {}  # Diccionario para almacenar las etiquetas de los IDs de los espacios
        self.space_ids = {}  # Diccionario para almacenar los IDs de los espacios
        self.next_id = 1  # Contador para los IDs
        
        self.shelf = self.create_rectangle(20, height//2 - 10, width - 20, height//2 + 10, fill="gray", outline="black")
        self.dividers = []
        
        for val in self.values:
            self.dividers.append(self.create_rectangle(0, 0, 10, height//2, fill="black", outline="black"))
        
        self.create_guides()
        self.update_positions()
        self.create_labels()
        
        self.bind("<Double-Button-1>", self.add_divider)
        self.bind("<Button-3>", self.remove_divider)
    
    def value_to_x(self, val):
        return 20 + (val - self.min_val) / (self.max_val - self.min_val) * (self.width - 40)
    
    def x_to_value(self, x):
        raw_value = self.min_val + ((x - 20) / (self.width - 40)) * (self.max_val - self.min_val)
        return round(raw_value / self.step) * self.step  # Ajustar al múltiplo más cercano de 5
    
    def update_positions(self):
        # Primero actualizamos las posiciones de los divisores
        for i, val in enumerate(self.values):
            x = self.value_to_x(val)
            self.coords(self.dividers[i], x - 5, 10, x + 5, self.height//2+10)
        self.update_labels()
        self.update_space_ids()
    
    def add_divider(self, event):
        x = event.x
        value = self.x_to_value(x)
        if value in self.values:
            messagebox.showwarning("Aviso", f"Ya existe un separador en la posición {value} cm")
            return  # Evita agregar un divisor en una posición existente
        self.values.append(value)
        self.values.sort()
        self.dividers.insert(self.values.index(value), self.create_rectangle(0, 0, 10, self.height//2, fill="brown", outline="black"))
        self.update_positions()
        self.create_labels()
    
    def remove_divider(self, event):
        if len(self.values) <= 2:
            return
        x_clicked = event.x
        for i in range(1, len(self.values) - 1):
            if abs(self.value_to_x(self.values[i]) - x_clicked) < 10:
                # Eliminar el divisor y su valor correspondiente
                removed_value = self.values[i]
                del self.values[i]
                self.delete(self.dividers[i])  # Eliminar el divisor visualmente
                del self.dividers[i]
                # Imprime el valor del separador eliminado
                #print(f"Separador de {removed_value} cm eliminado")
                self.update_space_ids()
                return
        messagebox.showwarning("Aviso", "No se encuentra un separador en esa zona para eliminar")
        
    def create_labels(self):
        # Primero eliminamos las etiquetas existentes
        for label in self.labels:
            label.destroy()
        self.labels.clear()
    
    def update_labels(self):
        # Actualizamos las posiciones y valores de las etiquetas
        for i, label in enumerate(self.labels):
            y_pos = 130 if self.values[i] not in [self.min_val, self.max_val] else 150
            label.config(text=f"{self.values[i]} cm")
            label.place(x=self.value_to_x(self.values[i]) - 15, y=y_pos)
    
    def create_guides(self):
        for i in range(self.min_val, self.max_val + 1, self.step):
            x = self.value_to_x(i)
            self.create_oval(x - 2, self.height//2 + 10, x + 2, self.height//2 + 14, fill="black")
            # Formatear el número para que siempre tenga dos dígitos
            guide_label = tk.Label(root, text=f"{i:03d}", font=("Arial", 8))
            guide_label.place(x=x + 40, y=self.height//2 + 65)
    
    def update_space_ids(self):
        # Limpiamos las etiquetas de los espacios existentes
        for label in self.space_labels.values():
            label.destroy()
        self.space_labels.clear()
        self.space_ids.clear()
        self.next_id = 1
        
        # Asignamos IDs a los espacios entre los divisores
        for i in range(len(self.values) - 1):
            start = self.values[i]
            end = self.values[i + 1]
            space_id = f"{self.next_id}"
            self.space_ids[(start, end)] = space_id
            
            # Calcular la posición central del espacio
            x_start = self.value_to_x(start)
            x_end = self.value_to_x(end)
            x_center = (x_start + x_end) / 2
            
            # Formatear el ID para que se muestre verticalmente
            vertical_text = "\n".join(space_id)
            
            # Crear una etiqueta en la posición central del espacio
            label = tk.Label(self, text=vertical_text, font=("Arial", 10, "bold"), bg="white")
            label.place(x=x_center-5, y=self.height//2 - 50)  # Ajustar la posición y
            self.space_labels[(start, end)] = label
            
            self.next_id += 1
        
        # Imprimimos los IDs de los espacios (puedes eliminarlo si no lo necesitas)
        print("Espacios con IDs:")
        for space, id_ in self.space_ids.items():
            print(f"{id_}: {space[0]} cm - {space[1]} cm")
    
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x200")
    root.title("MultiSlider Estantería")

    slider = MultiSlider(root)
    slider.place(x=50, y=50)

    root.mainloop()