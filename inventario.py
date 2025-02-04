import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
from tkinter import messagebox
import json
import os
from PIL import Image, ImageTk

class InventoryManager:
    def __init__(self, root):
        self.root = root
        self.ARCHIVO_COORDENADAS = "coordenadas_estanteria.json"
        self.ARCHIVO_INVENTARIO = "inventario_productos.json"
        self.RUTA_IMAGEN_DEFECTO = "img/easyPickR.jpg"
        self.entradas = {}
        self.ventana_imagen_grande = None
        
        # Configuración inicial de la ventana
        self.root.attributes("-fullscreen", True)
        self.root.bind("<F11>", lambda event: self.root.attributes("-fullscreen", 
                                            not self.root.attributes("-fullscreen")))
        self.root.bind("<Escape>", lambda event: self.root.attributes("-fullscreen", False))
        
        self.crear_interfaz()

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

    def crear_interfaz(self):

        self.guardar_datos
        coordenadas = self.cargar_coordenadas()
        inventario = self.cargar_inventario()

        self.root.title("Inventario de Productos")

        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()

        ancho_canvas = 650
        alto_canvas = 1670

        x_pos = (ancho_pantalla - ancho_canvas) // 2
        y_pos = 50

        frame_central = tk.Frame(self.root, width=ancho_canvas, height=alto_canvas)
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
            tk.Label(frame_contenido, text=texto, font=("Arial", 10, "bold"), 
                    borderwidth=1, relief="solid").grid(row=0, column=col, padx=5, 
                    pady=5, sticky="nsew")

        for idx, (id_producto, coord) in enumerate(coordenadas.items(), start=1):
            tk.Label(frame_contenido, text=id_producto, borderwidth=1, 
                    relief="solid").grid(row=idx, column=0, padx=5, pady=5, sticky="nsew")

            etiqueta_imagen = tk.Label(frame_contenido, width=20, height=5, relief="solid")
            etiqueta_imagen.grid(row=idx, column=1, padx=5, pady=5, sticky="nsew")
            
            self.mostrar_imagen_defecto(etiqueta_imagen)
            imagen_path = inventario.get(id_producto, {}).get("imagen", "")
            if imagen_path:
                self.mostrar_imagen(etiqueta_imagen, imagen_path)

            etiqueta_imagen.bind("<Button-1>", 
                               lambda event, imagen_path=imagen_path: 
                               self.mostrar_imagen_grande(imagen_path))

            proveedor_entry = tk.Entry(frame_contenido, width=20)
            proveedor_entry.grid(row=idx, column=2, padx=5, pady=5, sticky="nsew")
            proveedor_entry.insert(0, inventario.get(id_producto, {}).get("proveedor", ""))

            cantidad_entry = tk.Entry(frame_contenido, width=10)
            cantidad_entry.grid(row=idx, column=3, padx=5, pady=5, sticky="nsew")
            cantidad_entry.insert(0, inventario.get(id_producto, {}).get("cantidad", ""))

            precio_entry = tk.Entry(frame_contenido, width=10)
            precio_entry.grid(row=idx, column=4, padx=5, pady=5, sticky="nsew")
            precio_entry.insert(0, inventario.get(id_producto, {}).get("precio", ""))

            unidad_combo = ttk.Combobox(frame_contenido, 
                                      values=["UND", "Metro", "Bolsa"], 
                                      state="readonly", width=10)
            unidad_combo.grid(row=idx, column=5, padx=5, pady=5, sticky="nsew")
            unidad_combo.set(inventario.get(id_producto, {}).get("unidad", "UND"))

            self.entradas[id_producto] = {
                "imagen": etiqueta_imagen,
                "proveedor": proveedor_entry,
                "cantidad": cantidad_entry,
                "precio": precio_entry,
                "unidad": unidad_combo,
            }

        frame_bajos = tk.Frame(self.root, width=ancho_canvas, height=100)
        frame_bajos.place(x=x_pos, y=alto_pantalla - 100)

        canvas_bajos = tk.Canvas(frame_bajos, width=ancho_canvas, height=100)
        canvas_bajos.pack(side="left", fill="both", expand=True)

        btn_guardar = tk.Button(canvas_bajos, text="Guardar Inventario", 
                              command=self.guardar_datos)
        btn_guardar.place(relx=0.3, rely=0.5, anchor="center")

        btn_cargar_imagen = tk.Button(canvas_bajos, text="Cargar Imagen", 
                                    command=self.cargar_imagen_id)
        btn_cargar_imagen.place(relx=0.6, rely=0.5, anchor="center")
        
        btn_mover_id = tk.Button(canvas_bajos, text="Mover ID", command=self.mover_id)
        btn_mover_id.place(relx=0.45, rely=0.5, anchor="center")

        # btn_mover_grupo = tk.Button(canvas_bajos, text="Mover Grupo", command=self.abrir_mover_grupo)
        # btn_mover_grupo.place(relx=0.75, rely=0.5, anchor="center")


        frame_contenido.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

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
        messagebox.showinfo("Guardado", "Inventario guardado exitosamente")

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
        self.crear_interfaz()
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
    app = InventoryManager(root)
    root.mainloop()