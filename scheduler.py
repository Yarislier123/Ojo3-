import time
import subprocess
import json
import random
from proxy_utils import obtener_proxy

def leer_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def escribir_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def bucle_programado():
    cfg = leer_json("config.json", {})
    interval = cfg.get("interval_minutes", 15)

    while True:
        enlaces = leer_json("enlaces.json", [])
        cuentas = leer_json("cuentas.json", [])
        for enlace_obj in enlaces:
            url = enlace_obj.get("url")
            tipo = enlace_obj.get("tipo")
            if cuentas:
                cuenta = random.choice(cuentas)
                cuenta_id = cuenta.get("id")
                token_cuenta = cuenta.get("token", "")
                proxy_cuenta = cuenta.get("proxy")
                proxy = proxy_cuenta or obtener_proxy()
            else:
                cuenta_id = "sin_cuenta"
                token_cuenta = ""
                proxy = obtener_proxy()

            subprocess.Popen([
                "python", "skip_ad_simulation.py",
                url,
                tipo,
                token_cuenta,
                proxy or "None"
            ])

            enlace_obj["visitas"] = enlace_obj.get("visitas", 0) + 1

        escribir_json("enlaces.json", enlaces)
        time.sleep(interval * 60)

if __name__ == "__main__":
    bucle_programado()
