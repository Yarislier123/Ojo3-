import sys
import time
import random
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from proxy_utils import obtener_proxy

"""
Simulador de visitas en Adfly/Shorte.
Acepta 4 argumentos:
  1) url (string)
  2) tipo (adfly|shorte)
  3) token_cuenta (string)
  4) proxy (string) -- cadena de proxy o None
"""

def main():
    if len(sys.argv) < 5:
        print("❌ Uso: python skip_ad_simulation.py <url> <tipo> <token_cuenta> <proxy>")
        sys.exit(1)

    url = sys.argv[1]
    tipo = sys.argv[2].lower()
    token_cuenta = sys.argv[3]
    proxy_arg = sys.argv[4]
    proxy = proxy_arg if proxy_arg and proxy_arg.lower() != "none" else None

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 10) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100 Mobile Safari/537.36")

    if proxy:
        options.add_argument(f"--proxy-server={proxy}")

    driver = webdriver.Chrome(options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
      "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = {runtime: {}};
        Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
      """
    })

    try:
        driver.get(url)
        time.sleep(random.uniform(6, 10))

        if tipo == "adfly":
            if "skip" in driver.page_source.lower():
                pass
        elif tipo == "shorte":
            time.sleep(random.uniform(5, 10))
            pass
        else:
            print("❓ Plataforma desconocida")
            driver.quit()
            sys.exit(1)

        raw = f"{url}-{token_cuenta}-{time.time()}".encode()
        token_md5 = hashlib.md5(raw).hexdigest()
        print(token_md5)

    except Exception as e:
        print("❌ Error durante la simulación:", str(e))

    driver.quit()
    print("⏹️ Simulación completada")


if __name__ == "__main__":
    main()
