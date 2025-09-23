from pathlib import Path

path = Path("dashboard.py")
text = path.read_text()
text = text.replace("\r\n\\r\\n", "\r\n\r\n")
text = text.replace("\n\n\n\n", "\n\n")
path.write_text(text)
