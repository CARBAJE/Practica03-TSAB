import numpy as np
from PIL import Image


def get_image_data(path):
    img = Image.open(path).convert('L')
    data = np.array(img)
    bits = np.unpackbits(data.astype(np.uint8), axis=1)

    return bits


def show_image(bits, title="Imagen", save_path=None):
    img_data = np.packbits(bits, axis=1).astype(np.uint8)
    img = Image.fromarray(img_data, mode='L')
    img.show(title=title)

    if save_path is not None:
        img.save(save_path)
        print("Imagen guardada en:", save_path)


def encode_rule_90R(bits, iterations):
    rows = bits.shape[0]
    cols = bits.shape[1]
    bits = bits.copy()

    for _ in range(iterations):
        new_bits = bits.copy()

        for i in range(1, rows, 2):
            for j in range(0, cols):
                left = bits[i, j - 1] if j > 0 else 0
                past_center = bits[i - 1, j]
                right = bits[i, j + 1] if j < cols - 1 else 0
                new_bits[i - 1, j] = bits[i, j]
                new_bits[i, j] = (left + past_center + right) % 2

        bits = new_bits

    return bits


def decode_rule_90R(bits, iterations):
    rows = bits.shape[0]
    cols = bits.shape[1]
    bits = bits.copy()

    for _ in range(iterations):
        new_bits = bits.copy()

        for i in range(0, rows - 1, 2):
            for j in range(0, cols):
                left = bits[i, j - 1] if j > 0 else 0
                past_center = bits[i + 1, j]
                right = bits[i, j + 1] if j < cols - 1 else 0
                new_bits[i, j] = (left + past_center + right) % 2
                new_bits[i + 1, j] = bits[i, j]

        bits = new_bits

    return bits


def encode_rule_90R_fast(bits, iterations):
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


def decode_rule_90R_fast(bits, iterations):
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


def emisor():
    img_path = input("Ingrese la ruta de la imagen: ").strip().strip('"')
    iteraciones = int(input("Ingrese el número de iteraciones: "))
    bits = get_image_data(img_path)
    show_image(bits, title="Imagen Original")

    encoded_bits = encode_rule_90R_fast(bits, iteraciones)
    show_image(
        encoded_bits, title="Imagen Codificada",
        save_path="imagen_codificada.png"
    )

    np.save("encoded.npy", encoded_bits)


def receptor():
    encoded_bits_path = input(
        "Ingrese la ruta del archivo de bits codificados (.npy): "
    ).strip().strip('"')
    iteraciones = int(input("Ingrese el número de iteraciones: "))
    encoded_bits = np.load(encoded_bits_path)
    decoded_bits = decode_rule_90R_fast(encoded_bits, iteraciones)
    show_image(
        decoded_bits, title="Imagen Decodificada",
        save_path="imagen_decodificada.png"
    )


def main():
    print("Seleccione el modo:")
    print("1. Emisor")
    print("2. Receptor")
    choice = input("-> ").strip()

    if choice == '1':
        emisor()
    elif choice == '2':
        receptor()
    else:
        print("Opción no válida.")


if __name__ == "__main__":
    main()
