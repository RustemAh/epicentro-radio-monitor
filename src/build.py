import json
from pathlib import Path
from datetime import datetime

data = json.loads(Path("data/estado.json").read_text(encoding="utf-8"))
Path("public").mkdir(exist_ok=True)
try:
    dt = datetime.fromisoformat(data["verificado"].replace("Z","+00:00"))
    ts = dt.strftime("%d/%m/%Y %H:%M UTC")
except: ts = "?"
html = Path("src/template.html").read_text(encoding="utf-8")
html = html.replace("__DATA_JS__", json.dumps(data, ensure_ascii=False))
html = html.replace("__TS__", ts).replace("__TOTAL__", str(data["total"]))
html = html.replace("__ONLINE__", str(data["online"])).replace("__OFFLINE__", str(data["offline"]))
Path("public/index.html").write_text(html, encoding="utf-8")
print(f"HTML generado: {data['total']} senales, {data['online']} online")
