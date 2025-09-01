# DiyaaHoney

## Quick Start for Group Members
```bash
git clone <repo-url>
cd DiyaaHoney
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python honeypot.py &
python intrusion_detector.py &
python dashboard.py
```

### Database setup
The application uses SQLite by default. On startup it checks the database
connection and creates the database file, required tables and a default
administrator account if they are missing.

If your system does not have SQLite, you can download it from
[sqlite.org](https://sqlite.org/download.html).

You can run `python setup_db.py` manually to perform the initialization at
any time.

### Auto sign-in
The dashboard automatically signs in using the default administrator account.
By default this account uses the username `admin` with password `admin`, so no
manual login is required. Navigating to the dashboard will log you in
automatically with these credentials.

### Other scripts
- `generate_fake_hits.sh` – send 10 test connections
- `tests/test_db.py` – run with `pytest`
