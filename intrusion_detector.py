# intrusion_detector.py
"""
Watches honeypot.log, counts connection attempts per IP, and—once the
threshold is reached—sends a *single* aggregated alert (email + MQTT +
LED-print) per offending IP.  All IDS activity is written to alerts.log.
"""

import time
import re
import logging
from alerts import send_email_alert, send_mqtt_alert, trigger_led

# ── CONFIGURATION ────────────────────────────────────────────────────────────
THRESHOLD       = 3          # attempts before alert fires
CHECK_INTERVAL  = 5          # seconds between log sweeps
LOG_FILE        = "honeypot.log"
ALERTS_LOG_FILE = "alerts.log"
# ─────────────────────────────────────────────────────────────────────────────

# Logging: console + file so dashboard can read alerts.log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(ALERTS_LOG_FILE),
        logging.StreamHandler()
    ]
)

class IntrusionDetector:
    def __init__(self, threshold: int = THRESHOLD) -> None:
        self.threshold      = threshold
        self.alerted_ips    = set()
        self.file_position  = 0               # where we left off in honeypot.log

    # ── Private helpers ────────────────────────────────────────────────────
    def _read_new_lines(self) -> list[str]:
        """Return any new lines appended to honeypot.log since last read."""
        try:
            with open(LOG_FILE, "r") as f:
                f.seek(self.file_position)
                new_data       = f.read()
                self.file_position = f.tell()
        except FileNotFoundError:
            return []
        return new_data.splitlines()

    def _count_attempts(self) -> dict[str, int]:
        """Return total attempt count per IP in the entire log (quick scan)."""
        counts: dict[str, int] = {}
        try:
            with open(LOG_FILE) as f:
                for line in f:
                    # Matches “Connection from 192.168.1.10:54321”
                    m = re.search(r"from ([0-9.]+)", line)
                    if m:
                        ip = m.group(1)
                        counts[ip] = counts.get(ip, 0) + 1
        except FileNotFoundError:
            pass
        return counts

    # ── Main check cycle ───────────────────────────────────────────────────
    def _process(self) -> None:
        # Display new log lines in real time
        for entry in self._read_new_lines():
            logging.info(f"New log entry: {entry}")

        # Evaluate intrusion counts
        for ip, total in self._count_attempts().items():
            if total >= self.threshold and ip not in self.alerted_ips:
                msg = f"{total} failed attempts detected from {ip}"
                send_email_alert(msg)         # real email (alerts.py)
                send_mqtt_alert(msg)          # stub / simulated MQTT
                trigger_led(msg)              # stub / simulated LED/Buzzer
                logging.warning(f"Alert triggered for {ip}: {total} attempts")
                self.alerted_ips.add(ip)

    # ── Public entry point ─────────────────────────────────────────────────
    def run(self, interval: int = CHECK_INTERVAL) -> None:
        logging.info("📡 Intrusion Detector started")
        try:
            while True:
                self._process()
                time.sleep(interval)
        except KeyboardInterrupt:
            logging.info("Intrusion Detector stopped by user")


if __name__ == "__main__":
    IntrusionDetector().run()
