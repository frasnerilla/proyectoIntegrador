# -------------------------------
# IMPORTACIONES
# -------------------------------

from flask import Flask, request, jsonify, render_template
# Flask --> crea el servidor web
# request --> recibe datos del cliente (audio)
# jsonify --> devuelve respuestas en formato JSON
# render_template --> va a la carpeta templates, buscae el index, lo convierte en respuesta http y lo manda al navegador
import re  # Para usar expresiones regulares (extraer datos del texto)
import pickle  # Para cargar el modelo entrenado guardado en .pkl
from pathlib import Path  # Para trabajar con rutas y archivos
import pandas as pd  # Para crear el DataFrame que usa el modelo
import os

# Importamos funciones del archivo de Deepgram
from transcribir_deepgram import transcribir_audio, limpiar_texto, convertir_numeros


# -------------------------------
# CREAR APLICACIÓN FLASK
# -------------------------------

app = Flask(__name__)


# -------------------------------
# CARGAR MODELO UNA SOLA VEZ
# -------------------------------

# Abrimos el modelo entrenado en modo lectura binaria
with open("modelo_abandono.pkl", "rb") as f:
    modelo = pickle.load(f)
# Así el modelo se carga una vez al iniciar el servidor


# -------------------------------
# FUNCIÓN PARA EXTRAER DATOS CON REGEX
# -------------------------------

def extraer(patron, texto, tipo=float, default=0):
    # Busca el patrón en el texto, el patrón en este caso es:  "edad (\d+)", entre otros
    match = re.search(patron, texto) #Con regex el llamarle match a una coincidencia es una buena práctica
    # Si lo encuentra, devuelve el grupo  convertido al tipo indicado
    # Si no lo encuentra, devuelve el valor por defecto
    return tipo(match.group(1)) if match else default


# -------------------------------
# FUNCIÓN PRINCIPAL DE PREDICCIÓN
# -------------------------------

def predecir_desde_texto(texto: str):

    # Pasamos todo a minúsculas por si puede haber algo que se escapa
    texto = texto.lower()

    # Extraemos los valores numéricos mediante la función anterior
    edad = extraer(r"edad (\d+)", texto, int)
    faltas = extraer(r"faltas (\d+)", texto, int)
    nota = extraer(r"nota (\d+\.?\d*)", texto, float)
    horas = extraer(r"horas (\d+)", texto, int)

    # Convertimos si/no a 1/0
    repite = 1 if "repite si" in texto else 0
    trabaja = 1 if "trabaja si" in texto else 0

    # Motivación la convertimos a valor numérico
    if "motivacion alta" in texto:
        motivacion = 2
        motivacion_txt = "alta"
    elif "motivacion media" in texto:
        motivacion = 1
        motivacion_txt = "media"
    else:
        motivacion = 0
        motivacion_txt = "baja"

    # Creamos un DataFrame con el mismo orden de columnas que el del entrenamiento
    datos = pd.DataFrame([{
        "edad": edad,
        "faltas": faltas,
        "nota_media": nota,
        "repite": repite,
        "trabaja": trabaja,
        "horas_estudio": horas,
        "motivacion": motivacion
    }])

    # Hacemos la predicción
    pred_num = float(modelo.predict(datos)[0])

    # Convertimos el número continuo a clasificación binaria, al ser linearRegresion es obligatorio
    pred_txt = "alta" if pred_num >= 0.5 else "baja"

    # Devolvemos todos los datos en formato diccionario
    return {
        "texto": texto,
        "edad": edad,
        "faltas": faltas,
        "nota": nota,
        "repite": "si" if repite else "no",
        "trabaja": "si" if trabaja else "no",
        "horas": horas,
        "motivacion": motivacion_txt,
        "prediccion": pred_txt,
    }


# -------------------------------
# ENDPOINT API PARA RECIBIR AUDIO
# -------------------------------

@app.post("/api/predict")
def predict():

    # Comprobamos que se haya enviado un archivo
    if "audio" not in request.files:
        return jsonify({"error": "No se recibió el audio"}), 400

    file = request.files["audio"]

    # Si el nombre está vacío
    if file.filename == "":
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    # Creamos carpeta temporal si no existe
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)

    # Guardamos el audio temporalmente
    audio_path = tmp_dir / file.filename
    file.save(audio_path)

    try:
        # 1. Transcribimos el audio
        texto = transcribir_audio(str(audio_path))

        # 2. Limpiamos el texto
        texto = limpiar_texto(texto)

        # 3. Convertimos números escritos en palabras
        texto = convertir_numeros(texto)

        # 4. Hacemos la predicción
        resultado = predecir_desde_texto(texto)

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Eliminamos el archivo temporal
        try:
            audio_path.unlink(missing_ok=True)
        except:
            pass


# -------------------------------
# RUTAS PARA SERVIR EL FRONTEND
# -------------------------------

@app.get("/")
def home():
    return render_template("index.html")



# -------------------------------
# INICIAR SERVIDOR
# -------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
