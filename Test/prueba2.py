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
        self.root.title("Codificador/Decodificador Regla 90R")

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
        for path in filepaths:
            data = np.load(path, allow_pickle=True).item()
            decoded = rule90_reversible_decode(data["encoded"], data["history"])
            decoded_images.append(binary_array_to_image(decoded))

        visualize_images(decoded_images, [f"Decodificada {i+1}" for i in range(len(decoded_images))])


if __name__ == "__main__":
    root = tk.Tk()
    app = AutomataGUI(root)
    root.mainloop()
