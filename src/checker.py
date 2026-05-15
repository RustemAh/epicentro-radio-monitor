import json, requests, time, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from streams import STREAMS

TIMEOUT = 10
REINTENTOS = 2

def check_stream(s):
    for i in range(REINTENTOS):
        try:
            r = requests.head(s["url"], timeout=TIMEOUT, allow_redirects=True,
                              headers={"User-Agent":"EpicentroMonitor/1.0","Icy-MetaData":"1"})
            if r.status_code < 400: return "online", r.status_code, None
            r2 = requests.get(s["url"], timeout=TIMEOUT, stream=True,
                              headers={"User-Agent":"EpicentroMonitor/1.0","Icy-MetaData":"1"})
            r2.close()
            if r2.status_code < 400: return "online", r2.status_code, None
            return "offline", r2.status_code, f"HTTP {r2.status_code}"
        except requests.exceptions.ConnectionError: err = "Sin conexion al servidor"
        except requests.exceptions.Timeout: err = "Timeout sin respuesta"
        except Exception as e: err = str(e)[:80]
        if i < REINTENTOS-1: time.sleep(2)
    return "offline", None, err

def main():
    now = datetime.now(timezone.utc)
    print(f"\n Verificacion iniciada {now.strftime('%d/%m/%Y %H:%M UTC')}")
    resultados, on, off = [], 0, 0
    for s in STREAMS:
        estado, code, error = check_stream(s)
        print(f"  {'OK' if estado=='online' else 'XX'} [{s['categoria'][:8]}] {s['nombre']}: {estado.upper()}{' - '+error if error else ''}")
        if estado=="online": on+=1
        else: off+=1
        resultados.append({**{k:s[k] for k in ["nombre","zona","frecuencia","ciudad","categoria","url","url_web","lat","lon"]},
                            "estado":estado,"http_code":code,"error":error,"verificado":now.isoformat()})
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / "estado.json","w",encoding="utf-8") as f:
        json.dump({"verificado":now.isoformat(),"total":len(STREAMS),"online":on,"offline":off,"senales":resultados},f,ensure_ascii=False,indent=2)
    print(f"\n Resultado: {on} online / {off} offline")

if __name__=="__main__": main()
