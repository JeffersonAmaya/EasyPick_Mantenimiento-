import tkinter as tk

class MultiSlider(tk.Canvas):
    def __init__(self, parent, width=900, height=150, min_val=0, max_val=105):
        super().__init__(parent, width=width, height=height, bg="white")
        self.min_val = min_val
        self.max_val = max_val
        self.width = width
        self.height = height
        self.step = 5  # Los divisores solo pueden ubicarse cada 5 cm
        
        self.values = [min_val, max_val]
        self.shelf = self.create_rectangle(20, height//2 - 10, width - 20, height//2 + 10, fill="gray", outline="black")
        self.dividers = []
        
        for val in self.values:
            self.dividers.append(self.create_rectangle(0, 0, 10, height//2, fill="black", outline="black"))
        
        self.update_positions()  # Eliminamos self.create_guides()
        
        self.bind("<Double-Button-1>", self.add_divider)
        self.bind("<Button-3>", self.remove_divider)
    
    def value_to_x(self, val):
        return 20 + (val - self.min_val) / (self.max_val - self.min_val) * (self.width - 40)
    
    def update_positions(self):
        for i, val in enumerate(self.values):
            x = self.value_to_x(val)
            self.coords(self.dividers[i], x - 5, 10, x + 5, self.height//2+10)
    
    def add_divider(self, event):
        x = event.x
        value = self.min_val + ((x - 20) / (self.width - 40)) * (self.max_val - self.min_val)
        value = round(value / self.step) * self.step
        if value in self.values:
            return
        self.values.append(value)
        self.values.sort()
        self.dividers.insert(self.values.index(value), self.create_rectangle(0, 0, 10, self.height//2, fill="brown", outline="black"))
        self.update_positions()
    
    def remove_divider(self, event):
        if len(self.values) <= 2:
            return
        x_clicked = event.x
        for i in range(1, len(self.values) - 1):
            if abs(self.value_to_x(self.values[i]) - x_clicked) < 10:
                del self.values[i]
                self.delete(self.dividers[i])
                del self.dividers[i]
                return

class ShelfManager:
    def __init__(self, root):
        self.root = root
        self.shelves = []
        self.create_vertical_guides()
    
    def create_vertical_guides(self):
        self.guide_canvas = tk.Canvas(self.root, width=50, height=600, bg="white")
        self.guide_canvas.pack(side=tk.LEFT, fill=tk.Y)
        for y in range(0, 105 + 1, 15):
            y_pos = 50 + (y * 4)  # Ajuste de escala para distribución vertical
            self.guide_canvas.create_oval(20, y_pos, 30, y_pos + 10, fill="black")
            self.guide_canvas.tag_bind(self.guide_canvas.create_text(25, y_pos + 20, text=f"{y} cm"), "<Button-1>", lambda event, y_pos=y_pos: self.add_shelf(y_pos))
    
    def add_shelf(self, y_pos):
        new_shelf = MultiSlider(self.root)
        new_shelf.place(x=50, y=y_pos)
        self.shelves.append(new_shelf)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x1000")
    root.title("MultiSlider Estantería")
    
    shelf_manager = ShelfManager(root)
    
    root.mainloop()
