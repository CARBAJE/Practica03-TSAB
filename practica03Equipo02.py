import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
import os

#region Funciones de Conversión de Imagen

def image_to_bit_array(image_path):
    """Convierte una imagen en escala de grises a un arreglo de bits."""
    img = Image.open(image_path).convert("L")
    data = np.array(img)
    # Desempaqueta cada byte de píxel en 8 bits
    binary_array = np.unpackbits(data, axis=1)
    # Retorna el arreglo de bits y metadatos para la reconstrucción
    return binary_array, data.shape, data.shape[1] * 8

def bit_array_to_image(binary_array, shape, bits_per_row):
    """Convierte un arreglo de bits de vuelta a una imagen en escala de grises."""
    # Asegura que el arreglo de bits tenga el número correcto de columnas
    binary_array = binary_array[:, :bits_per_row]
    # Empaqueta los bits de vuelta en bytes
    packed = np.packbits(binary_array, axis=1)
    # Recorta cualquier padding que se haya añadido durante el empaquetado
    trimmed = packed[:, :shape[1]]
    return Image.fromarray(trimmed.astype(np.uint8), mode='L')

#endregion

#region Lógica del Autómata Celular (Regla 90R)

def encode_rule_90R(bits, iterations):
    """
    Codifica un arreglo de bits usando una variante de la Regla 90,
    idéntico a la implementación de 'practica3_kevin.py'.
    """
    bits = bits.copy()
    rows, _ = bits.shape

    for _ in range(iterations):
        new_bits = bits.copy()
        i_idx = np.arange(1, rows, 2)

        left = np.zeros_like(bits)
        right = np.zeros_like(bits)
        left[:, 1:] = bits[:, :-1]
        right[:, :-1] = bits[:, 1:]

        new_bits[i_idx, :] = (left[i_idx, :] +
                              bits[i_idx - 1, :] +
                              right[i_idx, :]) % 2
        new_bits[i_idx - 1, :] = bits[i_idx, :]

        bits = new_bits

    return bits


def decode_rule_90R(bits, iterations):
    """
    Decodifica un arreglo de bits codificado con 'encode_rule_90R',
    idéntico a la implementación de 'practica3_kevin.py'.
    """
    bits = bits.copy()
    rows, _ = bits.shape

    for _ in range(iterations):
        new_bits = bits.copy()
        i_idx = np.arange(0, rows - 1, 2)

        left = np.zeros_like(bits)
        right = np.zeros_like(bits)
        left[:, 1:] = bits[:, :-1]
        right[:, :-1] = bits[:, 1:]

        new_bits[i_idx, :] = (left[i_idx, :] +
                              bits[i_idx + 1, :] +
                              right[i_idx, :]) % 2
        new_bits[i_idx + 1, :] = bits[i_idx, :]

        bits = new_bits

    return bits


#region Interfaz Gráfica de Usuario (GUI)

def visualize_images(images, titles):
    """Muestra una o más imágenes usando Matplotlib."""
    n = len(images)
    fig, axs = plt.subplots(1, n, figsize=(5 * n, 5))
    if n == 1:
        axs = [axs]
    for i in range(n):
        axs[i].imshow(images[i], cmap='gray', vmin=0, vmax=255)
        axs[i].set_title(titles[i])
        axs[i].axis('off')
    plt.tight_layout()
    plt.show()

class AutomataGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Codificador/Decodificador de Imágenes - Regla 90R")
        self.iterations = tk.IntVar(value=10)
        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding=15)
        frame.pack(fill="both", expand=True)

        # UI para las iteraciones
        iter_frame = ttk.Frame(frame)
        iter_frame.pack(fill='x', pady=5)
        ttk.Label(iter_frame, text="Número de iteraciones:").pack(side='left', padx=5)
        ttk.Entry(iter_frame, textvariable=self.iterations, width=10).pack(side='left', padx=5)

        # UI para los botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=15)
        ttk.Button(btn_frame, text="Codificar Imagen (Emisor)", command=self.run_emisor).pack(side='left', expand=True, padx=10, ipady=5)
        ttk.Button(btn_frame, text="Decodificar Archivo (Receptor)", command=self.run_receptor).pack(side='left', expand=True, padx=10, ipady=5)

    def run_emisor(self):
        filepath = filedialog.askopenfilename(title="Selecciona la imagen a codificar", filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not filepath: return

        try:
            iterations = self.iterations.get()
            binary_array, shape, bits_per_row = image_to_bit_array(filepath)

            # Codificar los datos de la imagen
            encoded_bits = encode_rule_90R(binary_array, iterations)

            # Guardar el resultado en un archivo .npy
            save_path = filedialog.asksaveasfilename(
                title="Guardar archivo codificado",
                defaultextension=".npy",
                filetypes=[("NumPy file", "*.npy")]
            )
            if not save_path: return

            # Guardar los datos codificados y los metadatos necesarios en un diccionario
            data_to_save = encoded_bits
            np.save(save_path, data_to_save)

            # Visualizar las imágenes original y codificada
            original_img = Image.open(filepath)
            encoded_img = bit_array_to_image(encoded_bits, shape, bits_per_row)
            visualize_images([original_img, encoded_img], ["Original", f"Codificada ({iterations} iter.)"])

            messagebox.showinfo("Guardado Exitoso", f"El archivo codificado se ha guardado en:\n{save_path}")

        except Exception as e:
            messagebox.showerror("Error de Codificación", f"Ocurrió un error: {e}")

    def run_receptor(self):
        filepath = filedialog.askopenfilename(title="Selecciona el archivo .npy a decodificar", filetypes=[("NumPy file", "*.npy")])
        if not filepath: return

        try:
            iterations = self.iterations.get()

            # Cargar el diccionario desde el archivo .npy
            data_dict = np.load(filepath)
            # print("llegue aqui")
            encoded_bits = data_dict
            original_shape = list(data_dict.shape)
            bits_per_row = original_shape[1]

            # Decodificar los bits
            decoded_binary = decode_rule_90R(encoded_bits, iterations)
            # Reconstruir la imagen a partir de los bits decodificados
            decoded_image = bit_array_to_image(decoded_binary, original_shape, bits_per_row)

            if decoded_image:
                visualize_images([decoded_image], [f"Imagen Decodificada ({os.path.basename(filepath)})"])
            else:
                messagebox.showerror("Error", "No se pudo decodificar la imagen.")

        except Exception as e:
            messagebox.showerror("Error de Decodificación", f"Ocurrió un error: {e}\nAsegúrate de que el número de iteraciones sea el mismo que en la codificación.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomataGUI(root)
    root.mainloop()