import cv2
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import datetime
try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class ResultsWindow(ctk.CTkToplevel):
    def __init__(self, parent, history):
        super().__init__(parent)
        self.parent_app = parent
        self.title("Panel de Resultados Históricos")
        self.geometry("900x650")
        
        self.attributes('-topmost', True)
        self.focus()

        self.title_label = ctk.CTkLabel(self, text="Estadísticas y Resultados Acumulados", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))
        
        # Clasificar la historia
        good_history = [item for item in history if item['status'] == "CORRECTO"]
        bad_history = [item for item in history if item['status'] == "ERRÓNEO"]

        # Crear contenedor para las dos tablas
        self.tables_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tables_container.pack(fill="both", expand=True, padx=20, pady=10)

        # TABLA IZQUIERDA: CORRECTAS
        self.left_frame = ctk.CTkFrame(self.tables_container)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        lbl_left = ctk.CTkLabel(self.left_frame, text="✅ CORRECTAS (<= 5)", font=ctk.CTkFont(size=18, weight="bold"), text_color="#00FFAA")
        lbl_left.pack(pady=10)

        self.scroll_left = ctk.CTkScrollableFrame(self.left_frame, fg_color="#1e1e24")
        self.scroll_left.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        if not good_history:
            ctk.CTkLabel(self.scroll_left, text="No hay capturas\ncorrectas todavía.").pack(pady=20)
        else:
            for item in good_history:
                text = f"[{item['time']}] Cap. #{item['id']} -> {item['count']} objetos"
                ctk.CTkLabel(self.scroll_left, text=text, font=ctk.CTkFont(size=14, weight="bold"), text_color="#00FFAA").pack(anchor="w", padx=10, pady=5)

        total_good_captures = len(good_history)
        self.total_good_lbl = ctk.CTkLabel(self.left_frame, text=f"Total de capturas correctas: {total_good_captures}", font=ctk.CTkFont(size=14, weight="bold"))
        self.total_good_lbl.pack(pady=(10, 5))
        
        btn_reset_good = ctk.CTkButton(self.left_frame, text="🔄 Resetear Correctas", fg_color="#555555", hover_color="#D9534F", command=self.reset_good)
        btn_reset_good.pack(pady=(0, 10))

        # TABLA DERECHA: ERRÓNEAS
        self.right_frame = ctk.CTkFrame(self.tables_container)
        self.right_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))

        lbl_right = ctk.CTkLabel(self.right_frame, text="❌ ERRÓNEAS (> 5 o 0)", font=ctk.CTkFont(size=18, weight="bold"), text_color="#FF4C4C")
        lbl_right.pack(pady=10)

        self.scroll_right = ctk.CTkScrollableFrame(self.right_frame, fg_color="#1e1e24")
        self.scroll_right.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        if not bad_history:
            ctk.CTkLabel(self.scroll_right, text="No hay capturas\nerróneas todavía.").pack(pady=20)
        else:
            for item in bad_history:
                text = f"[{item['time']}] Cap. #{item['id']} -> {item['count']} objetos"
                ctk.CTkLabel(self.scroll_right, text=text, font=ctk.CTkFont(size=14, weight="bold"), text_color="#FF4C4C").pack(anchor="w", padx=10, pady=5)

        total_bad_captures = len(bad_history)
        self.total_bad_lbl = ctk.CTkLabel(self.right_frame, text=f"Total de capturas erróneas: {total_bad_captures}", font=ctk.CTkFont(size=14, weight="bold"))
        self.total_bad_lbl.pack(pady=(10, 5))

        btn_reset_bad = ctk.CTkButton(self.right_frame, text="🔄 Resetear Erróneas", fg_color="#555555", hover_color="#D9534F", command=self.reset_bad)
        btn_reset_bad.pack(pady=(0, 10))

    def reset_good(self):
        # Filtramos dejando SOLO los que no son correctos (es decir, los erróneos)
        self.parent_app.capture_history = [item for item in self.parent_app.capture_history if item['status'] != "CORRECTO"]
        self.destroy() # Cerramos esta ventana
        self.parent_app.show_results() # Volvemos a abrirla limpia

    def reset_bad(self):
        # Filtramos dejando SOLO los que no son erróneos (es decir, los correctos)
        self.parent_app.capture_history = [item for item in self.parent_app.capture_history if item['status'] != "ERRÓNEO"]
        self.destroy()
        self.parent_app.show_results()


class ObjectCounterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana principal
        self.title("Sistema Avanzado de Detección y Conteo")
        self.geometry("1200x800")
        # Forzar pantalla completa (maximizado real en Windows)
        self.after(0, lambda: self.state('zoomed'))
        
        # --- Variables del historial ---
        self.capture_history = []
        self.current_capture_id = 1
        
        # Grid para dividir la pantalla (Barra lateral y Panel principal)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1) # El panel derecho se expande

        # ==========================================
        # PANEL IZQUIERDO (Barra lateral de opciones)
        # ==========================================
        self.sidebar_frame = ctk.CTkFrame(self, width=350, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1) # Empuja los botones al fondo

        # 1. Título
        self.title_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Control de Calidad", 
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.status_label = ctk.CTkLabel(
            self.sidebar_frame, text="Buscando cámara...", text_color="yellow", font=ctk.CTkFont(size=14)
        )
        self.status_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # 2. Selector de Modo
        self.mode_label = ctk.CTkLabel(self.sidebar_frame, text="Modo de Detección", font=ctk.CTkFont(size=18, weight="bold"))
        self.mode_label.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")

        self.detection_mode = ctk.StringVar(value="Contornos")
        self.radio_ia = ctk.CTkRadioButton(self.sidebar_frame, text="IA (YOLO - Visión General)", variable=self.detection_mode, value="IA")
        self.radio_ia.grid(row=3, column=0, padx=20, pady=(5, 5), sticky="w")
        
        self.radio_contornos = ctk.CTkRadioButton(self.sidebar_frame, text="Visión Clásica (Objetos / Pastillas)", variable=self.detection_mode, value="Contornos")
        self.radio_contornos.grid(row=4, column=0, padx=20, pady=(5, 20), sticky="w")

        # 3. Sliders de Tamaño
        self.sliders_label = ctk.CTkLabel(self.sidebar_frame, text="Ajustes de Tamaño (Solo Visión Clásica)", font=ctk.CTkFont(size=14, weight="bold"))
        self.sliders_label.grid(row=5, column=0, padx=20, pady=(10, 5), sticky="w")

        self.slider_min_label = ctk.CTkLabel(self.sidebar_frame, text="Tamaño Mínimo (Ignorar polvo):", font=ctk.CTkFont(size=12))
        self.slider_min_label.grid(row=6, column=0, padx=20, pady=(5, 0), sticky="w")
        self.sensitivity_slider = ctk.CTkSlider(self.sidebar_frame, from_=50, to=5000, width=280)
        self.sensitivity_slider.set(800)
        self.sensitivity_slider.grid(row=7, column=0, padx=20, pady=(0, 15), sticky="n")

        self.slider_max_label = ctk.CTkLabel(self.sidebar_frame, text="Tamaño Máximo (Ignorar base del PC):", font=ctk.CTkFont(size=12))
        self.slider_max_label.grid(row=8, column=0, padx=20, pady=(5, 0), sticky="w")
        self.max_area_slider = ctk.CTkSlider(self.sidebar_frame, from_=5000, to=150000, width=280)
        self.max_area_slider.set(40000)
        self.max_area_slider.grid(row=9, column=0, padx=20, pady=(0, 20), sticky="n")

        # 4. Botón de Capturar
        self.btn_capture = ctk.CTkButton(
            self.sidebar_frame, 
            text="📸 CAPTURAR Y VALIDAR", 
            height=60, 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            fg_color="#D9534F",
            hover_color="#C9302C",
            corner_radius=10, 
            command=self.capture_and_validate
        )
        self.btn_capture.grid(row=10, column=0, padx=20, pady=(10, 10), sticky="ew")

        # 5. Nuevo Botón de Resultados
        self.btn_results = ctk.CTkButton(
            self.sidebar_frame, 
            text="📊 VER RESULTADOS ACUMULADOS", 
            height=40, 
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#337AB7",
            hover_color="#286090",
            corner_radius=10, 
            command=self.show_results
        )
        self.btn_results.grid(row=11, column=0, padx=20, pady=(0, 30), sticky="ew")

        # ==========================================
        # PANEL DERECHO (Cámara en grande y Texto)
        # ==========================================
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Contador Gigante
        self.counter_label = ctk.CTkLabel(
            self.main_frame,
            text="Objetos en pantalla: 0",
            font=ctk.CTkFont(family="Segoe UI", size=45, weight="bold"),
            text_color="#00FFAA"
        )
        self.counter_label.grid(row=0, column=0, pady=(0, 20))

        # Marco de video gigante
        self.video_label = ctk.CTkLabel(self.main_frame, text="")
        self.video_label.grid(row=1, column=0, sticky="nsew")

        # ==========================================
        # INICIALIZACIÓN
        # ==========================================
        try:
            if YOLO:
                self.model = YOLO("yolov8n.pt")
                self.status_label.configure(text="Sistemas listos y cámara activa", text_color="green")
            else:
                self.model = None
                self.status_label.configure(text="IA no instalada. Usando Visión.", text_color="orange")
                self.radio_ia.configure(state="disabled")
        except Exception as e:
            self.model = None

        self.vid = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        self.delay = 15 # ms
        self.current_count = 0
        self.history_counts = []
        self.stable_count = 0
        
        self.update_frame()
            
    def update_frame(self):
        ret, frame = self.vid.read()
        
        if ret:
            mode = self.detection_mode.get()
            self.current_count = 0
            annotated_frame = frame.copy()

            if mode == "IA" and self.model:
                results = self.model.predict(source=frame, conf=0.15, verbose=False)
                detections = results[0].boxes
                self.current_count = len(detections)
                annotated_frame = results[0].plot()

            elif mode == "Contornos":
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (9, 9), 0)
                edged = cv2.Canny(blurred, 30, 150)
                edges = cv2.dilate(edged, None, iterations=4)
                edges = cv2.erode(edges, None, iterations=2)

                contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                min_area = self.sensitivity_slider.get()
                max_area = self.max_area_slider.get()
                
                for c in contours:
                    area = cv2.contourArea(c)
                    if min_area < area < max_area:
                        self.current_count += 1
                        x, y, w, h = cv2.boundingRect(c)
                        cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(annotated_frame, "Objeto", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            self.history_counts.append(self.current_count)
            if len(self.history_counts) > 15: 
                self.history_counts.pop(0)
            
            if self.history_counts:
                self.stable_count = max(set(self.history_counts), key=self.history_counts.count)

            self.counter_label.configure(text=f"Objetos en pantalla: {self.stable_count}")
            
            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(1024, 768))
            
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            
        self.after(self.delay, self.update_frame)

    def capture_and_validate(self):
        count = self.stable_count
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        
        status = ""
        
        if count == 0:
            status = "ERRÓNEO"
            messagebox.showerror(
                "Error de Inspección", 
                "No se han detectado objetos en la imagen.\nPor favor, sitúa los objetos en el área válida."
            )
        elif count > 5:
            status = "ERRÓNEO"
            messagebox.showerror(
                "LÍMITE EXCEDIDO", 
                f"Has excedido el límite.\nHay {count} objetos en pantalla y el máximo es 5."
            )
        else:
            status = "CORRECTO"
            messagebox.showinfo(
                "Inspección Correcta", 
                f"Validación superada correctamente.\nHas introducido {count} objetos, cantidad permitida."
            )

        # ----------------------------------------------------
        # Guardar en el buffer de resultados (Histórico)
        # ----------------------------------------------------
        self.capture_history.append({
            'id': self.current_capture_id,
            'time': now_str,
            'count': count,
            'status': status
        })
        self.current_capture_id += 1

    def show_results(self):
        # Abrimos la ventana que definimos arriba
        window = ResultsWindow(self, self.capture_history)
        # Que agarre el enfoque para que el usuario la vea rápido sobre el video
        window.grab_set()

    def close_manager(self):
        if self.vid.isOpened():
            self.vid.release()
        self.destroy()

if __name__ == "__main__":
    app = ObjectCounterApp()
    app.protocol("WM_DELETE_WINDOW", app.close_manager)
    app.mainloop()
