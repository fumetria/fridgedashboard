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
    <title>Ciclo frigorífico</title>
    <style>
        h1 {
            text-transform: capitalize;

        }

        body {
            display: grid;
            grid-template-rows: auto 1fr auto;
            font-family: Arial, sans-serif;
            height: 100vh;
            margin: 0;
        }

        header,
        footer {
            background-color: oklch(54.6% 0.245 262.881);
            color: white;
            width: 100%;
        }

        header {
            text-transform: capitalize;
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid oklch(54.6% 0.245 262.881);

            & h1 {
                font-size: 2.2rem;
                margin-left: 20px;
            }
        }

        footer {
            font-size: small;
            text-align: center;
            padding-block: 0;
        }




        #app {
            background: white;
            display: grid;
            justify-items: center;
            align-items: center;

        }

        #fridge {
            width: 400px;
            height: 400px;
            position: relative;
            border: 1px solid;
            text-align: center;
        }

        .sensor {
            font-size: 26px;
            position: absolute;
            cursor: pointer;
        }

        #evaporador-salida {
            position: absolute;
            top: 85%;
            right: 15%;
            font-size: 16px;
            color: blue;
            cursor: pointer;
        }

        #evaporador-entrada {
            position: absolute;
            top: 85%;
            left: 20%;
            font-size: 16px;
            color: blue;
            cursor: pointer;
        }

        #compresor-entrada {
            position: absolute;
            top: 65%;
            right: 0%;
            font-size: 16px;
            color: blue;
            cursor: pointer;
        }

        #compresor-salida {
            position: absolute;
            top: 34%;
            right: 0%;
            font-size: 16px;
            color: red;
            cursor: pointer;
        }

        #condensador-entrada {
            position: absolute;
            top: 15%;
            right: 15%;
            font-size: 16px;
            color: red;
            cursor: pointer;
        }

        #condensador-salida {
            position: absolute;
            top: 15%;
            left: 20%;
            font-size: 16px;
            color: red;
            cursor: pointer;
        }

        #temperatura-camara {
            position: absolute;
            top: 42%;
            left: 45%;
            font-size: 16px;
            color: yellowgreen;
            cursor: pointer;
        }

        /* 
        #sensor-alta {
            top: 25%;
            right: 0%;
            font-size: 22px;
            color: darkred;
            cursor: pointer;
        }

        #sensor-baja {
            top: 70%;
            right: 0%;
            font-size: 22px;
            color: darkblue;
            cursor: pointer; */
        /* } */

        #temperatura-ambiente {
            cursor: pointer;
            color: green;
        }

        #outdoor {
            display: grid;
            place-items: center;
            position: relative;
            border: 1px solid;
            padding: 0.5rem;

            & p,
            #temperatura-ambiente {
                text-align: center;
                font-weight: 700;
                font-size: 20px;
            }
        }

        .hidden {
            display: none;
        }

        #compresor {
            position: absolute;
            top: 51%;
            left: 55%;
            width: 110px;
            height: 30px;
            background: none;
            border: none;
            cursor: pointer;

        }

        #condensador {
            position: absolute;
            top: 36%;
            left: 32%;
            width: 140px;
            height: 30px;
            background: none;
            border: none;
            cursor: pointer;

        }

        #valvula-de-expansion {
            position: absolute;
            top: 49%;
            left: 20%;
            width: 140px;
            height: 35px;
            background: none;
            border: none;
            cursor: pointer;

        }

        #evaporador {
            position: absolute;
            top: 60%;
            left: 32%;
            width: 140px;
            height: 35px;
            background: none;
            border: none;
            cursor: pointer;

        }

        #main {
            display: flex;
            justify-content: left;
            align-items: center;
            gap: 20px;
        }

        #show-info {
            text-wrap: wrap;
            display: flex;
            flex-direction: column;

        }

        #pegatina {
            background-color: white;
            width: 100px;
            height: 20px;
            position: absolute;
            top: 92%;
            right: 5%;

        }
    </style>
</head>

<body>
    <header>

        <h1>monitor frigorífico</h1>
        <img src="/static/logo-ies-pou-clar.png" alt="">
    </header>
    <section id="app">
        <!-- <h2>Ciclo Frigorífico — Temperaturas</h2> -->

        <!-- <p>Actualiza cada 2 segundos.</p>
<div>Presión baja (entrada compresor): <span id="sensor-baja">-- bar</span></div>
<div>Presión alta (salida compresor): <span id="sensor-alta">-- bar</span></div>
<br> -->
        <div id="main">
            <section id="outdoor">
                <p>EXTERIOR</p>
                <div id="temperatura-ambiente">-- ºC</div>
                <section id="fridge">
                    <img src="/static/Froztec-Cicloderefrigeracion.webp" width="400" height="400">
                    <div id="evaporador-entrada" class="sensor" onclick="showinfo('evaporador-entrada')">-- ºC</div>

                    <div id="evaporador-salida" class="sensor" onclick="showinfo('evaporador-salida')">-- ºC</div>

                    <div id="compresor-entrada" class="sensor" onclick="showinfo('compresor-entrada')">-- ºC</div>

                    <div id="compresor-salida" class="sensor" onclick="showinfo('compresor-salida')">-- ºC</div>

                    <div id="condensador-entrada" class="sensor" onclick="showinfo('condensador-entrada')">-- ºC</div>

                    <div id="condensador-salida" class="sensor" onclick="showinfo('condensador-salida')">-- ºC</div>
                    <div id="pegatina"></div>

                    <!-- <div id="sensor-alta" class="sensor" onclick="showinfo('sensor-alta')">-- bar</div>

                <div id="sensor-baja" class="sensor" onclick="showinfo('sensor-baja')">-- bar</div> -->

                    <div id="temperatura-camara" class="sensor">-- ºC</div>
                    <button id="compresor" onclick="showinfo('compresor')"></button>
                    <button id="condensador" onclick="showinfo('condensador')"></button>
                    <button id="valvula-de-expansion" onclick="showinfo('valvula-de-expansion')"></button>
                    <button id="evaporador" onclick="showinfo('evaporador')"></button>
                </section>
            </section>
            <section id="show-info"></section>
        </div>

    </section>

    <script>
        async function updateTemps() {
            try {
                const res = await fetch('/temps');
                const data = await res.json();

                for (const key in data) {
                    const el = document.getElementById(key);
                    if (el) {
                        const t = data[key] === null ? '--' : (data[key].toFixed(2) + ' ºC');
                        el.textContent = t;
                    }
                }
            } catch (e) {
                console.error('Error:', e);
            }
        }
        setInterval(updateTemps, 1000);
        updateTemps();

        const diccionario = {
            "evaporador-entrada": {
                titulo: "Entrada Evaporador",
                info: "",
                imgUrl: "/static/Entrada evaporador.png",
            },
            "evaporador-salida": {
                titulo: "Salida Evaporador",
                info: "",
                imgUrl: "/static/salida-evaporador.png"
            },
            "compresor-entrada": {
                titulo: "Compresor entrada",
                info: "Información sobre el compresor de entrda",
                imgUrl: "https://frigoristas.files.wordpress.com/2016/06/condensador-aire-21.jpg"
            },
            "compresor-salida": {
                titulo: "Compresor salida",
                info: "Información sobre el compresor de salida",
                imgUrl: "https://frigoristas.files.wordpress.com/2016/06/condensador-aire-21.jpg"
            },
            "condensador-entrada": {
                titulo: "Condesador entrada",
                info: "Información sobre el condensador de entrda",
                imgUrl: "https://frigoristas.files.wordpress.com/2016/06/condensador-aire-21.jpg"
            },
            "condensador-salida": {
                titulo: "condensador salida",
                info: "Información sobre el condensador de salida",
                imgUrl: "https://frigoristas.files.wordpress.com/2016/06/condensador-aire-21.jpg"
            },

            "compresor": {
                titulo: "compresor",
                info: "",
                imgUrl: "/static/Compresores.png"
            },
            "condensador": {
                titulo: "condensador",
                info: "",
                imgUrl: "/static/Condensador.png"
            },
            "valvula-de-expansion": {
                titulo: "Válvula de expansión",
                info: "",
                imgUrl: "/static/Valvula-expansion.png"
            },
            "evaporador": {
                titulo: "evaporador",
                info: ``,
                imgUrl: "/static/Evaporador.png"
            },
            // "sensor-alta": {
            //     titulo: "sensor alta",
            //     info: "Información sobre el sensor de alta",
            //     imgUrl: "https://frigoristas.files.wordpress.com/2016/06/condensador-aire-21.jpg"
            // },
            // "sensor-baja": {
            //     titulo: "sensor baja",
            //     info: "Información sobre el sensor de baja",
            //     imgUrl: "https://frigoristas.files.wordpress.com/2016/06/condensador-aire-21.jpg"
            // },
        }

        function showinfo(element) {
            const infoPanel = document.getElementById('show-info');
            const infoElement = diccionario[element];
            console.log(infoElement.titulo);
            // infoPanel.innerHTML = `
            //     <h1>${infoElement.titulo}</h1>
            //     <p id='show-info-text'>${infoElement.info}</p>
            //     ${infoElement.imgUrl ? `<img src="${infoElement.imgUrl}" />` : ``}
            // `
            infoPanel.innerHTML = `
                <h1>${infoElement.titulo}</h1>
                ${infoElement.imgUrl ? `<img src="${infoElement.imgUrl}" />` : ``}
            `
        }
    </script>

    <footer>
        <p>Creado por CHANG JUN FU LIN</p>
    </footer>
</body>

</html>
"""
    return Response(html, mimetype='text/html')


if __name__ == '__main__':
    # Ejecutar: python3 app.py
    app.run(host='0.0.0.0', port=5000)
