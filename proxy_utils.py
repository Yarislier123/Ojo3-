import random

def obtener_proxy(path="proxies.txt"):
    """
    Lee proxies desde un archivo de texto (uno por línea) y devuelve
    una cadena aleatoria o None si el archivo no existe o está vacío.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            lineas = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#")]
        return random.choice(lineas) if lineas else None
    except FileNotFoundError:
        return None
