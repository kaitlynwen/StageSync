#!/usr/bin/env python

# -----------------------------------------------------------------------
# stagesync.py
# Author: Kaitlyn Wen, Michael Igbinoba, Timothy Sim
# -----------------------------------------------------------------------

from flask import render_template, redirect, url_for, request, jsonify
import flask
import os
import dotenv
import tempfile
import parsedata

# from flask_sqlalchemy import SQLAlchemy
import auth
import psycopg2
from top import app


# -----------------------------------------------------------------------

# Load environment variables
dotenv.load_dotenv()

# # Initialize Flask app
# app = flask.Flask(
#     "stagesync",
#     template_folder="templates",  # Folder for HTML files
#     static_folder="static",  # Folder for CSS, JS, and images
# )

# Secret key setup (set up in .env)
app.secret_key = os.environ.get(
    "APP_SECRET_KEY", "your_default_secret_key"
)  # Make sure .env has the APP_SECRET_KEY

DATABASE_URL = os.getenv("DATABASE_URL")

# Set temporary storage location for testing
UPLOAD_FOLDER = tempfile.mkdtemp()

# Allowable file extensions
ALLOWED_EXTENSIONS = {"csv", "xlsx"}

# -----------------------------------------------------------------------s


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -----------------------------------------------------------------------


# Define user info function (currently hardcoded for bypassing authentication)
"""def get_user_info():
    user_info = auth.authenticate()
    netid = user_info['user']
    is_admin = False #Default false

    # Based on PostgreSQL/authorsearch.py
    try:
        with psycopg2.connect(DATABASE_URL) as conn:

            with conn.cursor() as cur:
                query = 'SELECT is_admin FROM users '
                query += 'WHERE netid = \'' + netid + '\''
                cur.execute(query)

                row = cur.fetchone()
                if row:
                    is_admin = row[0]

    except Exception as ex:
        pass # for now

    return {"user": netid, "is_admin": is_admin}"""
    
def get_user_info():    
     return {"user": "test", "is_admin": True}

# -----------------------------------------------------------------------


def get_admin_users():
    """Fetch all admin users from the database."""
    admin_users = []
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT netid FROM users WHERE is_admin = TRUE")
                admin_users = [row[0] for row in cur.fetchall()]
    except Exception as ex:
        print("Database error:", ex)

    return admin_users


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


@app.route("/published-schedule", methods=["GET"])
def publish():
    user_info = get_user_info()
    if user_info.get("is_admin", False):
        return render_template("publish.html", user=user_info)
    else:
        return redirect(url_for("home"))


@app.route("/manage-admins", methods=["GET"])
def manage_users():
    user_info = get_user_info()
    admin_info = get_admin_users()
    if user_info.get("is_admin", False):
        return render_template("manage-admins.html", user=user_info, admins=admin_info)
    else:
        return redirect(url_for("home"))


@app.route("/add-admin", methods=["POST"])
def add_admin():
    try:
        # Get the netid of the user to add as admin from the request body
        data = request.get_json()
        netid = data.get("netid")

        if not netid:
            return jsonify({"error": "NetID is required"}), 400  # Return error with status code 400

        # Connect to the database
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Update the is_admin flag to True for the selected user
                query = """
                    UPDATE users
                    SET is_admin = TRUE
                    WHERE netid = %s;
                """
                cur.execute(query, (netid,))
                conn.commit()

        return jsonify({"message": "Admin added successfully"}), 200  # Return success with status code 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500  # Return error with status code 500

@app.route("/remove-admins", methods=["POST"])
def remove_admins():
    try:
        # Get the netids of users to remove from admin from the request body
        data = request.get_json()
        # print("data: ", data) for testing
        netids = data.get("netids", [])
        # print(netids) for testing

        if not netids:
            return jsonify({"error": "NetID(s) required"}), 400  # Return error with status code 400

        # Connect to the database
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Update the is_admin flag to False for the selected users
                query = """
                    UPDATE users
                    SET is_admin = FALSE
                    WHERE netid = ANY(%s);
                """
                cur.execute(query, (netids,))
                conn.commit()

        return jsonify({"message": "Admins removed successfully"}), 200  # Return success with status code 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500  # Return error with status code 500


@app.route("/manage-groups", methods=["GET"])
def manage_groups():
    user_info = get_user_info()
    if user_info.get("is_admin", False):
        return render_template("manage-groups.html", user=user_info)
    else:
        return redirect(url_for("home"))


@app.route("/view-availability", methods=["GET"])
def availability():
    user_info = get_user_info()
    if user_info.get("is_admin", False):
        return render_template("availability.html", user=user_info)
    else:
        return redirect(url_for("home"))


# -----------------------------------------------------------------------

# If the file is being executed directly, run the app
if __name__ == "__main__":
    app.run(debug=True)
