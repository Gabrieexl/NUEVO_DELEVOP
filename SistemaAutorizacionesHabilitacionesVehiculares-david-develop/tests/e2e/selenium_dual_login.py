"""
Abre dos sesiones Selenium en paralelo para validar permisos por rol.

Uso basico:
  python tests/e2e/selenium_dual_login.py ^
    --base-url http://127.0.0.1:8000 ^
    --admin-user admin --admin-pass testpass123 --admin-path /admin/ ^
    --consulta-user consulta --consulta-pass testpass123 --consulta-path /consulta/placa/

Notas:
- Debes tener el servidor Django ejecutandose.
- Si quieres, deja la ruta por defecto luego del login para observar ambas sesiones.
"""

from __future__ import annotations

import argparse
import threading
import time
import tempfile
import shutil
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@dataclass
class SessionConfig:
    name: str
    username: str
    password: str
    target_path: str


def _build_driver(headless: bool, profile_dir: str, browser: str):
    if browser == "edge":
        options = EdgeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument(f"--user-data-dir={profile_dir}")
        return webdriver.Edge(options=options)

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(f"--user-data-dir={profile_dir}")
    return webdriver.Chrome(options=options)


def _login_and_open(
    base_url: str,
    config: SessionConfig,
    headless: bool,
    keep_open_seconds: int,
    errors: list[str],
    browser: str,
) -> None:
    driver = None
    profile_dir = tempfile.mkdtemp(prefix=f"selenium-{config.name.lower()}-")
    try:
        driver = _build_driver(headless=headless, profile_dir=profile_dir, browser=browser)
        wait = WebDriverWait(driver, 15)

        login_url = urljoin(base_url, "/usuarios/login/")
        target_url = urljoin(base_url, config.target_path)

        driver.get(login_url)
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(config.username)
        wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(config.password)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()

        # Espera a que salga del login. Si no redirige, se asume credenciales invalidas.
        wait.until(lambda d: "/usuarios/login/" not in d.current_url)

        driver.get(target_url)
        print(f"[{config.name}] OK -> {driver.current_url}")

        if keep_open_seconds > 0:
            time.sleep(keep_open_seconds)
        elif not headless:
            # Modo observacion manual: mantener abierto hasta Ctrl+C.
            while True:
                time.sleep(1)

    except TimeoutException as exc:
        errors.append(f"[{config.name}] timeout/login fallo: {exc}")
    except Exception as exc:  # pragma: no cover - utilidad manual
        errors.append(f"[{config.name}] error: {exc}")
    finally:
        if driver is not None:
            driver.quit()
        shutil.rmtree(profile_dir, ignore_errors=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Abre sesion admin y consulta en paralelo con Selenium."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")

    parser.add_argument("--admin-user", required=True)
    parser.add_argument("--admin-pass", required=True)
    parser.add_argument("--admin-path", default="/admin/")

    parser.add_argument("--consulta-user", required=True)
    parser.add_argument("--consulta-pass", required=True)
    parser.add_argument("--consulta-path", default="/consulta/placa/")

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Ejecuta sin UI (no recomendado para observacion manual).",
    )
    parser.add_argument(
        "--keep-open-seconds",
        type=int,
        default=0,
        help="Segundos a mantener abiertas las ventanas. 0 = hasta Ctrl+C en modo no headless.",
    )
    parser.add_argument(
        "--browser",
        choices=["edge", "chrome"],
        default="edge",
        help="Navegador a usar en ambas sesiones.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []

    admin_cfg = SessionConfig(
        name="ADMIN",
        username=args.admin_user,
        password=args.admin_pass,
        target_path=args.admin_path,
    )
    consulta_cfg = SessionConfig(
        name="CONSULTA",
        username=args.consulta_user,
        password=args.consulta_pass,
        target_path=args.consulta_path,
    )

    t1 = threading.Thread(
        target=_login_and_open,
        args=(args.base_url, admin_cfg, args.headless, args.keep_open_seconds, errors, args.browser),
        daemon=False,
    )
    t2 = threading.Thread(
        target=_login_and_open,
        args=(args.base_url, consulta_cfg, args.headless, args.keep_open_seconds, errors, args.browser),
        daemon=False,
    )

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    if errors:
        print("\nErrores detectados:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("\nSesiones completadas sin errores.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
