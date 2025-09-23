import os
import random
import time
from datetime import datetime
from pathlib import Path
import bcrypt
from flask import (
    Blueprint,
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    abort,
    flash,
    make_response,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    UserMixin,
    current_user,
)
try:
    from flask_compress import Compress
except Exception:
    Compress = None
from sqlalchemy import text, select, func
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import IntegrityError
from db_utils import engine, connections, users

bp = Blueprint("dashboard", __name__, template_folder="templates")
login_manager = LoginManager()
login_manager.login_view = "dashboard.login"


def _safe_next_url() -> str:
    candidate = request.args.get("next") or request.form.get("next")
    if candidate and candidate.startswith("/"):
        return candidate
    return ""




class User(UserMixin):
    def __init__(self, id: int, username: str, password: str, role: str) -> None:
        self.id = id
        self.username = username
        self.password = password
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'


def _row_to_user(row) -> User:
    return User(row["id"], row["username"], row["password"], row["role"])


@login_manager.user_loader
def load_user(user_id: str):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM users WHERE id = :id"), {"id": int(user_id)}
        ).mappings().first()
    return _row_to_user(row) if row else None


@bp.route("/login", methods=["GET", "POST"])
def login():
    default_username = os.getenv("ADMIN_USER", "admin")
    default_password = os.getenv("ADMIN_PASS", "admin")
    next_url = _safe_next_url()
    if request.method == "POST":
        username_value = (request.form.get("username") or "").strip()
        password_value = request.form.get("password") or ""
        if username_value and password_value:
            with engine.connect() as conn:
                row = conn.execute(
                    text("SELECT * FROM users WHERE username = :u"), {"u": username_value}
                ).mappings().first()
            if row and bcrypt.checkpw(password_value.encode(), row["password"].encode()):
                login_user(_row_to_user(row))
                flash("Logged in successfully.", "success")
                target = next_url or url_for("dashboard.dashboard")
                return redirect(target)
        flash("Invalid username or password.", "error")
    else:
        username_value = default_username
        password_value = default_password
    return render_template(
        "login.html",
        username_value=username_value,
        password_value=password_value,
        next=next_url,
    )


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("dashboard.login"))


@bp.route("/home")
@login_required
def home():
    return render_template("home.html")


@bp.route("/api/hits")
@login_required
def api_hits():
    data = [
        {"ip": f"192.168.1.{random.randint(1,254)}", "hits": random.randint(1,100)}
        for _ in range(5)
    ]
    resp = make_response(jsonify(data))
    resp.headers["Cache-Control"] = "no-store, max-age=0"
    return resp


@bp.route("/hits")
@login_required
def hits():
    return render_template("hits.html")


@bp.route("/")
@login_required
def dashboard():
    ip = request.args.get("ip")
    start = request.args.get("start")
    end = request.args.get("end")
    alert_only = request.args.get("alert_only")

    filters = []
    params = {}
    if ip:
        filters.append("c.ip = :ip")
        params["ip"] = ip
    if start:
        filters.append("c.ts >= :start")
        params["start"] = start
    if end:
        filters.append("c.ts <= :end")
        params["end"] = end
    if alert_only:
        filters.append("a.id IS NOT NULL")

    where = "WHERE " + " AND ".join(filters) if filters else ""
    query = text(
        """SELECT c.ip, c.port, c.ts, a.message
               FROM connections c
               LEFT JOIN alerts a ON c.ip = a.ip
               %s
               ORDER BY c.ts DESC
               LIMIT 500""" % where
    )
    with engine.connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return render_template("dashboard.html", rows=rows, user=current_user)


@bp.route("/dashboard/forecast")
@login_required
def forecast():
    return render_template("forecast.html")


@bp.route("/api/stats")
@login_required
def api_stats():
    ip = request.args.get("ip")
    # Support both legacy (start/end) and new (start_date/end_date) params
    start = request.args.get("start_date") or request.args.get("start")
    end = request.args.get("end_date") or request.args.get("end")
    stmt = select(connections.c.ip, func.count().label("hits")).group_by(connections.c.ip)
    if ip:
        stmt = stmt.where(connections.c.ip == ip)
    if start:
        try:
            stmt = stmt.where(connections.c.ts >= datetime.fromisoformat(start))
        except ValueError:
            pass
    if end:
        try:
            stmt = stmt.where(connections.c.ts <= datetime.fromisoformat(end))
        except ValueError:
            pass
    with engine.connect() as conn:
        rows = conn.execute(stmt).all()
    resp = make_response(jsonify([{"ip": r.ip, "hits": r.hits} for r in rows]))
    resp.headers["Cache-Control"] = "no-store, max-age=0"
    return resp


@bp.route("/charts")
@login_required
def charts():
    return render_template("charts.html")


@bp.route("/users")
@login_required
def manage_users():
    if not getattr(current_user, "is_admin", False):
        abort(403)

    with engine.connect() as conn:
        existing_users = conn.execute(
            text("SELECT id, username, role FROM users ORDER BY username")
        ).mappings().all()

    return render_template(
        "users.html",
        users=existing_users,
    )


@bp.route("/users/create", methods=["GET", "POST"])
@login_required
def create_user():
    if not getattr(current_user, "is_admin", False):
        abort(403)

    form_username = ""
    form_role = "viewer"

    if request.method == "POST":
        form_username = (request.form.get("username") or "").strip()
        form_password = request.form.get("password") or ""
        form_role = (request.form.get("role") or "viewer").strip().lower()
        allowed_roles = {"admin", "viewer"}
        if form_role not in allowed_roles:
            form_role = "viewer"

        if not form_username or not form_password:
            flash("Username and password are required.", "error")
        else:
            hashed = bcrypt.hashpw(form_password.encode(), bcrypt.gensalt()).decode()
            try:
                with engine.begin() as conn:
                    conn.execute(
                        users.insert().values(
                            username=form_username,
                            password=hashed,
                            role=form_role,
                        )
                    )
            except IntegrityError:
                flash(f"User '{form_username}' already exists.", "error")
            else:
                flash(f"User '{form_username}' created.", "success")
                return redirect(url_for("dashboard.manage_users"))

    return render_template(
        "user_create.html",
        form_username=form_username,
        form_role=form_role,
    )


@bp.route("/dbgui", methods=["GET", "POST"])
@login_required
def dbgui():
    # Restrict to admin role
    if getattr(current_user, "role", "viewer") != "admin":
        abort(403)
    # List tables via SQLAlchemy inspector
    tables = sa_inspect(engine).get_table_names()
    query = None
    rows = None
    if request.method == "POST":
        query = (request.form.get("query") or "").strip()
        if query:
            if query.lower().startswith("select"):
                try:
                    with engine.connect() as conn:
                        result = conn.execute(text(query))
                        rows = result.mappings().fetchmany(100)
                except Exception as ex:
                    flash(f"Error executing query: {ex}", "error")
            else:
                flash("Only SELECT statements are allowed.", "error")
    return render_template("dbgui.html", tables=tables, rows=rows, query=query)


def create_app() -> Flask:
    app = Flask(__name__)
    secret = os.getenv("SECRET_KEY")
    if not secret:
        secret = os.urandom(32)
    app.secret_key = secret
    # Static caching + small JSON speedups
    if os.getenv("FLASK_DEBUG", "0") == "1":
        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    else:
        app.config.setdefault("SEND_FILE_MAX_AGE_DEFAULT", 60 * 60 * 24)  # 24h
    app.config.setdefault("JSONIFY_PRETTYPRINT_REGULAR", False)
    app.config.setdefault("TEMPLATES_AUTO_RELOAD", False)
    login_manager.init_app(app)
    app.register_blueprint(bp)

    asset_versions = {}
    static_folder = Path(app.static_folder) if app.static_folder else None

    @app.context_processor
    def inject_asset_url():
        def asset_url(filename: str) -> str:
            version = asset_versions.get(filename)
            if version is None:
                if static_folder:
                    file_path = static_folder / filename
                    if file_path.exists():
                        version = str(int(file_path.stat().st_mtime))
                    else:
                        version = str(int(time.time()))
                else:
                    version = str(int(time.time()))
                asset_versions[filename] = version
            return url_for('static', filename=filename, v=version)

        return {"asset_url": asset_url, "current_year": datetime.utcnow().year}

    # Enable gzip/brotli if available
    if Compress is not None:
        try:
            Compress(app)
        except Exception:
            pass
    return app


if __name__ == "__main__":
    # For a snappier dev experience, disable reloader and debug unless explicitly enabled
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    create_app().run(debug=debug, use_reloader=False, threaded=True)



