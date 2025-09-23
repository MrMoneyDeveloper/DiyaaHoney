# DiyaaHoney

## Quick Start

### Windows (PowerShell)
```powershell
git clone <repo-url>
cd DiyaaHoney
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python setup_db.py
Start-Process powershell -WorkingDirectory $PWD -ArgumentList '-NoExit','-Command','.\venv\Scripts\python.exe honeypot.py'
Start-Process powershell -WorkingDirectory $PWD -ArgumentList '-NoExit','-Command','.\venv\Scripts\python.exe intrusion_detector.py'
.\venv\Scripts\python.exe dashboard.py
```
The dashboard listens on <http://127.0.0.1:5000/>. Visit <http://127.0.0.1:5000/login>, leave the pre-filled admin credentials in place, and press **Login** to enter the UI.

### Linux / macOS / Git Bash
```bash
git clone <repo-url>
cd DiyaaHoney
python3 -m venv venv
source venv/bin/activate  # Git Bash on Windows: source venv/Scripts/activate
pip install -r requirements.txt
python setup_db.py
python honeypot.py &
python intrusion_detector.py &
python dashboard.py
```
After the last command browse to <http://127.0.0.1:5000/login>, submit the pre-filled form, and then use <http://127.0.0.1:5000/> for the dashboard. Use `fg` or `Ctrl+C` to stop the services when finished.

### Stop the services
- Press `Ctrl+C` in each PowerShell window that was started.
- On Linux/macOS or Git Bash, `fg` the background processes and `Ctrl+C`, or run `kill %1 %2`.

## Database setup
The application uses SQLite by default. On startup it checks the database
connection and creates the database file, required tables and a default
administrator account if they are missing.

If your system does not have SQLite, you can download it from
[sqlite.org](https://sqlite.org/download.html).

You can run `python setup_db.py` manually to perform the initialization at
any time.

## Authentication
- Default credentials are `admin` / `admin`. The login page loads with these values pre-filled so you can simply press **Login**.
- Once signed in as an admin you can open <http://127.0.0.1:5000/users> (or the **Users** navigation link) to add new accounts. Newly created users can sign in with their chosen role immediately.

## Other scripts
- `generate_fake_hits.sh` - send 10 test connections
- `tests/test_db.py` - run with `pytest`

## Performance tips

- Compression: flask-compress is included in requirements.txt and is auto-enabled if installed.
- Stable dev runs: disable reloader and debug for consistent timings: FLASK_DEBUG=0 python dashboard.py
- Static caching: enabled for 24h; after CSS/JS changes, hard-refresh or bust cache.
- APIs: send Cache-Control: no-store to avoid stale results for live feeds.
