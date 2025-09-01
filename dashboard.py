import os
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
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    UserMixin,
    current_user,
)
from sqlalchemy import text, select, func
from db_utils import engine, connections

bp = Blueprint("dashboard", __name__, template_folder="templates")
login_manager = LoginManager()
login_manager.login_view = "dashboard.login"


class User(UserMixin):
    def __init__(self, id: int, username: str, password: str, role: str) -> None:
        self.id = id
        self.username = username
        self.password = password
        self.role = role


def _row_to_user(row) -> User:
    return User(row["id"], row["username"], row["password"], row["role"])


@login_manager.user_loader
def load_user(user_id: str):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM users WHERE id = :id"), {"id": int(user_id)}
        ).mappings().first()
    return _row_to_user(row) if row else None


@bp.route("/login")
def login():
    default_username = os.getenv("ADMIN_USER", "admin")
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM users WHERE username = :u"), {"u": default_username}
        ).mappings().first()
    if not row:
        return "Default admin user not found", 500
    login_user(_row_to_user(row))
    return redirect(url_for("dashboard.dashboard"))


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("dashboard.login"))


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
               ORDER BY c.ts DESC""" % where
    )
    with engine.connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return render_template("dashboard.html", rows=rows, user=current_user)


@bp.route("/stats")
@login_required
def stats():
    stmt = (
        select(connections.c.ip, func.count().label("hits"))
        .group_by(connections.c.ip)
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt).all()
    return jsonify([{"ip": row.ip, "hits": row.hits} for row in rows])


@bp.route("/charts")
@login_required
def charts():
    return render_template("charts.html")


@bp.route("/query", methods=["GET", "POST"])
@login_required
def query():
    if current_user.role != "admin":
        abort(403)
    sql = request.form.get("sql")
    rows = headers = None
    if request.method == "POST" and sql:
        try:
            with engine.connect() as conn:
                result = conn.execute(text(sql))
                headers = result.keys()
                rows = result.fetchall()
        except Exception as e:
            flash(str(e), "danger")
    return render_template("query.html", rows=rows, headers=headers, sql=sql or "")


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "devkey")
    login_manager.init_app(app)
    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
