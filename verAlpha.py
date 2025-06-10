import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
import os

#region Funciones de Conversión de Imagen (Nivel de Bits y Píxeles)

def image_to_bit_array(image_path):
    """Convierte una imagen a un arreglo binario a nivel de bits (como en practica3.py)."""
    img = Image.open(image_path).convert("L")
    data = np.array(img)
    binary_array = np.unpackbits(data, axis=1)
    return binary_array, data.shape, data.shape[1] * 8

def bit_array_to_image(binary_array, shape, bits_per_row):
    """Convierte un arreglo binario a nivel de bits de vuelta a una imagen en escala de grises."""
    binary_array = binary_array[:, :bits_per_row]
    packed = np.packbits(binary_array, axis=1)
    trimmed = packed[:, :shape[1]]
    return Image.fromarray(trimmed.astype(np.uint8), mode='L')

def binary_to_pixel_array_copia(binary_img):
    """Convierte un arreglo binario a un arreglo de píxeles (como en copia_de_cifradoimgregla90r.py)."""
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

#endregion

#region Lógica de Autómatas Celulares (Codificación y Decodificación)

def _mirror_boundary(state):
    """Función auxiliar para aplicar fronteras espejo."""
    left = state[:, 1:2]
    right = state[:, -2:-1]
    return np.concatenate([left, state, right], axis=1)

# --- Método 1: Codificación/Decodificación compatible con 'practica3.py' ---
def encode_rule90R_practica3(binary_data, iterations):
    """Codifica con la lógica exacta de 'practica3.py', realizando (iterations-1) pasos."""
    if iterations < 2:
        raise ValueError("El número de iteraciones para este método debe ser >= 2.")

    history = [np.zeros_like(binary_data) for _ in range(iterations)]
    history[0] = binary_data.copy()

    # Paso 1 (no reversible por sí solo): t=1
    extended_t0 = _mirror_boundary(history[0])
    history[1] = extended_t0[:, :-2] ^ extended_t0[:, 2:]

    # Pasos reversibles: t=2 hasta t=iterations-1
    for t in range(2, iterations):
        extended_t_minus_1 = _mirror_boundary(history[t - 1])
        history[t] = np.bitwise_xor.reduce([history[t - 2], extended_t_minus_1[:, :-2], extended_t_minus_1[:, 2:]])

    return history[-1], history[-2]

def decode_rule90R_practica3(final_state, second_to_last_state, iterations):
    """Decodifica con la lógica inversa exacta de 'practica3.py'."""
    if iterations < 2:
        # Si la codificación usó N<2, la decodificación no es posible con esta regla.
        raise ValueError("El número de iteraciones para este método debe ser >= 2.")

    history = [np.zeros_like(final_state) for _ in range(iterations)]
    history[-1] = final_state
    history[-2] = second_to_last_state

    # Invierte los pasos desde el final hacia el principio
    # La fórmula inversa es: C(t-2) = C(t) XOR R90(C(t-1))
    for t in range(iterations - 1, 1, -1):
        extended_t_minus_1 = _mirror_boundary(history[t - 1])
        r90_of_t_minus_1 = extended_t_minus_1[:, :-2] ^ extended_t_minus_1[:, 2:]
        history[t - 2] = history[t] ^ r90_of_t_minus_1

    return history[0]

# --- Método 2: Decodificación del formato original de 'prueba2.py' ---
def decode_rule90_original_prueba2(data):
    return data["history"][0]

# --- Método 3: Decodificación del formato de 'copia_de_cifradoimgregla90r.py' ---
def decode_rule90R_copia(cifrada_bin, iterations):
    img = cifrada_bin.copy()
    filas, _ = img.shape

    def rule90R_inverse(t1, t2):
        n = len(t1)
        t0 = np.zeros(n, dtype=np.uint8)
        for i in range(n):
            left = t1[i - 1] if i > 0 else 0
            right = t1[i + 1] if i < n - 1 else 0
            future = t2[i]
            t0[i] = (left ^ right ^ future)
        return t0

    for i in range(0, filas - 1, 2):
        t2_final, t1_final = img[i+1], img[i]
        for _ in range(iterations):
            t0_recuperado = rule90R_inverse(t1_final, t2_final)
            t2_final, t1_final = t1_final, t0_recuperado
        img[i], img[i+1] = t1_final, t2_final
    return img

#endregion

#region Interfaz Gráfica de Usuario (GUI)
def visualize_images(images, titles):
    """Muestra una o más imágenes usando Matplotlib."""
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
        self.root.title("Codificador/Decodificador Universal Regla 90R")
        self.iterations = tk.IntVar(value=10)
        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        # Iterations UI
        iter_frame = ttk.Frame(frame)
        iter_frame.pack(fill='x', pady=5)
        ttk.Label(iter_frame, text="Número de iteraciones:").pack(side='left', padx=5)
        ttk.Entry(iter_frame, textvariable=self.iterations, width=10).pack(side='left', padx=5)
        ttk.Label(iter_frame, text="(Debe ser >= 2 para compatibilidad)", font=('Calibri', 8)).pack(side='left', padx=5)

        # Buttons UI
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)
        ttk.Button(btn_frame, text="Codificar Imagen (Emisor)", command=self.run_emisor).pack(side='left', expand=True, padx=5)
        ttk.Button(btn_frame, text="Decodificar Archivo (Receptor)", command=self.run_receptor).pack(side='left', expand=True, padx=5)

    def run_emisor(self):
        filepath = filedialog.askopenfilename(title="Selecciona la imagen a codificar", filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not filepath: return

        try:
            iterations = self.iterations.get()
            if iterations < 2:
                messagebox.showwarning("Advertencia", "El número de iteraciones debe ser 2 o mayor para ser compatible con los scripts originales.")
                return

            binary_array, shape, bits_per_row = image_to_bit_array(filepath)
            encoded, second_to_last = encode_rule90R_practica3(binary_array, iterations)

            base_save_path = filedialog.asksaveasfilename(title="Indica el nombre base para los archivos de salida", filetypes=[("Todos los archivos", "*.*")])
            if not base_save_path: return

            base_name, _ = os.path.splitext(base_save_path)
            path_npz = base_name + ".npz"
            np.savez(path_npz, cifrada=encoded, tN_minus_1=second_to_last, shape=shape, bits=bits_per_row)

            path_npy = base_name + ".npy"
            np.save(path_npy, encoded)

            original_img = Image.open(filepath)
            encoded_img = bit_array_to_image(encoded, shape, bits_per_row)

            visualize_images([original_img, encoded_img], ["Original", f"Codificada ({iterations} iter.)"])
            messagebox.showinfo(
                "Guardado Exitoso",
                "Se generaron dos archivos compatibles:\n\n"
                f"1. Para 'practica3.py' (.npz):\n{path_npz}\n\n"
                f"2. Para 'copia_de_... .py' (.npy):\n{path_npy}"
            )

        except Exception as e:
            messagebox.showerror("Error de Codificación", f"Ocurrió un error: {e}")

    def run_receptor(self):
        filepath = filedialog.askopenfilename(title="Selecciona el archivo a decodificar", filetypes=[("Archivos Soportados", "*.npz *.npy")])
        if not filepath: return

        try:
            iterations = self.iterations.get()
            decoded_image = None

            if filepath.endswith(".npz"):
                data = np.load(filepath)
                decoded_binary = decode_rule90R_practica3(data['cifrada'], data['tN_minus_1'], iterations)
                decoded_image = bit_array_to_image(decoded_binary, tuple(data['shape']), int(data['bits']))

            elif filepath.endswith(".npy"):
                try:
                    data = np.load(filepath, allow_pickle=True).item()
                    if isinstance(data, dict) and 'history' in data:
                        decoded_binary = decode_rule90_original_prueba2(data)
                        decoded_image = Image.fromarray((decoded_binary * 255).astype(np.uint8))
                    else: raise TypeError
                except Exception:
                    encoded_binary = np.load(filepath)
                    decoded_binary = decode_rule90R_copia(encoded_binary, iterations)
                    pixel_array = binary_to_pixel_array_copia(decoded_binary)
                    decoded_image = Image.fromarray(pixel_array)

            if decoded_image:
                visualize_images([decoded_image], [f"Decodificada ({os.path.basename(filepath)})"])
            else:
                messagebox.showerror("Error de Decodificación", "No se pudo determinar el formato del archivo o decodificarlo.")

        except Exception as e:
            messagebox.showerror("Error de Decodificación", f"Ocurrió un error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomataGUI(root)
    root.mainloop()