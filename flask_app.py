import sqlite3, os, secrets, time,json

from datetime import datetime
from flask import Flask, render_template, request, redirect, session,jsonify,send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from utils import error, login_required

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def homepage():
    return render_template("homepage.html")

@login_required
@app.route("/homepage")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        if not username:
            return ("Missing Username")
        elif not password:
            return ("Missing Password")
        elif not confirmation:
            return ("Missing Confirmation")
        elif confirmation != password:
            return ("Unmatching Password Confirmation")

        with sqlite3.connect("database.db") as con:
            con.row_factory = sqlite3.Row
            db = con.cursor()

            existing_user = db.execute("SELECT username FROM users WHERE username = ?", (username,)).fetchone()
            if existing_user:
                return ("Username has already been taken")

            try:
                db.execute("INSERT INTO users (username,hash) VALUES(?,?)",
                           (username, generate_password_hash(password)))
                con.commit()
                
                user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
                session["user_id"] = user["id"]
                
            except sqlite3.IntegrityError:
                return ("Username has already been taken")

        return redirect("/homepage")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return "kullanıcı adı yok"
        elif not request.form.get("password"):
            return "Missing Password"
            
        with sqlite3.connect("database.db") as con:
            con.row_factory = sqlite3.Row
            db = con.cursor()

            row = db.execute(
                "SELECT * FROM users WHERE username = ?",
                (request.form.get("username"),)
            ).fetchone()

            if row is None or not check_password_hash(row["hash"], request.form.get("password")):
                return "Username is invalid"
                
            session["user_id"] = row["id"]

        return redirect("/homepage")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@login_required
@app.route("/about")
def about():
    return render_template("about.html")

@login_required
@app.route("/contact")
def contact():
    return render_template("contact.html")

@login_required
@app.route("/settings")
def settings():
    return render_template("settings.html")

@login_required
@app.route("/devices")
def devices():
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        db = con.cursor()
        try:
            device = db.execute(
                "SELECT * FROM devices WHERE user_id = ?",
                (session["user_id"],)
            ).fetchone()
            return render_template("devices.html",model_info = device["model"],feed_url = device["cam_feed"],data_url=device["data_feed"])
        except TypeError:
            return render_template("devices.html",model_info = None,feed_url = None,data_url=None)

@login_required
@app.route("/submitsettings", methods=["GET","POST"])
def submitsettings():
    user_id = session["user_id"]
    model = request.form.get("model_info")
    feed_url = request.form.get("feed_url")
    data_url = request.form.get("data_url")
    with sqlite3.connect("database.db") as con:
        db = con.cursor()
        exist = db.execute(
                "SELECT model FROM devices WHERE user_id = ?",
                (session["user_id"],)
            ).fetchone()
        if exist:
            db.execute("UPDATE devices SET(model,cam_feed,data_feed) = (?,?,?) WHERE user_id = ?",(model,feed_url,data_url,user_id,))
        else:
            db.execute("INSERT INTO devices (user_id,model,cam_feed,data_feed) VALUES(?,?,?,?)",(user_id,model,feed_url,data_url,))
        con.commit()
    
    return redirect("/devices")

@login_required
@app.route("/3dmap")
def map3d():
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        db = con.cursor()
        try:
            feed = db.execute(
                "SELECT cam_feed FROM devices WHERE user_id = ?",
                (session["user_id"],)
            ).fetchone()["cam_feed"]
        except TypeError:
            feed = None
        return render_template("3dmap.html",cam_feed = feed)

@login_required
@app.route("/sensors")
def sensors():
    return render_template("sensors.html")

@login_required
@app.route("/riskmap")
def riskmap():
    return render_template("riskmap.html")
