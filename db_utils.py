import os
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, ForeignKey, text
from sqlalchemy.engine import Engine

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

metadata.create_all(engine)


def insert_connection(ip: str, port: int, ts: datetime, user_id: Optional[int] = None) -> None:
    with engine.begin() as conn:
        conn.execute(
            connections.insert().values(ip=ip, port=port, ts=ts, user_id=user_id)
        )


def insert_alert(ip: str, message: str, ts: datetime) -> None:
    with engine.begin() as conn:
        conn.execute(
            alerts.insert().values(ip=ip, message=message, ts=ts)
        )


__all__ = [
    "engine",
    "insert_connection",
    "insert_alert",
    "users",
    "connections",
    "alerts",
    "metadata",
]
