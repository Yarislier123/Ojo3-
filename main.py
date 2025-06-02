lofrom flask import Flask, request, redirect, render_template_string, flash, session, url_for
from threading import Thread
import json
import subprocess
import uuid
import random
from collections import defaultdict
from functools import wraps
from proxy_utils import obtener_proxy

app = Flask(__name__)
app.secret_key = "supersecretkey"

def leer_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def escribir_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

CONFIG = leer_json("config.json", {})

def requiere_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logueado"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        clave = request.form.get("clave")
        if clave == CONFIG.get("clave_acceso"):
            session["logueado"] = True
            flash("✅ Acceso concedido.")
            return redirect("/panel")
        else:
            flash("❌ Clave incorrecta.")
    return render_template_string("""
        <h2>🔒 Acceso requerido</h2>
        <form method="post">
            <input name="clave" type="password" placeholder="Clave de acceso" required>
            <button>Entrar</button>
        </form>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <ul style="color: red;">
              {% for msg in messages %}
                <li>{{ msg }}</li>
              {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
    """)

@app.route("/logout")
@requere_login
def logout():
    session.clear()
    return redirect("/login")

def leer_enlaces():
    return leer_json("enlaces.json", [])

def guardar_enlaces(data):
    escribir_json("enlaces.json", data)

def leer_cuentas():
    return leer_json("cuentas.json", [])

def leer_tokens():
    return leer_json("tokens.json", [])

def registrar_token(enlace, token, cuenta_id):
    tokens = leer_tokens()
    tokens.append({
        "id": str(uuid.uuid4()),
        "url": enlace,
        "token": token,
        "cuenta": cuenta_id
    })
    escribir_json("tokens.json", tokens)

def ejecutar_bot(enlace_obj, cuenta):
    def tarea():
        url = enlace_obj.get("url")
        tipo = enlace_obj.get("tipo")
        cuenta_id = cuenta.get("id") if cuenta else "sin_cuenta"
        token_cuenta = cuenta.get("token", "")
        proxy = cuenta.get("proxy") or obtener_proxy()
        proxy_arg = proxy if proxy else "None"

        result = subprocess.run([
            "python", "skip_ad_simulation.py",
            url,
            tipo,
            token_cuenta,
            proxy_arg
        ], capture_output=True, text=True)

        salida = result.stdout.strip().split("\n")
        token = salida[-1] if salida else ""
        registrar_token(url, token, cuenta_id)

    Thread(target=tarea).start()

@app.route("/")
def home():
    return redirect("/panel")

@app.route("/panel")
@requiere_login
def panel():
    enlaces = leer_enlaces()
    cuentas = leer_cuentas()
    tokens = leer_tokens()

    estadisticas_enlace = { e["url"]: e.get("visitas", 0) for e in enlaces }
    estadisticas_cuenta = defaultdict(int)
    for t in tokens:
        estadisticas_cuenta[t["cuenta"]] += 1

    interval = CONFIG.get("interval_minutes", 15)

    return render_template_string("""
        <h2>🔗 Enlaces activos</h2>
        <ul>
        {% for e in enlaces %}
          <li>
            <b>{{ e.url }}</b> ({{ e.tipo }}) — Visitas iniciadas manual: {{ e.visitas }} 
            <a href="{{ url_for('eliminar', url=e.url) }}">🗑️ Eliminar</a>
            <a href="{{ url_for('iniciar', url=e.url) }}">▶️ Iniciar manual</a>
          </li>
        {% endfor %}
        </ul>

        <hr>
        <h3>➕ Agregar nuevo enlace</h3>
        <form action="{{ url_for('agregar') }}" method="post">
          <input name="url" placeholder="URL" required>
          <select name="tipo">
            <option value="adfly">adfly</option>
            <option value="shorte">shorte</option>
          </select>
          <button>Agregar</button>
        </form>

        <hr>
        <h3>👥 Cuentas y estadísticas</h3>
        <ul>
        {% for c in cuentas %}
          <li><b>{{ c.id }}</b> — Tokens generados: {{ estadisticas_cuenta[c.id] }}</li>
        {% endfor %}
        </ul>

        <hr>
        <h3>⏰ Programación automática</h3>
        <p>El bot se ejecutará cada <b>{{ interval }}</b> minutos para todos los enlaces.</p>

        <hr>
        <a href="{{ url_for('estadisticas') }}">📊 Ver estadísticas distribuidas</a> &nbsp;|&nbsp;
        <a href="{{ url_for('logout') }}">🚪 Cerrar sesión</a>

        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <ul style="color: green;">
              {% for msg in messages %}
                <li>{{ msg }}</li>
              {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
    """",
    enlaces=enlaces,
    cuentas=cuentas,
    estadisticas_cuenta=estadisticas_cuenta,
    interval=interval)

@app.route("/agregar", methods=["POST"])
@requiere_login
def agregar():
    url = request.form.get("url")
    tipo = request.form.get("tipo")
    enlaces = leer_enlaces()
    if not any(e["url"] == url for e in enlaces):
        enlaces.append({"url": url, "tipo": tipo, "visitas": 0})
        guardar_enlaces(enlaces)
    return redirect("/panel")

@app.route("/eliminar")
@requiere_login
def eliminar():
    url = request.args.get("url")
    enlaces = [e for e in leer_enlaces() if e["url"] != url]
    guardar_enlaces(enlaces)
    return redirect("/panel")

@app.route("/iniciar")
@requiere_login
def iniciar():
    url = request.args.get("url")
    enlaces = leer_enlaces()
    cuentas = leer_cuentas()

    for e in enlaces:
        if e["url"] == url:
            e["visitas"] = e.get("visitas", 0) + 1
            guardar_enlaces(enlaces)
            if cuentas:
                cuenta = random.choice(cuentas)
            else:
                cuenta = None
            ejecutar_bot(e, cuenta)
            flash(f"Bot iniciado manual para: {url} (Cuenta: {cuenta['id'] if cuenta else 'sin_cuenta'})")
            break

    return redirect("/panel")

@app.route("/estadisticas")
@requiere_login
def estadisticas():
    enlaces = leer_enlaces()
    tokens = leer_tokens()

    conteo_enlace = defaultdict(int)
    conteo_cuenta = defaultdict(int)
    for t in tokens:
        conteo_enlace[t["url"]] += 1
        conteo_cuenta[t["cuenta"]] += 1

    return render_template_string("""
        <h2>📊 Estadísticas detalladas</h2>

        <h3>Por enlace:</h3>
        <ul>
        {% for enlace, total in conteo_enlace.items() %}
          <li><b>{{ enlace }}</b> — Tokens: {{ total }}</li>
        {% endfor %}
        </ul>

        <h3>Por cuenta:</h3>
        <ul>
        {% for cuenta, total in conteo_cuenta.items() %}
          <li><b>{{ cuenta }}</b> — Tokens: {{ total }}</li>
        {% endfor %}
        </ul>

        <a href="{{ url_for('panel') }}">⬅ Volver al panel</a>
    """,
    conteo_enlace=conteo_enlace,
    conteo_cuenta=conteo_cuenta)

buildCommand: "pip install -r requirements.txt"
    startCommand: "python main.py"
    envVars:
      - key: PYTHON_VERSION
        value: "3.10"
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
  - type: web
    name: bot-realista-monetizable
    env: python
    plan: free
    
