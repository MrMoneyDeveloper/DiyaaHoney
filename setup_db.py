import os
import bcrypt
from sqlalchemy import create_engine
from db_utils import metadata, users

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///diyaa.db")
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

DEFAULT_USERNAME = os.getenv("ADMIN_USER", "admin")
DEFAULT_PASSWORD = os.getenv("ADMIN_PASS", "admin")

with engine.begin() as conn:
    result = conn.execute(users.select().where(users.c.username == DEFAULT_USERNAME)).fetchone()
    if not result:
        hashed = bcrypt.hashpw(DEFAULT_PASSWORD.encode(), bcrypt.gensalt()).decode()
        conn.execute(users.insert().values(username=DEFAULT_USERNAME, password=hashed, role="admin"))
        print(f"Created default admin user '{DEFAULT_USERNAME}' with password '{DEFAULT_PASSWORD}'")
    else:
        print("Admin user already exists")
