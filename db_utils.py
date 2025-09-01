import os
import random
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, OperationalError

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///diyaa.db")
engine: Engine = create_engine(DATABASE_URL)
metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, unique=True, nullable=False),
    Column("password", String, nullable=False),
    Column("role", String, nullable=False, default="viewer"),
)

connections = Table(
    "connections",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("ip", String, nullable=False),
    Column("port", Integer, nullable=False),
    Column("ts", DateTime, nullable=False, default=datetime.utcnow),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
)

alerts = Table(
    "alerts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("ip", String, nullable=False),
    Column("message", String, nullable=False),
    Column("ts", DateTime, nullable=False, default=datetime.utcnow),
)


def init_db(verbose: bool = False) -> None:
    """Ensure database exists and has a default admin user.

    If the connection fails, a new database file is created along with the
    required tables and a default admin account.
    """

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        # If the database does not exist, create it
        pass

    metadata.create_all(engine)

    default_username = os.getenv("ADMIN_USER", "admin")
    default_password = os.getenv("ADMIN_PASS", "admin")

    # Attempt to insert the default admin user in a single transaction.
    # If another process inserts the same user concurrently, the UNIQUE
    # constraint on the username will raise an IntegrityError which we can
    # safely ignore.
    hashed = bcrypt.hashpw(default_password.encode(), bcrypt.gensalt()).decode()
    with engine.begin() as conn:
        try:
            conn.execute(
                users.insert().values(
                    username=default_username,
                    password=hashed,
                    role="admin",
                )
            )
            if verbose:
                print(
                    f"Created default admin user '{default_username}' with password '{default_password}'"
                )
        except IntegrityError:
            if verbose:
                print("Admin user already exists")

    # Ensure demo users and sample 2025 data exist for the dashboard
    seed_demo_users(verbose=verbose)
    seed_demo_data_2025(verbose=verbose)


def insert_connection(ip: str, port: int, ts: datetime, user_id: Optional[int] = None) -> None:
    with engine.begin() as conn:
        conn.execute(
            connections.insert().values(ip=ip, port=port, ts=ts, user_id=user_id)
        )


def insert_alert(ip: str, message: str, ts: datetime) -> None:
    with engine.begin() as conn:
        conn.execute(alerts.insert().values(ip=ip, message=message, ts=ts))


__all__ = [
    "engine",
    "insert_connection",
    "insert_alert",
    "users",
    "connections",
    "alerts",
    "metadata",
    "init_db",
]
# --- Demo/seed helpers -----------------------------------------------------

def _ensure_user(username: str, role: str, password: str = "admin") -> int:
    """Ensure a user exists and return its id."""
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with engine.begin() as conn:
        try:
            conn.execute(
                users.insert().values(username=username, password=hashed, role=role)
            )
        except IntegrityError:
            pass
        row = conn.execute(
            text("SELECT id FROM users WHERE username = :u"), {"u": username}
        ).mappings().first()
        return int(row["id"]) if row else 0


def seed_demo_users(verbose: bool = False) -> None:
    """Create a couple of non-admin users if missing."""
    _ensure_user("analyst", "viewer", password="analyst")
    _ensure_user("viewer", "viewer", password="viewer")
    if verbose:
        print("Ensured demo users 'analyst' and 'viewer'.")


def seed_demo_data_2025(verbose: bool = False) -> None:
    """Populate the database with synthetic 2025 data if it's sparse.

    - Spreads connection events throughout 2025 with daily variance.
    - Adds a few alerts for heavy-hitter IPs.
    - Keeps dataset reasonable in size (~3-5k rows) and idempotent.
    """

    start_2025 = datetime(2025, 1, 1)
    start_2026 = datetime(2026, 1, 1)

    with engine.connect() as conn:
        existing = conn.execute(
            text(
                "SELECT COUNT(*) FROM connections WHERE ts >= :s AND ts < :e"
            ),
            {"s": start_2025, "e": start_2026},
        ).scalar_one()

    # If we already have a healthy dataset, do nothing
    if existing and existing >= 1500:
        if verbose:
            print(f"2025 demo data present: {existing} connections")
        return

    if verbose:
        print("Seeding 2025 demo data (connections + alerts)...")

    # Users for linking (optional)
    admin_id = _ensure_user(os.getenv("ADMIN_USER", "admin"), "admin", password=os.getenv("ADMIN_PASS", "admin"))
    analyst_id = _ensure_user("analyst", "viewer", password="analyst")
    viewer_id = _ensure_user("viewer", "viewer", password="viewer")
    user_ids = [admin_id, analyst_id, viewer_id]

    # IP pools and weights (some heavy hitters)
    heavy_ips = [
        "203.0.113.10",
        "203.0.113.23",
        "198.51.100.77",
        "198.51.100.88",
    ]
    normal_ips = [f"192.168.1.{i}" for i in range(2, 50)] + [f"10.0.0.{i}" for i in range(2, 50)]
    ports = [22, 23, 80, 443, 3389, 8080, 1883]

    rng = random.Random(42)
    total_days = (start_2026 - start_2025).days
    rows = []
    alerts_rows = []

    for d in range(total_days):
        day = start_2025 + timedelta(days=d)
        # Weekends quieter, midweek busier
        base = 6 if day.weekday() >= 5 else 12
        # Seasonal variance (summer slightly higher)
        if day.month in (6, 7, 8):
            base += 4
        # Random jitter
        count = base + rng.randint(0, 8)

        # Inject occasional spikes for heavy IPs -> alerts
        spike = rng.random() < 0.08
        if spike:
            count += 25 + rng.randint(0, 20)
            ip_spiker = rng.choice(heavy_ips)
        else:
            ip_spiker = None

        for _ in range(count):
            if ip_spiker and rng.random() < 0.5:
                ip = ip_spiker
            else:
                ip = rng.choice(heavy_ips if rng.random() < 0.15 else normal_ips)
            port = rng.choice(ports)
            ts = day + timedelta(seconds=rng.randint(0, 86399))
            uid = rng.choice(user_ids) if rng.random() < 0.4 else None
            rows.append({"ip": ip, "port": port, "ts": ts, "user_id": uid})

        # Record an alert if a heavy ip spiked
        if ip_spiker:
            alerts_rows.append(
                {"ip": ip_spiker, "message": "Excessive connection attempts detected", "ts": day}
        )

    # Insert in batches
    with engine.begin() as conn:
        # Clear only if entirely empty for 2025? We do additive inserts.
        if rows:
            conn.execute(connections.insert(), rows)
        if alerts_rows:
            conn.execute(alerts.insert(), alerts_rows)

    if verbose:
        print(
            f"Seeded {len(rows)} connections and {len(alerts_rows)} alerts for 2025."
        )


# Initialize on import
init_db()
