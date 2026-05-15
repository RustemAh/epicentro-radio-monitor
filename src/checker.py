import json, requests, time, sys, io
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from streams import STREAMS

TIMEOUT = 10
REINTENTOS = 2
AUDIO_CHECK_BYTES = 65536  # 64KB de stream para analizar
SILENCE_THRESHOLD = 500    # Umbral de amplitud (ajustable)

def check_stream(s):
    """Verifica conexión Y si hay audio real"""
    for i in range(REINTENTOS):
        try:
            # 1. Verificar conexión al stream
            r = requests.get(s["url"], timeout=TIMEOUT, stream=True,
                              headers={"User-Agent":"EpicentroMonitor/1.0","Icy-MetaData":"1"})

            if r.status_code >= 400:
                return "offline", r.status_code, f"HTTP {r.status_code}"

            # 2. Descargar muestra de audio para analizar
            audio_data = b""
            try:
                for chunk in r.iter_content(chunk_size=8192):
                    audio_data += chunk
                    if len(audio_data) >= AUDIO_CHECK_BYTES:
                        break
                r.close()
            except:
                r.close()
                return "offline", None, "Error descargando stream"

            if len(audio_data) < 1000:
                return "offline", None, "Stream vacio"

            # 3. Análisis simple de amplitud (detecta silencio)
            try:
                samples = []
                for j in range(0, min(len(audio_data)-1, 10000), 2):
                    sample = int.from_bytes(audio_data[j:j+2], byteorder='little', signed=True)
                    samples.append(abs(sample))

                if not samples:
                    return "online", r.status_code, None

                avg_amplitude = sum(samples) / len(samples)
                max_amplitude = max(samples)

                if avg_amplitude < SILENCE_THRESHOLD and max_amplitude < 2000:
                    return "silencio", r.status_code, f"Stream en silencio (amp: {int(avg_amplitude)})"
