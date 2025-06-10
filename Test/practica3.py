import numpy as np
import os
from PIL import Image
import matplotlib.pyplot as plt

# Paso 1: Convertir imagen a binario y delimitar fronteras espejo
def imagen_a_binaria(imagen_path): #Convertimos a escala de grises en un arreglo
    imagen = Image.open(imagen_path).convert("L")
    datos = np.array(imagen)
    binaria = np.unpackbits(datos, axis=1) #Usamos unpackbits para convertir cada píxel a su equivalente en binario -8
    return binaria, datos.shape, datos.shape[1] * 8

def binaria_a_imagen(binaria, shape, bits_por_fila): #Queremos ahora de binaria a uan imagen en gris
    binaria = binaria[:, :bits_por_fila]
    empaquetado = np.packbits(binaria, axis=1)
    recortado = empaquetado[:, :shape[1]]
    return Image.fromarray(recortado.astype(np.uint8), mode='L')

def frontera_espejo(actual): #Delimitamos el problema para que no tengamos problemas de frontera
    izquierda = actual[:, 1:2]
    derecha = actual[:, -2:-1]
    extendido = np.concatenate([izquierda, actual, derecha], axis=1)
    return extendido

# Regla 90R
def regla_90R(binaria, iteraciones):
    historia = [np.zeros_like(binaria) for _ in range(iteraciones)] #Se busca almacenar cada generación en el tiempo
    historia[0] = binaria.copy()

    extendido = frontera_espejo(historia[0]) #Guardamos el t=0
    historia[1] = extendido[:, :-2] ^ extendido[:, 2:] #Calculamos t=1 con Ci(t+1)=Ci-1(t)+Ci+1(t)

    for t in range(2, iteraciones): #Ahora empleamos Regla 90 reversible
        extendido = frontera_espejo(historia[t - 1])
        historia[t] = np.bitwise_xor.reduce([ #Recordando que XOR es equivalente a la suma módulo 2
            extendido[:, :-2], extendido[:, 2:], historia[t - 2]
        ])

    return historia[-1], historia[-2], historia[0]

# Desencriptado
def desencriptar_regla90R(binaria_final, binaria_t_menos1, iteraciones): #Creamos una lista de generaciones para colocar ultimo y penultimo estado para regla inversa
    historia = [np.zeros_like(binaria_final) for _ in range(iteraciones)]
    historia[-1] = binaria_final
    historia[-2] = binaria_t_menos1

    for t in range(iteraciones - 3, -1, -1):
        extendido = frontera_espejo(historia[t + 1])
        historia[t] = np.bitwise_xor.reduce([
            extendido[:, :-2], extendido[:, 2:], historia[t + 2]
        ])

    return historia[0]


def modo_emisor():
    ruta = input("Ruta de la imagen (formato PNG/JPG): ").strip().strip('"')
    iteraciones = int(input("Número de iteraciones para cifrado: "))

    binaria, shape, bits_por_fila = imagen_a_binaria(ruta)
    cifrada, tN_minus_1, t0 = regla_90R(binaria, iteraciones)

    np.savez("salida_emisor.npz", cifrada=cifrada, tN_minus_1=tN_minus_1, t0=t0, shape=shape, bits=bits_por_fila)
    print("Imagen cifrada correctamente. Archivo 'salida_emisor.npz' generado.")

    imagen_cifrada = binaria_a_imagen(cifrada, shape, bits_por_fila)
    imagen_cifrada.save("imagen_cifrada.png")
    imagen_cifrada.show()
    print("Imagen cifrada guardada como 'imagen_cifrada.png'")

def modo_receptor():
    nombre = input("Ingresa el nombre del archivo .npz: ").strip()
    iteraciones = int(input("Número de iteraciones utilizadas en el cifrado: "))

    datos = np.load(nombre)
    cifrada = datos['cifrada']
    tN_minus_1 = datos['tN_minus_1']
    shape = tuple(datos['shape'])
    bits_por_fila = int(datos['bits'])

    recuperada = desencriptar_regla90R(cifrada, tN_minus_1, iteraciones)
    imagen = binaria_a_imagen(recuperada, shape, bits_por_fila)
    imagen.save("imagen_recuperada.png")
    imagen.show()
    print("Imagen recuperada y guardada como 'imagen_recuperada.png'")

# MAIN
if __name__ == '__main__':
    print("Seleccione el modo de operación:")
    print("1. Equipo Emisor (Encriptar)")
    print("2. Equipo Receptor (Desencriptar)")
    opcion = input("Opción: ").strip()

    if opcion == '1':
        modo_emisor()
    elif opcion == '2':
        modo_receptor()
    else:
        print("Opción no válida. Intenta nuevamente.")
