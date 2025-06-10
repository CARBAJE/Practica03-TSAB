import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
import os


def image_to_binary_array(image_path):
    img = Image.open(image_path).convert("L")
    img = img.resize((128, 128))
    data = np.array(img)
    binary = (data > 127).astype(np.uint8)
    return binary, img


def binary_array_to_image(binary_array):
    return Image.fromarray((binary_array * 255).astype(np.uint8))


# MÉTODOS DEL EQUIPO ORIGINAL (TU CÓDIGO)
def rule90_reversible_encode(data, steps):
    history = [data.copy()]
    current = data.copy()
    for _ in range(steps):
        left = np.roll(current, 1, axis=1)
        right = np.roll(current, -1, axis=1)
        next_gen = np.bitwise_xor(left, right)
        history.append(current.copy())
        current = next_gen
    return current, history


def rule90_reversible_decode(encoded, history):
    current = encoded.copy()
    for past in reversed(history[:-1]):
        left = np.roll(current, 1, axis=1)
        right = np.roll(current, -1, axis=1)
        prev = np.bitwise_xor(left, right)
        current = past
    return current


# MÉTODOS DEL OTRO EQUIPO (REGLA 90R)
def regla_90R(t0, t1):
    """Regla 90R del otro equipo"""
    n = len(t0)
    t2 = np.zeros(n, dtype=np.uint8)
    for i in range(n):
        left = t1[i - 1] if i - 1 >= 0 else 0
        right = t1[i + 1] if i + 1 < n else 0
        center = t0[i]
        t2[i] = (left + right + center) % 2
    return t2


def regla_90R_inversa(t1, t2):
    """Regla 90R inversa del otro equipo"""
    n = len(t1)
    t0 = np.zeros(n, dtype=np.uint8)
    for i in range(n):
        left = t1[i - 1] if i - 1 >= 0 else 0
        right = t1[i + 1] if i + 1 < n else 0
        future = t2[i]
        t0[i] = (left + right + future) % 2
    return t0


def convert_rows_to_binary(img):
    """Convierte imagen a representación binaria bit por bit"""
    rows = img.shape[0]
    binary_rows = []

    for r in range(rows):
        bin_str_row = ''.join(format(pixel, '08b') for pixel in img[r])
        bin_list = [int(bit) for bit in bin_str_row]
        binary_rows.append(bin_list)

    return np.array(binary_rows, dtype=np.uint8)


def binary_to_pixel_array(binary_img):
    """Convierte representación binaria de vuelta a pixeles"""
    rows, total_bits = binary_img.shape
    num_pixels_per_row = total_bits // 8

    pixel_rows = []
    for r in range(rows):
        row_bits = binary_img[r]
        pixels = []
        for i in range(num_pixels_per_row):
            byte_bits = row_bits[i*8:(i+1)*8]
            byte_str = ''.join(str(b) for b in byte_bits)
            pixel_val = int(byte_str, 2)
            pixels.append(pixel_val)
        pixel_rows.append(pixels)

    return np.array(pixel_rows, dtype=np.uint8)


def descifrar_con_regla90R(img_cifrada, num_iteraciones):
    """Descifra usando el método del otro equipo"""
    img = img_cifrada.copy()
    filas, cols = img.shape

    for i in range(0, filas - 1, 2):
        if i + 1 < filas:  # Verificar que hay par de filas
            t2 = img[i+1]
            t1 = img[i]

            for _ in range(num_iteraciones):
                t0 = regla_90R_inversa(t1, t2)
                t2, t1 = t1, t0

            img[i] = t1
            img[i+1] = t2

    return img


def rule90_decode_without_history(encoded, steps):
    """Decodificación sin historial para tu método"""
    current = encoded.copy()
    for _ in range(steps):
        left = np.roll(current, 1, axis=1)
        right = np.roll(current, -1, axis=1)
        current = np.bitwise_xor(left, right)
    return current


def detect_file_format(data):
    """Detecta el formato del archivo y el método de cifrado usado"""
    try:
        # Verificar si es un array 2D con dimensiones típicas de imagen binaria expandida
        if len(data.shape) == 2:
            rows, cols = data.shape

            # Si el número de columnas es múltiplo de 8 y mayor que las filas,
            # probablemente es del otro equipo (cada pixel -> 8 bits)
            if cols % 8 == 0 and cols > rows * 4:
                return 'otro_equipo_binario'

            # Si es cuadrada o rectangular normal, probablemente es tu método
            elif 64 <= rows <= 256 and 64 <= cols <= 256:
                return 'metodo_original'

            # Si es muy diferente, podría ser imagen directa
            else:
                return 'imagen_directa'

        return 'desconocido'

    except:
        return 'desconocido'


def load_npy_file(file_path):
    """Función robusta para cargar archivos .npy con diferentes estructuras"""
    try:
        data = np.load(file_path, allow_pickle=True)

        # Caso 1: Diccionario con 'encoded' e 'history' (tu formato)
        if isinstance(data, np.ndarray) and data.dtype == object:
            try:
                data_dict = data.item()
                if isinstance(data_dict, dict) and 'encoded' in data_dict:
                    return {
                        'type': 'with_history',
                        'method': 'metodo_original',
                        'encoded': data_dict['encoded'],
                        'history': data_dict.get('history', [])
                    }
            except (ValueError, AttributeError):
                pass

        # Caso 2: Array numpy directo
        if isinstance(data, np.ndarray) and data.dtype != object:
            format_type = detect_file_format(data)

            return {
                'type': 'array_only',
                'method': format_type,
                'encoded': data,
                'history': []
            }

        # Caso 3: Otros formatos de diccionario
        try:
            if hasattr(data, 'item'):
                item_data = data.item()
                if isinstance(item_data, dict):
                    # Buscar claves comunes
                    encoded_key = None
                    for key in ['encoded', 'data', 'array', 'image', 'binary']:
                        if key in item_data:
                            encoded_key = key
                            break

                    if encoded_key:
                        encoded_data = item_data[encoded_key]
                        format_type = detect_file_format(encoded_data)

                        return {
                            'type': 'dict_format',
                            'method': format_type,
                            'encoded': encoded_data,
                            'history': item_data.get('history', [])
                        }
        except:
            pass

        raise ValueError("Formato de archivo no reconocido")

    except Exception as e:
        raise ValueError(f"Error al cargar el archivo: {str(e)}")


def visualize_images(images, titles):
    n = len(images)
    fig, axs = plt.subplots(1, n, figsize=(4 * n, 4))
    if n == 1:
        axs = [axs]
    for i in range(n):
        axs[i].imshow(images[i], cmap='gray')
        axs[i].set_title(titles[i])
        axs[i].axis('off')
    plt.tight_layout()
    plt.show()


class AutomataGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Codificador/Decodificador Regla 90R - Compatible con ambos métodos")

        self.binary = None
        self.original_img = None
        self.iterations = tk.IntVar(value=10)
        self.mode = tk.StringVar(value="emisor")
        self.history = []

        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Número de iteraciones:").grid(column=0, row=0, sticky='w')
        ttk.Entry(frame, textvariable=self.iterations, width=10).grid(column=1, row=0, sticky='w')

        ttk.Label(frame, text="Modo:").grid(column=0, row=1, sticky='w')
        ttk.Radiobutton(frame, text="Emisor", variable=self.mode, value="emisor").grid(column=1, row=1, sticky='w')
        ttk.Radiobutton(frame, text="Receptor", variable=self.mode, value="receptor").grid(column=2, row=1, sticky='w')

        ttk.Button(frame, text="Ejecutar", command=self.run_mode).grid(column=0, row=2, columnspan=3, pady=10)

        # Información de debug
        self.info_label = ttk.Label(frame, text="", foreground="blue")
        self.info_label.grid(column=0, row=3, columnspan=3, pady=5)

    def run_mode(self):
        if self.mode.get() == "emisor":
            self.run_emisor()
        elif self.mode.get() == "receptor":
            self.run_receptor()

    def run_emisor(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return

        self.binary, self.original_img = image_to_binary_array(filepath)
        encoded, self.history = rule90_reversible_encode(self.binary, self.iterations.get())

        encoded_path = filedialog.asksaveasfilename(defaultextension=".npy", filetypes=[("Archivo NPY", "*.npy")])
        if not encoded_path:
            return

        np.save(encoded_path, {"encoded": encoded, "history": self.history})
        visualize_images([binary_array_to_image(self.binary),
                          binary_array_to_image(encoded)],
                         ["Original", "Codificada"])
        messagebox.showinfo("Guardado", f"Archivo cifrado guardado en:\n{encoded_path}")

    def run_receptor(self):
        filepaths = filedialog.askopenfilenames(filetypes=[("Archivo NPY", "*.npy")])
        if not filepaths:
            return

        decoded_images = []
        success_count = 0
        error_count = 0

        for i, path in enumerate(filepaths):
            try:
                # Cargar el archivo
                file_data = load_npy_file(path)

                encoded = file_data['encoded']
                history = file_data['history']
                file_type = file_data['type']
                method = file_data['method']

                self.info_label.config(text=f"Procesando archivo {i+1}: {method}, Shape: {encoded.shape}")
                self.root.update()

                decoded = None

                # Decodificar según el método detectado
                if method == 'otro_equipo_binario':
                    # Método del otro equipo
                    print(f"Archivo {i+1}: Detectado como método del otro equipo")

                    # Aplicar decodificación con regla 90R inversa
                    decoded_binary = descifrar_con_regla90R(encoded, self.iterations.get())

                    # Convertir de binario a imagen
                    decoded = binary_to_pixel_array(decoded_binary)

                elif method == 'metodo_original' or file_type == 'with_history':
                    # Tu método original
                    print(f"Archivo {i+1}: Detectado como método original")

                    if file_type == 'with_history' and len(history) > 0:
                        decoded = rule90_reversible_decode(encoded, history)
                    else:
                        decoded = rule90_decode_without_history(encoded, self.iterations.get())

                elif method == 'imagen_directa':
                    # Tratar como imagen directa
                    print(f"Archivo {i+1}: Tratado como imagen directa")
                    decoded = encoded

                else:
                    # Intentar ambos métodos
                    print(f"Archivo {i+1}: Método desconocido, probando ambos")

                    try:
                        # Primero intentar método original
                        decoded = rule90_decode_without_history(encoded, self.iterations.get())
                    except:
                        try:
                            # Luego intentar método del otro equipo
                            decoded_binary = descifrar_con_regla90R(encoded, self.iterations.get())
                            decoded = binary_to_pixel_array(decoded_binary)
                        except:
                            # Como último recurso, mostrar tal como está
                            decoded = encoded

                if decoded is not None:
                    # Convertir a imagen si es necesario
                    if len(decoded.shape) == 2 and decoded.dtype == np.uint8:
                        decoded_images.append(Image.fromarray(decoded, mode='L'))
                    else:
                        decoded_images.append(binary_array_to_image(decoded))

                    success_count += 1
                    print(f"Archivo {i+1}: Procesado exitosamente")

            except Exception as e:
                error_count += 1
                print(f"Error al procesar archivo {i+1} ({os.path.basename(path)}): {str(e)}")

                # Último intento: mostrar raw data
                try:
                    raw_data = np.load(path, allow_pickle=True)
                    if isinstance(raw_data, np.ndarray) and len(raw_data.shape) == 2:
                        decoded_images.append(Image.fromarray(raw_data.astype(np.uint8), mode='L'))
                        success_count += 1
                        print(f"Archivo {i+1}: Mostrado como raw data")
                    else:
                        messagebox.showerror("Error", f"No se pudo procesar:\n{os.path.basename(path)}\nError: {str(e)}")
                except:
                    messagebox.showerror("Error", f"Error crítico con:\n{os.path.basename(path)}\nError: {str(e)}")

        if decoded_images:
            # Convertir PIL Images a arrays para visualización
            image_arrays = []
            for img in decoded_images:
                if isinstance(img, Image.Image):
                    image_arrays.append(np.array(img))
                else:
                    image_arrays.append(img)

            visualize_images(image_arrays, [f"Decodificada {i+1}" for i in range(len(image_arrays))])

        # Mostrar resumen
        total_files = len(filepaths)
        self.info_label.config(text=f"Procesamiento completo: {success_count}/{total_files} archivos exitosos")

        if success_count > 0:
            messagebox.showinfo("Completado", f"Se procesaron exitosamente {success_count} de {total_files} archivos")
        else:
            messagebox.showwarning("Sin resultados", "No se pudo procesar ningún archivo exitosamente")


if __name__ == "__main__":
    root = tk.Tk()
    app = AutomataGUI(root)
    root.mainloop()