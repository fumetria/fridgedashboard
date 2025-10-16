Perfecto — buena idea. Te explico paso a paso cómo montar un sistema con una Raspberry Pi que lea sondas de temperatura en un circuito frigorífico y te muestre las temperaturas sobre un esquema del ciclo frigorífico. Voy a darte:

-   lista de componentes (con alternativas),
-   montaje eléctrico y físico (cómo fijar las sondas a las tuberías sin abrir el circuito),
-   software (activar 1-Wire en la RPi, script para leer sensores y servidor web sencillo que dibuja el ciclo y actualiza las temperaturas),
-   consejos de seguridad y mejoras posibles.

Voy a suponer que usarás sondas DS18B20 (versiones sumergibles / probe) porque son baratas, fáciles de usar con Raspberry Pi y suficientes para medir las temperaturas en las tuberías (superficiales). Si quieres más precisión, comento opciones avanzadas al final.

---

# 1) Componentes necesarios (mínimo)

-   Raspberry Pi (cualquiera con GPIO; Pi 3, Pi 4 o Pi Zero W sirven).
-   microSD (8–16 GB) con Raspberry Pi OS.
-   Fuente USB 5V para la Pi (2–3 A según modelo).
-   Sondas DS18B20 waterproof (probe) — cantidad según puntos que quieras medir (recomendado: 4 ó 6). Modelos típicos: probe de acero inoxidable con cable.
-   Resistencia 4.7 kΩ (una sola, pull-up para la línea 1-Wire).
-   Cables dupont / breadboard o soldadura y 3-5 mm de tubo termo-retractil.
-   Cinta de aluminio térmica / pasta térmica para acoplar la sonda a la tubería (mejora la transferencia térmica).
-   Abrazaderas / bridas / cinta americana para fijar la sonda al tubo.
-   (Opcional) Caja / carcasa para la Pi, y insulación para volver a aislar la tubería donde fijes la sonda.
-   (Opcional, avanzado) PT100 + amplificador (MAX31865) o termopar + amplificador si quieres mayor precisión o rangos especiales.

---

# 2) Dónde colocar las sondas en el circuito frigorífico (puntos recomendados)

Típico mínimo (4 sondas útiles):

1. Salida del evaporador / tubería de succión (cerca del evaporador) — para ver temperatura de vapor antes del compresor.
2. Entrada al compresor / succión (lo más cerca posible exteriormente) — identifica pérdidas de calor.
3. Salida del compresor / descarga (línea caliente de gas comprimido) — tubo pequeño y caliente.
4. Salida del condensador / línea líquida (después del condensador) — medir temperatura del líquido.

Si quieres, añade:

-   sonda en evaporador (interior de la bobina) y/o entrada de la válvula de expansión.
-   sonda ambiente/nevera para referencia.

Importante: no abras el circuito frigorífico ni introduzcas sondas en el fluido. Mide por contacto en la superficie de las tuberías. Usa pasta térmica y cinta metálica para buen contacto.

---

# 3) Montaje físico de las sondas (buenas prácticas)

1. Limpia la parte del tubo donde fijarás la sonda (quita polvo/aceite).
2. Aplica pasta térmica en la punta de la sonda (mejora el acoplamiento).
3. Fija la sonda con cinta de aluminio y una abrazadera o brida para que quede en contacto firme con el tubo.
4. Vuelve a aislar (espuma) la zona si el tubo está aislado; deja pasar los cables.
5. Identifica y etiqueta cada sonda físicamente (ej. “S1 evaporador”, “S2 succión”) — será clave para mapear ID ↔ ubicación en el software.

---

# 4) Cableado con la Raspberry Pi (DS18B20, bus 1-Wire)

Las DS18B20 pueden conectarse todas en el mismo bus 1-Wire:

Cable típico de cada probe: rojo = VCC, negro = GND, amarillo/blanco = DATA (puede variar por vendedor; confirma).

Conectar así en la RPi:

-   VCC de las sondas → 3.3 V de la Raspberry Pi (NO uses 5 V si vas a leer la línea DATA con GPIO de la Pi).
-   GND → GND de la Pi.
-   DATA (todos los DATA de las sondas juntos) → GPIO4 (pin físico 7) en la Pi.
-   Resistencia 4.7 kΩ entre DATA y 3.3 V (pull-up).

Es decir: todas las sondas comparten DATA y GND; sólo necesitas una resistencia pull-up. Evita alimentar las sondas con 5V si vas a conectar DATA al GPIO de la Pi (riesgo para la Pi).

Diagrama lógico (texto):

```bash
3.3V -----+------ 4.7kΩ ------+---- DATA (GPIO4)
          |                  |
         VCC(sonda1)        DATA(sonda1)
         VCC(sonda2)        DATA(sonda2)
GND -----+------------------+---- GND(sondas)
GPIO4 ----------------------- (DATA común)
```

---

# 5) Software en la Raspberry Pi (instalar y habilitar 1-Wire)

1. Flashea Raspberry Pi OS en la microSD e inicia la Pi.
2. Actualiza:

```bash
sudo apt update && sudo apt upgrade -y
```

3. Habilita 1-Wire:

-   Opción GUI: sudo raspi-config → Interface Options → 1-Wire → Enable → Reboot.
-   Opción manual: edita /boot/config.txt y añade al final:

```
dtoverlay=w1-gpio,gpiopin=4
```

y reinicia.

4. Carga los módulos (si no se cargaron):

```bash

sudo modprobe w1-gpio
sudo modprobe w1-therm
```

5. Verifica detección de sondas:

```bash

ls /sys/bus/w1/devices/

# deberías ver carpetas que empiezan por 28-xxxxxxxx
```

6. Leer una sonda manualmente:

```Bash

cat /sys/bus/w1/devices/28-XXXXXXXXXXXX/w1_slave

# en el texto aparecerá "t=XXXXX" (temperatura en miligrados)
```

---

# 6) Mapeo de IDs a ubicaciones

Cuando conectes las sondas, cada DS18B20 tiene un ID único tipo 28-00000xxxxx. Haz esto:

1. Conecta y fija cada sonda en su ubicación y etiquétala físicamente.
2. En la Pi, mira los IDs detectados:

```bash
for d in /sys/bus/w1/devices/28\* ; do echo "$d"; cat $d/w1_slave; done
```

3. Anota qué ID corresponde a cada etiqueta física (ej. 28-00000a1b2c3 -> Succión).
4. Guarda ese mapeo en un archivo (ej. sensor_map.json) o directamente en el script que usarás para mostrar la UI.

---

# 7) Script Python y pequeña web para mostrar el ciclo frigorífico

Abajo tienes un ejemplo completo: lee todas las DS18B20, mapea ID → ubicación y sirve una página web que muestra un esquema muy simple del ciclo (SVG) con las temperaturas actualizadas cada 2 segundos.

Guarda todo en un solo archivo app.py.

```python

# app.py

from flask import Flask, jsonify, Response
import glob, os, time, json

app = Flask(name)

# --- EDITA este diccionario con tus IDs reales (los que ves en /sys/bus/w1/devices/)

SENSOR_MAP = {
"28-00000aaaaaaa": "Evaporador",
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
devices = glob.glob(BASE_DIR + '28\*')
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

if name == 'main': # Ejecutar: python3 app.py
app.run(host='0.0.0.0', port=5000)
```

**Cómo usarlo:**

-   Edita `SENSOR_MAP` con los IDs reales (los ves en `/sys/bus/w1/devices/`).
-   Instala Flask si no la tienes:

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask
python app.py
```

-   Abre en tu navegador `http://IP_DE_TU_PI:5000` y verás el esquema y las temperaturas.

---

# 8) Cálculos útiles (superheat / subcooling) — nota rápida

Para calcusobrecalentamiento (superheat)t)\*subenfriamiento (subcooling)g)** necesipresioneses** (para conocer la temperatura de saturación) o tablas/sondas adicionales. Con sólo temperaturas en tuberías puedes estimar diferencias (ΔT entre líneas), pero para superheat real necesitarías medir la presión de succión y convertirla a temperatura de saturación. Si te interesa ampliar (añadir sensores de presión transductores y lectura con ADC), te explico cómo hacerlo.

---

# 9) Seguridad y advertenciasNo abrasas\*\* el circuito frigorífico salvo que seas técnico certificado. La manipulación de refrigerante o tuberías a presión es peligrosa.

-   Evita tocar bornes del compresor y desconecta la alimentación si trabajas muy cerca.
-   Si vas a medir zonas muy calientes (descarga), protege los cables y la sonda.
-   Si no estás seguro de fijar algo (por ejemplo, volver a aislar correctamente la tubería), consulta con un profesional.

---

# 10) Mejoras y ampliacionesInterfaz más avanzada:

1. ** uGrafana + InfluxDBDB** para almacenar históricos y hacer dashboardsNode-REDED**: muy buena para integración, fácil de crear UI visual sin programarPT100 + MAX3186565**: más precisión y estabilidad si lo necesitas, pero requiere un poco más de electrónicaAñadir lectura de presioneses** con transductores (ej. 0-10 bar) y un ADC (ADS1115) para poder calcular superheat/subcooling correctamenteAlertasas** por email/push si una temperatura sale de rango.

---

# 11) Lista rápida de compra (ejemplo)

-   Raspberry Pi 4 (o Zero W) + funda
-   microSD 16 GB
-   4–6 × DS18B20 waterproof probes
-   1 × resistencia 4.7 kΩ
-   Pack cables dupont / breadboard
-   Cinta aluminio térmica + pasta térmica pequeña
-   Abrazaderas / bridas

---

Si quieres, en el siguiente pte puedo:o:\*\*

-   generarte el `app.py` listo para descargar (con un `sensor_map` ejemplo),
-   o crearte una versión Node-REDED** o Grafana+InfluxDBDB** y los pasos de instalación concretos,
-   o decirte exactamedónde fijarar\*\* las sondas en TU nevera (dime modelo/tipo y cuántas sondas quieres).
    Dime qué prefieres y te lo dejo listo (archivo de código, instrucciones precisas de compra, o instrucciones para añadir presiones).
