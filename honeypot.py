# honeypot.pypython honeypot.py
"""Simple TCP honeypot that logs every connection to **honeypot.log** (file) and
stdout, then fires real‑time alert functions.

Changes:
1. File path is absolute – guarantees the log is created in the same folder as
   this script, no matter where you launch Python from.
2. `RotatingFileHandler` (max 1 MB, up to 5 backups) so the log never grows
   unbounded.
3. Explicit `logger = logging.getLogger("honeypot")` to avoid clashing with
   other logging configs.
"""

import os
import socket
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from alerts import send_email_alert, send_mqtt_alert, trigger_led

# ── Paths ────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(BASE_DIR, "honeypot.log")

# ── Logger configuration ─────────────────────────────────────────────────
logger = logging.getLogger("honeypot")
logger.setLevel(logging.INFO)

# File handler (rotating)
file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=1_000_000, backupCount=5)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(console_handler)

# ── Honeypot settings ────────────────────────────────────────────────────
HOST       = "0.0.0.0"
PORT       = 2222
MAX_CONNS  = 5
BANNER     = b"SSH-2.0-Honeypot_1.0\r\n"

# ── Helper function ──────────────────────────────────────────────────────

def handle_client(client_sock: socket.socket, addr):
    ip, port = addr
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        logger.info(f"Connection from {ip}:{port}")
        client_sock.sendall(BANNER)
        alert_msg = f"Connection from {ip}:{port} at {timestamp}"
        send_email_alert(alert_msg)   # real email via alerts.py
        send_mqtt_alert(alert_msg)    # stub / simulated MQTT
        trigger_led(alert_msg)        # stub / simulated LED/Buzzer
    except Exception as exc:
        logger.error(f"Error handling {ip}:{port}: {exc}")
    finally:
        client_sock.close()

# ── Main ─────────────────────────────────────────────────────────────────

def start_honeypot(host: str = HOST, port: int = PORT) -> None:
    """Bind to <host>:<port> and run indefinitely until Ctrl‑C."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(MAX_CONNS)
        logger.info(f"Honeypot listening on {host}:{port}")
        try:
            while True:
                client, addr = srv.accept()
                handle_client(client, addr)
        except KeyboardInterrupt:
            logger.info("Stopping honeypot gracefully…")

if __name__ == "__main__":
    start_honeypot()
