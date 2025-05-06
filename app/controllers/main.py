from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app import db
from app.models.models import User, Fast, FastHistory
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import math

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("main.login"))
        user_id = session["user_id"]
        user = User.query.get(user_id)
        if user is None:
            session.pop("user_id", None)
            return redirect(url_for("main.login"))
        return f(*args, **kwargs)
    return decorated_function

def update_fast(active_fast, form_data):
    new_start_time = form_data.get("start_time")
    new_hours_planned = form_data.get("hours_planned", type=int)
    new_status = form_data.get("status")

    try:
        if new_start_time:
            new_start = datetime.strptime(new_start_time, "%Y-%m-%dT%H:%M")
            if new_start > datetime.now():
                flash("Start time cannot be in the future", "error")
                return False
            active_fast.start_time = new_start

        if new_hours_planned is not None:
            if not (0 < new_hours_planned <= 24):
                flash("Planned duration must be between 1 and 24 hours.", "error")
                return False
            active_fast.hours_planned = new_hours_planned

        if new_status:
            active_fast.status = new_status.strip() or None

        db.session.commit()
        return True
    except ValueError:
        flash("Invalid date format. Use YYYY-MM-DD HH:MM", "error")
        return False

main_bp = Blueprint("main", __name__)

@main_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    user_id = session["user_id"]
    active_fast = Fast.query.filter_by(user_id=user_id, end_time=None).first()
    if request.method == "POST":
        window = request.form.get("fasting_window")
        if window in ["12", "14", "16"]:
            hours = int(window)
            new_fast = Fast(user_id=user_id, start_time=datetime.now(), hours_planned=hours)
            db.session.add(new_fast)
            db.session.commit()
            print(f"Debug: Redirecting to timer with hours = {hours}")
            return redirect(url_for("main.timer", hours=hours))
        return "Pick 12, 14, or 16 hours - keep it chill!"
    
    if active_fast:
        if active_fast.end_time:
            remaining_hours = (active_fast.end_time - datetime.now()).total_seconds() / 3600
            if datetime.now() < active_fast.end_time:
                print(f"Debug: Redirecting to timer with remaining_hours = {remaining_hours}")
                return redirect(url_for("main.timer", hours=remaining_hours))    
        else:
            print(f"Debug: Redirecting to timer with hours = {active_fast.hours_planned}")
            return redirect(url_for("main.timer", hours=active_fast.hours_planned))
            
    user = User.query.get(user_id)
    return render_template("index.html", consistency=user.completed_fasts_streak)

@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username and password and not User.query.filter_by(username=username).first():
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            session["user_id"] = new_user.id
            return redirect(url_for("main.index"))
        flash("Username taken or invalid input.", "error")
        return render_template("register.html")
    return render_template("register.html")

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("main.index"))
        flash("Invalid credentials.", "error")
        print("Flashed: Invalid credentials")
        return render_template("login.html")
    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("main.login"))

@main_bp.route("/timer", methods=["GET", "POST"])
@login_required
def timer():
    user_id = session["user_id"]
    active_fast = Fast.query.filter_by(user_id=user_id, end_time=None).first()
    if not active_fast:
        return redirect(url_for("main.index"))
    
    end_time = active_fast.start_time + timedelta(hours=active_fast.hours_planned)
    elapsed_time = datetime.now() - active_fast.start_time
    elapsed_hours = elapsed_time.total_seconds() / 3600
    remaining_hours = max(0, active_fast.hours_planned - elapsed_hours)

    circumference = 2 * math.pi * 45
    progress = elapsed_hours / active_fast.hours_planned if active_fast.hours_planned else 0
    stroke_dashoffset = circumference * (1-progress) if active_fast.hours_planned else circumference

    if request.method == "POST":
        return redirect(url_for("main.timer"))

    user = User.query.get(user_id)
    return render_template(
        "timer.html", 
        end_time=end_time.isoformat(),
        start_time=active_fast.start_time.isoformat(),
        hours=active_fast.hours_planned,
        elapsed_hours=elapsed_hours,
        remaining_hours=remaining_hours,
        consistency=user.completed_fasts_streak,
        status=active_fast.status,
        stroke_dashoffset=round(stroke_dashoffset, 2)
        )

@main_bp.route("/complete")
@login_required
def complete():
    user_id = session["user_id"]
    active_fast = Fast.query.filter_by(user_id=user_id, end_time=None).first()
    if active_fast:
        duration_hours = int((datetime.now() - active_fast.start_time).total_seconds() / 3600)
        hours_planned = int(request.args.get("hours", 0))
        print(f"User {user_id}: Completing fast - Duration: {duration_hours}h, Planned: {hours_planned}h")
        new_history = FastHistory(
            user_id=user_id,
            date=datetime.now(),
            duration_hours=duration_hours,
            hours_planned=hours_planned
        )
        active_fast.end_time = datetime.now()
        db.session.add(new_history)
        try: 
            db.session.commit()
            print(f"User {user_id}: Fast history recorded successfully")
        except Exception as e:
            db.session.rollback()
            print(f"User {user_id}: Error committing fast: {str(e)}")
            return f"Error recording fast: {str(e)}", 500
    else:
        print(f"User {user_id}: No active fast found")
    user = User.query.get(user_id)
    return redirect(url_for("main.index"))
    
@main_bp.route("/history", methods=["GET", "POST"])
@login_required
def history():
    user_id = session["user_id"]
    edit_id = request.args.get("edit", type=int)

    if request.method == "POST":
        fast_id = request.form.get("fast_id", type=int)
        fast = FastHistory.query.filter_by(user_id=user_id, id=fast_id).first_or_404()
        new_date = request.form.get("date")
        new_duration = request.form.get("duration_hours", type=int)
        new_planned = request.form.get("hours_planned", type=int)
        try:
            parsed_date = datetime.strptime(new_date, "%Y-%m-%d %H:%M")
            fast.date = parsed_date
            fast.duration_hours = new_duration
            fast.hours_planned = new_planned
            db.session.commit()
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD HH:MM.", "error")

        return redirect(url_for("main.history"))

    past_fasts = FastHistory.query.filter_by(user_id=user_id).all()
    return render_template("history.html", past_fasts=past_fasts, edit_id=edit_id)

@main_bp.route("/history/delete/<int:index>")
@login_required
def delete_fast(index):
    user_id = session["user_id"]
    fast = FastHistory.query.filter_by(user_id=user_id, id=index).first_or_404()
    db.session.delete(fast)
    db.session.commit()
    return redirect(url_for("main.history"))