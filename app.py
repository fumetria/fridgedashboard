# app.py
import glob
import os

from flask import Flask, jsonify, Response, url_for

app = Flask(__name__)

# --- EDITA este diccionario con tus IDs reales (los que ves en /sys/bus/w1/devices/)
# Añade todos los sensores que tengas y añade el mismo nombre que las ids de la página HTML
SENSOR_MAP = {
    "28-000000b19d26": "evaporador-entrada",
    "28-000000b1a98c": "evaporador-salida",
    "28-000000b20b6b": "compresor-entrada",
    "28-000000b22d0b": "compresor-salida",
    "28-000000b22ef2": "condensador-entrada",
    "28-000000b24aac": "condensador-salida",
    "28-000000b24c95": "temperatura-ambiente",
    "28-000000b24fab": "temperatura-camara"
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
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: Arial, sans-serif;
            padding: 20px;
            background-color: grey;
            height: 100dvh;
        }

        #app {
            background-color: white;
            padding: 20px;
        }

        #fridge {
            width: 400px;
            height: 300px;
            position: relative;
            border: 1px solid;
        }

        #evaporador-salida {
            position: absolute;
            top: 16%;
            right: 28%;
            font-size: 26px;
            color: blue;
        }

        #evaporador-entrada {
            position: absolute;
            top: 16%;
            left: 20%;
            font-size: 26px;
            color: blue;
        }

        #compresor-entrada {
            position: absolute;
            top: 30%;
            right: 15%;
            font-size: 26px;
            color: blue;
        }

        #compresor-salida {
            position: absolute;
            top: 60%;
            left: 70%;
            font-size: 26px;
            color: red;
        }

        #condensador-entrada {
            position: absolute;
            top: 80%;
            right: 25%;
            font-size: 26px;
            color: red;
        }

        #condensador-salida {
            position: absolute;
            top: 80%;
            left: 20%;
            font-size: 26px;
            color: red;
        }

        #temperatura-camara {
            position: absolute;
            top: 48%;
            left: 38%;
            font-size: 26px;
            color: green;
        }

        #temperatura-ambiente {
            color: green;
        }

        #outdoor {
            border: 1px solid;
            padding: 0.5rem 2rem;

            & p,
            #temperatura-ambiente {
                text-align: center;
                font-weight: 700;
                font-size: 26px;
            }
        }
    </style>
</head>

<body>
    <section id="app">
        <h2>Ciclo frigorífico — temperaturas</h2>
        <p>Actualiza cada 2 segundos.</p>
        <section id="outdoor">
            <p>EXTERIOR</p>
            <div id="temperatura-ambiente">-- ºC</div>
            <section id="fridge">
                <img src="/static/esquema.webp" alt="" width="400" height="300">
                <div id="evaporador-entrada">-- ºC</div>
                <div id="evaporador-salida">-- ºC</div>
                <div id="compresor-entrada">-- ºC</div>
                <div id="compresor-salida">-- ºC</div>
                <div id="condensador-entrada">-- ºC</div>
                <div id="condensador-salida">-- ºC</div>
                <div id="temperatura-camara">-- ºC</div>
            </section>
        </section>
    </section>

    <script>
        async function updateTemps() {
            try {
                const res = await fetch('/temps');
                const data = await res.json();
                // para cada clave -> actualiza el text cuyo id sea esa clave
                for (const key in data) {
                    const el = document.getElementById(key);
                    if (el) {
                        const t = data[key] === null ? '--' : (data[key].toFixed(2) + '°C');
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
