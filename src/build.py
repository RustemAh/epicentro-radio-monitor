import json
from pathlib import Path
from datetime import datetime

ROOT     = Path(__file__).parent.parent
DATA     = ROOT / "data" / "estado.json"
TEMPLATE = ROOT / "src" / "template.html"
PUBLIC   = ROOT / "public"

data = json.loads(DATA.read_text(encoding="utf-8"))
PUBLIC.mkdir(exist_ok=True)

try:
    dt = datetime.fromisoformat(data["verificado"].replace("Z", "+00:00"))
    ts = dt.strftime("%d/%m/%Y %H:%M UTC")
except:
    ts = "?"

html = TEMPLATE.read_text(encoding="utf-8")
html = html.replace("__DATA_JS__", json.dumps(data, ensure_ascii=False))
html = html.replace("__TS__", ts)
html = html.replace("__TOTAL__", str(data["total"]))
html = html.replace("__ONLINE__", str(data["online"]))
html = html.replace("__OFFLINE__", str(data["offline"]))
html = html.replace("__SILENCIO__", str(data.get("silencio", 0)))

(PUBLIC / "index.html").write_text(html, encoding="utf-8")
print(f"HTML generado: {data['total']} senales, {data['online']} online, {data.get('silencio',0)} silencio")
