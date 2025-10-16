# app.py
from flask import Flask, jsonify, Response
import glob, os, time, json

app = Flask(__name__)

# --- EDITA este diccionario con tus IDs reales (los que ves en /sys/bus/w1/devices/)
SENSOR_MAP = {
    "28-000000b1aff0": "Evaporador",
    "28-00000bbbbbbb": "Succion",
    "28-00000ccccccc": "Descarga",
    "28-00000ddddddd": "Liquido"
}
BASE_DIR = '/sys/bus/w1/devices/'

def read_temp_from_folder(folder):
    try:
        with open(os.path.join(folder, 'w1_slave'), 'r') as f:
            text = f.read()
        lines = text.splitlines()
        if lines and 't=' in lines[-1]:
            temp_milli = lines[-1].split('t=')[-1]
            return float(temp_milli) / 1000.0
    except Exception:
        return None

@app.route('/temps')
def temps():
    devices = glob.glob(BASE_DIR + '28*')
    result = {}
    for d in devices:
        id = os.path.basename(d)
        label = SENSOR_MAP.get(id, id)
        temp = read_temp_from_folder(d)
        result[label] = round(temp, 3) if temp is not None else None
    return jsonify(result)

@app.route('/')
def index():
    html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Ciclo frigorífico - temperaturas</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    svg { width: 700px; max-width: 100%; border: 1px solid #ddd; }
    .node { font-size: 14px; text-anchor: middle; }
    .temp { font-weight: bold; }
  </style>
</head>
<body>
  <h2>Ciclo frigorífico — temperaturas</h2>
  <p>Actualiza cada 2 segundos.</p>
  <svg viewBox="0 0 700 300">
    <!-- Compressor -->
    <rect x="300" y="30" width="100" height="60" fill="#f2f2f2" stroke="#333"/>
    <text x="350" y="65" class="node">Compresor</text>
    <text id="Descarga" x="350" y="85" class="node temp">-- °C</text>

    <!-- Condenser -->
    <rect x="480" y="30" width="140" height="60" fill="#f2f2f2" stroke="#333"/>
    <text x="550" y="65" class="node">Condensador</text>
    <text id="Liquido" x="550" y="85" class="node temp">-- °C</text>

    <!-- Expansion valve -->
    <circle cx="610" cy="170" r="20" fill="#f2f2f2" stroke="#333"/>
    <text x="610" y="175" class="node">Válvula</text>

    <!-- Evaporator -->
    <rect x="300" y="170" width="140" height="60" fill="#f2f2f2" stroke="#333"/>
    <text x="370" y="205" class="node">Evaporador</text>
    <text id="Evaporador" x="370" y="225" class="node temp">-- °C</text>

    <!-- Suction line -->
    <text id="Succion" x="200" y="205" class="node temp">-- °C</text>

    <!-- Lines (simple) -->
    <line x1="350" y1="90" x2="480" y2="60" stroke="#444" stroke-width="2"/>
    <line x1="620" y1="90" x2="620" y2="150" stroke="#444" stroke-width="2"/>
    <line x1="620" y1="190" x2="440" y2="190" stroke="#444" stroke-width="2"/>
    <line x1="440" y1="190" x2="350" y2="190" stroke="#444" stroke-width="2"/>
    <line x1="300" y1="140" x2="300" y2="90" stroke="#444" stroke-width="2"/>
    <line x1="300" y1="90" x2="350" y2="90" stroke="#444" stroke-width="2"/>
  </svg>

<script>
async function updateTemps() {
  try {
    const res = await fetch('/temps');
    const data = await res.json();
    // para cada clave -> actualiza el text cuyo id sea esa clave
    for (const key in data){
      const el = document.getElementById(key);
      if (el) {
        const t = data[key] === null ? '--' : (data[key].toFixed(2) + ' °C');
        el.textContent = t;
      }
    }
  } catch (e) {
    console.error('fetch error', e);
  }
}
setInterval(updateTemps, 2000);
updateTemps();
</script>
</body>
</html>
"""
    return Response(html, mimetype='text/html')

if __name__ == '__main__':
    # Ejecutar: python3 app.py
    app.run(host='0.0.0.0', port=5000)
