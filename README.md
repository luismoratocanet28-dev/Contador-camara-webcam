# Contador-camara-webcam

Este proyecto es una aplicación de escritorio desarrollada en Python que utiliza la cámara web para detectar y contar objetos en tiempo real. Combina técnicas de visión artificial clásica (mediante OpenCV) y detección basada en Inteligencia Artificial (usando YOLO) con una interfaz de usuario moderna creada con CustomTkinter.

## Características Principales

*   **Detección Dual:** 
    *   **Visión Clásica:** Utiliza detección de contornos para identificar objetos (ideal para piezas pequeñas como pastillas), con ajustes personalizables de tamaño mínimo y máximo para filtrar ruido de fondo o ignorar la base sobre la que se coloquen.
    *   **IA (YOLO):** Utiliza modelos de IA preentrenados (YOLOv8) para un reconocimiento general de objetos más avanzado.
*   **Validación de Inspecciones:** Verifica que la cantidad de objetos en pantalla se encuentre dentro del límite permitido (máximo 5 objetos por inspección). Muestra alertas de error si hay 0 objetos detectados o si se supera el límite.
*   **Panel de Resultados Históricos:** Almacena y clasifica el historial de las capturas realizadas en "Correctas" y "Erróneas", permitiendo llevar un control de calidad eficiente y resetear estadísticas fácilmente.
*   **Interfaz Moderna e Intuitiva:** Interfaz gráfica atractiva en modo oscuro y visualización del recuento estabilizado en tiempo real.

## Requisitos Previos

Para ejecutar este proyecto, necesitarás tener instalado Python en tu sistema y las siguientes librerías:

```bash
pip install opencv-python
pip install customtkinter
pip install Pillow
pip install ultralytics # Opcional, solo si quieres usar el modelo YOLO
```

## Instalación y Uso

1.  Clona este repositorio o descarga los archivos en tu ordenador.
2.  Asegúrate de tener una cámara web conectada y habilitada.
3.  Ejecuta el archivo principal:
    ```bash
    python gui_app.py
    ```

## Archivos del Proyecto

*   **`gui_app.py`**: El código fuente principal de la aplicación. Contiene toda la lógica de detección, captura de cámara, la interfaz gráfica y la gestión del historial de inspecciones.
*   **`Explicacion de la practica.pdf`**: Documento detallado con la explicación teórica y las pautas que se han seguido para realizar esta práctica.
