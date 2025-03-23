#!/usr/bin/env python

# -----------------------------------------------------------------------
# stagesync.py
# Author: Kaitlyn Wen, Michael Igbinoba, Timothy Sim
# -----------------------------------------------------------------------

from flask import render_template, redirect, url_for, request, jsonify
from datetime import datetime
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
def get_user_info():
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

    return {"user": netid, "is_admin": is_admin}


# -----------------------------------------------------------------------


def get_admin_users():
    """Fetch all admin users from the database."""
    admin_users = []
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT netid, first_name, last_name FROM users WHERE is_admin = TRUE")
                for netid, first_name, last_name in cur.fetchall():
                    admin_users.append({"netid":netid, "first_name": first_name, "last_name": last_name})
                    
    except Exception as ex:
        print("Database error:", ex)

    return admin_users


# -----------------------------------------------------------------------


def get_groups():
    """Fetch all groups of members from the database."""
    groups = {}

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT 
                            rehearsal_groups.title AS group_name, 
                            users.first_name, 
                            users.last_name
                        FROM group_members
                        JOIN rehearsal_groups ON group_members.groupid = rehearsal_groups.groupid
                        JOIN users ON group_members.netid = users.netid
                        ORDER BY rehearsal_groups.title, users.last_name, users.first_name;
                    """
                )
                for group_name, first_name, last_name in cur.fetchall():
                    if group_name not in groups:
                        groups[group_name] = [] 
                    groups[group_name].append({"first_name": first_name, "last_name": last_name})

    except Exception as ex:
        print("Database error:", ex)

    # Convert dictionary to list of dictionaries
    return [{"title": group, "members": members} for group, members in groups.items()]


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


@app.route("/update-availability", methods=["GET", "POST"])
def update():
    if request.method == "GET":
        user_info = get_user_info()
        user_netid = user_info['user']
        weekly_conflicts = get_weekly_conflict(user_netid)
        return render_template("update.html", user=user_info, conflicts=weekly_conflicts)

    else:
        user_info = get_user_info()  # Fetch user info (netid) for the current user
        user_netid = user_info['user']  # Get the user netid
        weekly_conflicts = {
            "Monday": request.form['monday_conflicts'],
            "Tuesday": request.form['tuesday_conflicts'],
            "Wednesday": request.form['wednesday_conflicts'],
            "Thursday": request.form['thursday_conflicts'],
            "Friday": request.form['friday_conflicts'],
            "Saturday": request.form['saturday_conflicts'],
            "Sunday": request.form['sunday_conflicts'],
        }
        one_time_conflicts = request.form['one_time_conflict']
        conflict_notes = request.form['conflict_notes']
        
        # Parse and insert weekly conflicts
        for day, conflicts in weekly_conflicts.items():
            if conflicts:
                for conflict in conflicts.split(';'):
                    start_time, end_time = conflict.split('-')
                    start_time = convert_to_24hr_format(start_time.strip())
                    end_time = convert_to_24hr_format(end_time.strip())
                    insert_weekly_conflict(user_netid, day, start_time, end_time)

        # Parse and insert one-time conflicts
        if one_time_conflicts:
            one_time_list = one_time_conflicts.split(';')
            for conflict in one_time_list:
                date_str, time_range = conflict.split('.')
                date_str = date_str.strip()
                time_range = time_range.strip()
                date = datetime.strptime(date_str, '%m/%d').replace(year=datetime.now().year)
                day = date.strftime('%A')
                start_time, end_time = time_range.split('-')
                start_time = convert_to_24hr_format(start_time.strip())
                end_time = convert_to_24hr_format(end_time.strip())
                insert_one_time_conflict(user_netid, date, day, start_time, end_time, conflict_notes)

        success_message = "Availability successfully updated!"
        return render_template("update.html", user=user_info, success_message=success_message)

# Convert time to 24-hour format for PostgreSQL
def convert_to_24hr_format(time_str):
    return datetime.strptime(time_str, '%I:%M%p').strftime('%H:%M:%S')

# Convert time to 12-hour format for html
def convert_to_12hr_format(time_str):
     return time_str.strftime("%I:%M %p").replace(' ', '')

# Get existing weekly conflicts from database
def get_weekly_conflict(netid):
    weekly_conflicts = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": [],
        }
    
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT day_of_week, start_time, end_time
                FROM availability
                WHERE netid = %s AND is_recurring = FALSE
                ORDER BY day_of_week, start_time
            """, (netid,))
            
            for day, start, end in cursor.fetchall():
                start = convert_to_12hr_format(start)
                end = convert_to_12hr_format(end)
                weekly_conflicts[day].append(f"{start}-{end}")
    return weekly_conflicts

# Insert weekly conflict into the database
def insert_weekly_conflict(netid, day, start_time, end_time):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO availability (netid, day_of_week, start_time, end_time, is_recurring, one_time_date, notes)
        VALUES (%s, %s, %s, %s, FALSE, NULL, NULL)
    """, (netid, day, start_time, end_time))
    conn.commit()
    cursor.close()
    conn.close()

# Insert one-time conflict into the database
def insert_one_time_conflict(netid, one_time_date, day, start_time, end_time, notes):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO availability (netid, day_of_week, start_time, end_time, is_recurring, one_time_date, notes)
        VALUES (%s, %s, %s, %s, TRUE, %s, %s)
    """, (netid, day, start_time, end_time, one_time_date, notes))
    conn.commit()
    cursor.close()
    conn.close()

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
            return (
                jsonify({"success": False, "message": "NetID is required"}),
                400,
            )  # Return error with status code 400

        # Check to see if netid exists in database
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT EXISTS(SELECT 1 
                    FROM users
                    WHERE netid = %s);
                """
                cur.execute(query, (netid,))
                exists = cur.fetchone()[0]

                if not exists:
                    return jsonify(
                        {"success": False, "message": "NetID does not exist"}
                    )

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

        return jsonify({"success": True}), 200  # Return success with status code 200

    except Exception as e:
        print(f"Error: {e}")
        return (
            jsonify({"error": "Internal Server Error"}),
            500,
        )  # Return error with status code 500


@app.route("/remove-admins", methods=["POST"])
def remove_admins():
    try:
        # Get the netids of users to remove from admin from the request body
        data = request.get_json()
        # print("data: ", data) for testing
        netids = data.get("netids", [])
        # print(netids) for testing

        if not netids:
            return (
                jsonify({"success": False, "message": "NetID(s) required"}),
                400,
            )  # Return error with status code 400

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

        return jsonify({"success": True}), 200  # Return success with status code 200

    except Exception as e:
        print(f"Error: {e}")
        return (
            jsonify({"error": "Internal Server Error"}),
            500,
        )  # Return error with status code 500


@app.route("/manage-groups", methods=["GET"])
def manage_groups():
    user_info = get_user_info()
    group_info = get_groups()
    if user_info.get("is_admin", False):
        return render_template("manage-groups.html", user=user_info, groups=group_info)
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
