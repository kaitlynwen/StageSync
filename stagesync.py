#!/usr/bin/env python

# -----------------------------------------------------------------------
# stagesync.py
# Author: Kaitlyn Wen, Michael Igbinoba, Timothy Sim
# -----------------------------------------------------------------------

from flask import Flask, render_template, redirect, url_for, request
import flask
import os
import dotenv
import tempfile
import parsedata
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, ForeignKey, Column
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# import auth

# -----------------------------------------------------------------------

# Load environment variables
dotenv.load_dotenv()

# Initialize Flask app
app = flask.Flask(
    "stagesync",
    template_folder="templates",  # Folder for HTML files
    static_folder="static",  # Folder for CSS, JS, and images
)

# Secret key setup (set up in .env)
app.secret_key = os.environ.get(
    "APP_SECRET_KEY", "your_default_secret_key"
)  # Make sure .env has the APP_SECRET_KEY

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = (
    True  # If needed, disable for performance
)
db = SQLAlchemy(app)

# Set temporary storage location for testing
UPLOAD_FOLDER = tempfile.mkdtemp()

# Allowable file extensions
ALLOWED_EXTENSIONS = {"csv", "xlsx"}

# -----------------------------------------------------------------------s


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -----------------------------------------------------------------------


# Define user info function (currently hardcoded for bypassing authentication)
def get_user_info():
    return {"user": "Admin User", "is_admin": True}


# -----------------------------------------------------------------------


# Routes
@app.route("/", methods=["GET"])
@app.route("/home", methods=["GET"])
def home():
    user_info = get_user_info()
    return render_template("home.html", user=user_info)


@app.route("/settings", methods=["GET"])
def settings():
    user_info = get_user_info()
    if user_info.get("is_admin", False):
        return render_template("settings-admin.html", user=user_info)
    else:
        return render_template("settings.html", user=user_info)


@app.route("/update-availability", methods=["GET"])
def update():
    user_info = get_user_info()
    return render_template("update.html", user=user_info)


@app.route("/view-schedule", methods=["GET"])
def view():
    user_info = get_user_info()
    return render_template("view.html", user=user_info)


@app.route("/upload-data", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part", 400

        file = request.files["file"]

        if file.filename == "":
            return "No selected file", 400

        if file and allowed_file(file.filename):
            group_name = "kokopops"

            date_range, calendar_events = parsedata.extract_schedule(file, group_name)

            return render_template(
                "upload.html", calendar_events=calendar_events, date_range=date_range
            )

        else:
            return "Invalid file type. Only CSV and XLSX are allowed", 400

    return render_template("upload.html")


@app.route("/generate-schedule", methods=["GET"])
def generate():
    user_info = get_user_info()
    if user_info.get("is_admin", False):
        return render_template("generate.html", user=user_info)
    else:
        return redirect(url_for("home"))


@app.route("/publish-schedule", methods=["GET"])
def publish():
    user_info = get_user_info()
    if user_info.get("is_admin", False):
        return render_template("publish.html", user=user_info)
    else:
        return redirect(url_for("home"))


@app.route("/manage-members", methods=["GET"])
def manage_members():
    user_info = get_user_info()
    if user_info.get("is_admin", False):
        return render_template("manage-members.html", user=user_info)
    else:
        return redirect(url_for("home"))


@app.route("/manage-users", methods=["GET"])
def manage_users():
    user_info = get_user_info()
    if user_info.get("is_admin", False):
        return render_template("manage-users.html", user=user_info)
    else:
        return redirect(url_for("home"))


@app.route("/manage-groups", methods=["GET"])
def manage_groups():
    user_info = get_user_info()
    if user_info.get("is_admin", False):
        return render_template("groups.html", user=user_info)
    else:
        return redirect(url_for("home"))


@app.route("/availability", methods=["GET"])
def availability():
    user_info = get_user_info()
    if user_info.get("is_admin", False):
        return render_template("availability.html", user=user_info)
    else:
        return redirect(url_for("home"))


# -----------------------------------------------------------------------


class Availability(db.Model):
    __tablename__ = "availability"

    # Columns
    id = db.Column(db.Integer, primary_key=True)  # auto incrementing ID
    netid = db.Column(db.String(50), ForeignKey("users.netid"), nullable=False)
    day_of_week = db.Column(
        Enum(
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
            name="days_of_week",
        ),
        nullable=False,
    )  # days of the week (e.g., 'Monday')
    start_time = db.Column(db.Time, nullable=False)  # start time of the time conflict
    end_time = db.Column(db.Time, nullable=False)  # end time of the time conflict
    is_recurring = db.Column(
        db.Boolean, nullable=False, default=False
    )  # whether conflict is recurring
    one_time_date = db.Column(db.Date, nullable=True)  # one-time date (if applicable)
    notes = db.Column(db.String(500), nullable=True)  # any additional notes

    # Relationship with the User model
    user = relationship("User", backref="availability")

    def __repr__(self):
        return f"<Availability {self.netid} {self.day_of_week} {self.start_time} - {self.end_time}>"


# Create tables
with app.app_context():
    db.create_all()

# -----------------------------------------------------------------------

# If the file is being executed directly, run the app
if __name__ == "__main__":
    app.run(debug=True)
