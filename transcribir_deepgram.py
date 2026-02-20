# -------------------------------
# IMPORTACIONES
# -------------------------------

import os          # Para leer la API Key desde el archivo .env
import re          # Para limpiar el texto usando expresiones regulares
import sys         # Para pasar el nombre del audio por consola
from pathlib import Path  # Para trabajar con rutas y archivos

import requests    # Para hacer la petición HTTP a Deepgram
from dotenv import load_dotenv  # Para cargar variables del archivo .env
from word2number_es import w2n  # Para convertir palabras como "veinte" a 20


# -------------------------------
# CONFIGURACIÓN
# -------------------------------

# Cargamos las variables del archivo .env
load_dotenv()

# Guardamos la API Key de Deepgram
API_KEY = os.getenv("DEEPGRAM_API_KEY")

# URL oficial de Deepgram para enviar el audio
DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"


# -------------------------------
# LIMPIAR TEXTO
# -------------------------------

def limpiar_texto(texto: str) -> str:
    # Pasamos todo a minúsculas para evitar problemas de coincidencia
    texto = texto.lower()

    # Quitamos tildes manualmente
    texto = (texto.replace("á", "a")
                  .replace("é", "e")
                  .replace("í", "i")
                  .replace("ó", "o")
                  .replace("ú", "u"))

    # Eliminamos signos de puntuación básicos
    texto = re.sub(r"[.,;:]", " ", texto) #sub = substitute(patron,reeplazo,de donde)

    # Quitamos espacios duplicados
    texto = re.sub(r"\s+", " ", texto) #\s(1o+ espacios en blanco),

    return texto.strip() #Devuelve el texto quitandole los espacios del principio y del final


# -------------------------------
# CONVERTIR PALABRAS A NÚMEROS
# -------------------------------

def convertir_numeros(texto: str) -> str:
    # Separamos el texto palabra por palabra
    palabras = texto.split()
    resultado = []

    for palabra in palabras: #Para cada palabra que hay en "el texto"
        try:
            # Intentamos convertir la palabra a número
            numero = w2n.word_to_num(palabra)
            resultado.append(str(numero))
        except:
            # Si no es un número escrito, la dejamos igual
            resultado.append(palabra)

    return " ".join(resultado)


# -------------------------------
# DETECTAR TIPO DE AUDIO
# -------------------------------

def content_type_por_extension(audio_path: Path) -> str:
    # Miramos la extensión del archivo
    ext = audio_path.suffix.lower()

    if ext == ".wav":
        return "audio/wav"
    if ext == ".mp3":
        return "audio/mpeg"
    if ext == ".m4a":
        return "audio/mp4"

    # Si no es uno de esos formatos, lanzamos error
    raise ValueError("Formato no soportado. Usa .wav, .mp3 o .m4a")


# -------------------------------
# TRANSCRIBIR AUDIO CON DEEPGRAM
# -------------------------------

def transcribir_audio(ruta_audio: str) -> str:

    # Comprobamos que exista la API Key
    if not API_KEY:
        raise ValueError("No se encontró la API Key de Deepgram")

    audio_path = Path(ruta_audio)

    # Comprobamos que el archivo exista
    if not audio_path.exists():
        raise FileNotFoundError(f"No existe el archivo {audio_path}")

    # Cabeceras que exige la API
    headers = {
        "Authorization": f"Token {API_KEY}",
        "Content-Type": content_type_por_extension(audio_path),
    }

    # Parámetros de configuración del modelo
    params = {
        "model": "nova-3",
        "language": "es",
        "smart_format": "true",
    }

    # Enviamos el audio a Deepgram
    response = requests.post(
        DEEPGRAM_URL,
        headers=headers,
        params=params,
        data=audio_path.read_bytes(),
        timeout=60,
    )

    # Si la respuesta no es correcta, mostramos el error
    if response.status_code != 200:
        raise RuntimeError(f"Error HTTP {response.status_code}\n{response.text}")

    data = response.json()

    try:
        # Extraemos el texto transcrito del JSON
        return data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
    except:
        raise RuntimeError(f"No se pudo leer la transcripción\n{data}")


# -------------------------------
# MAIN
# -------------------------------

def main():

    # Comprobamos que el usuario haya pasado el audio por consola
    if len(sys.argv) != 2:
        print("Uso: python transcribir_deepgram.py audio.wav")
        sys.exit(1)

    try:
        # 1. Transcribimos el audio
        texto = transcribir_audio(sys.argv[1])

        # 2. Limpiamos el texto
        texto = limpiar_texto(texto)

        # 3. Convertimos palabras numéricas a números
        texto = convertir_numeros(texto)

        print("\nTexto procesado:\n")
        print(texto if texto else "No se detectó voz")

        # Guardamos el resultado en un archivo para usarlo después
        Path("transcripcion.txt").write_text(texto, encoding="utf-8")
        print("\nGuardado en transcripcion.txt")

    except Exception as e:
        print("Error:", e)
        sys.exit(2)


# Ejecuta el main solo si el archivo se ejecuta directamente
if __name__ == "__main__":
    main()
