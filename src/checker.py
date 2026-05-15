import json, requests, time, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from streams import STREAMS

TIMEOUT = 10
REINTENTOS = 2
AUDIO_CHECK_BYTES = 65536
SILENCE_THRESHOLD = 500
VARIATION_THRESHOLD = 1000
UNIQUE_VALUES_MIN = 30  # Mínimo de valores únicos en 100 muestras para ser audio real

def check_stream(s):
    for i in range(REINTENTOS):
        try:
            r = requests.get(s["url"], timeout=TIMEOUT, stream=True,
                              headers={"User-Agent":"EpicentroMonitor/1.0","Icy-MetaData":"1"})

            if r.status_code >= 400:
                return "offline", r.status_code, f"HTTP {r.status_code}"

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

            try:
                samples = []
                for j in range(0, min(len(audio_data)-1, 10000), 2):
                    sample = int.from_bytes(audio_data[j:j+2], byteorder='little', signed=True)
                    samples.append(abs(sample))

                if not samples:
                    return "online", r.status_code, None

                # Calcular estadísticas
                n = len(samples)
                avg_amplitude = sum(samples) / n
                max_amplitude = max(samples)

                # Calcular desviación estándar
                variance = sum((x - avg_amplitude) ** 2 for x in samples) / n
                std_dev = variance ** 0.5

                # Contar valores únicos en las primeras 100 muestras
                unique_count = len(set(samples[:100]))

                # 1. Detectar silencio total: amplitud muy baja
                if avg_amplitude < SILENCE_THRESHOLD and max_amplitude < 2000:
                    return "silencio", r.status_code, f"Silencio total (amp: {int(avg_amplitude)})"

                # 2. Detectar tono continuo/sin programación: pocos valores únicos
                if unique_count < UNIQUE_VALUES_MIN:
                    return "silencio", r.status_code, f"Sin programacion (uniq: {unique_count})"

                # 3. Detectar ruido sin variación
                if std_dev < VARIATION_THRESHOLD:
                    return "silencio", r.status_code, f"Tono continuo (var: {int(std_dev)})"

                return "online", r.status_code, None

            except Exception as e:
                return "online", r.status_code, None

        except requests.exceptions.ConnectionError:
            err = "Sin conexion al servidor"
        except requests.exceptions.Timeout:
            err = "Timeout sin respuesta"
        except Exception as e:
            err = str(e)[:80]

        if i < REINTENTOS-1:
            time.sleep(2)

    return "offline", None, err

def main():
    now = datetime.now(timezone.utc)
    print(f"\n Verificacion con analisis de audio {now.strftime('%d/%m/%Y %H:%M UTC')}")
    resultados, on, off, sil = [], 0, 0, 0

    for s in STREAMS:
        estado, code, error = check_stream(s)

        if estado == "online":
            icono = "OK"
            on += 1
        elif estado == "silencio":
            icono = "SIL"
            sil += 1
        else:
            icono = "XX"
            off += 1

        print(f"  {icono} [{s['categoria'][:8]}] {s['nombre']}: {estado.upper()}{' - '+error if error else ''}")

        resultados.append({
            **{k:s[k] for k in ["nombre","zona","frecuencia","ciudad","categoria","url","url_web","lat","lon"]},
            "estado": estado,
            "http_code": code,
            "error": error,
            "verificado": now.isoformat()
        })

    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    with open(data_dir / "estado.json","w",encoding="utf-8") as f:
        json.dump({
            "verificado": now.isoformat(),
            "total": len(STREAMS),
            "online": on,
            "offline": off,
            "silencio": sil,
            "senales": resultados
        }, f, ensure_ascii=False, indent=2)

    print(f"\n Resultado: {on} online / {sil} silencio / {off} offline")

if __name__=="__main__":
    main()
