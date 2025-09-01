# DiyaaHoney

## Quick Start for Group Members
```bash
git clone <repo-url>
cd DiyaaHoney
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup_db.py  # creates default admin
python honeypot.py &
python intrusion_detector.py &
python dashboard.py
```

### Other scripts
- `generate_fake_hits.sh` – send 10 test connections
- `tests/test_db.py` – run with `pytest`
