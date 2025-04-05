#!/usr/bin/env python

# ----------------------------------------------------------------------
# stagesync.py
# Author: Kaitlyn Wen, Michael Igbinoba, Timothy Sim
# ----------------------------------------------------------------------

from flask import render_template, redirect, url_for, request, jsonify, flash
from datetime import datetime, timedelta
import os
import dotenv
import parsedata
from zoneinfo import ZoneInfo  # Import ZoneInfo for time zone handling

import auth
import psycopg2
from top import app
from scheduler import assign_rehearsals, update_events_table
from req_lib import ReqLib


# ----------------------------------------------------------------------

# Load environment variables
dotenv.load_dotenv()

# Secret key setup (set up in .env)
app.secret_key = os.environ.get("APP_SECRET_KEY", "your_default_secret_key")

DATABASE_URL = os.getenv("DATABASE_URL")

# Allowable file extensions
ALLOWED_EXTENSIONS = {"xlsx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

COLOR_MAP = {
    "Bloomberg": "#84cc16",
    "Whitman": "#0ea5e9",
    "Dillon MPR": "#a855f7",
    "New South (Main)": "#f472b6",
    "NS Warm Up": "#14b8a6",
    "Murphy": "#f43f5e",
    "Broadmead": "#f59e0b",
}

# ----------------------------------------------------------------------


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ----------------------------------------------------------------------


def convert_to_utc(dt):
    """Converts a naive datetime to UTC using zoneinfo."""
    # Use ZoneInfo instead of pytz for time zone conversion
    est = ZoneInfo("US/Eastern")  # Eastern Time Zone
    utc = ZoneInfo("UTC")  # UTC time zone
    
    # Check if datetime is naive (i.e., doesn't have timezone information)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=est)  # Replace with the EST timezone info if naive
        
    return dt.astimezone(utc)  # Convert to UTC


def convert_from_utc(dt):
    """Converts a UTC datetime to local time zone using zoneinfo."""
    # Define your local time zone (Eastern Time Zone)
    local_tz = ZoneInfo("US/Eastern")
    
    # Make sure the datetime is timezone-aware (convert if it's naive)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))  # Localize to UTC if naive

    # Convert the UTC datetime to the local time zone
    return dt.astimezone(local_tz)

# ----------------------------------------------------------------------


# Define user info function (currently hardcoded for bypassing authentication)
def get_user_info():
    user_info = auth.authenticate()
    netid = user_info["user"]
    is_admin = None  # Default None

    # Based on PostgreSQL/authorsearch.py
    try:
        with psycopg2.connect(DATABASE_URL) as conn:

            with conn.cursor() as cur:
                query = "SELECT is_admin FROM users "
                query += "WHERE netid = '" + netid + "'"
                cur.execute(query)

                row = cur.fetchone()
                if row:
                    is_admin = row[0]

    except Exception as ex:
        pass  # for now

    return {"user": netid, "is_admin": is_admin}


# ----------------------------------------------------------------------


def get_all_users():
    """Fetches all members from the database to populate the dropdown."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT netid, first_name, last_name FROM users ORDER BY last_name, first_name"
                )
                members = cur.fetchall()

        # Convert result to a list of dictionaries
        return [
            {"netid": row[0], "first_name": row[1], "last_name": row[2]}
            for row in members
        ]

    except Exception as e:
        print(f"Error fetching members: {e}")
        return []  # Return empty list in case of failure


# ----------------------------------------------------------------------


def get_user_by_netid(netid):
    """Fetches a user from the database by netid."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT first_name, last_name FROM users
                    WHERE netid = %s
                """,
                    (netid,),
                )
                member = cursor.fetchone()

        return {"first_name": member[0], "last_name": member[1]}

    except Exception as e:
        print(netid)
        print(f"Error fetching members: {e}")
        return []  # Return empty list in case of failure


# ----------------------------------------------------------------------


def get_admin_users():
    """Fetch all admin users from the database."""
    admin_users = []
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT netid, first_name, last_name FROM users WHERE is_admin = TRUE"
                )
                for netid, first_name, last_name in cur.fetchall():
                    admin_users.append(
                        {
                            "netid": netid,
                            "first_name": first_name,
                            "last_name": last_name,
                        }
                    )

    except Exception as ex:
        print("Database error:", ex)

    return admin_users


# ----------------------------------------------------------------------


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
                            users.last_name,
                            users.netid,
                            rehearsal_groups.groupid
                        FROM group_members
                        JOIN rehearsal_groups ON group_members.groupid = rehearsal_groups.groupid
                        JOIN users ON group_members.netid = users.netid
                        ORDER BY rehearsal_groups.title, users.last_name, users.first_name;
                    """
                )
                for (
                    group_name,
                    first_name,
                    last_name,
                    netid,
                    group_id,
                ) in cur.fetchall():
                    if group_id not in groups:
                        groups[group_id] = {
                            "groupid": group_id,
                            "title": group_name,
                            "members": [],
                        }
                    groups[group_id]["members"].append(
                        {
                            "first_name": first_name,
                            "last_name": last_name,
                            "netid": netid,
                        }
                    )

    except Exception as ex:
        print("Database error:", ex)

    # Convert dictionary to list of dictionaries
    return list(groups.values())


# ----------------------------------------------------------------------

# Use OIT's Active Directory API to obtain basic user information
def active_directory_user(netid):
    req_lib = ReqLib()

    # req is a list of one dict
    req = req_lib.getJSON(
        req_lib.configs.USERS_BASIC,
        uid=netid,
    )
    if len(req) == 0:
        print("NetID does not exist")
        return None, None, None
    else:
        name=req[0]['displayname'].split()
        email=req[0]['mail']
        first_name=name[0]
        last_name=name[-1]
        return first_name, last_name, email

# ----------------------------------------------------------------------

# Convert time to 24-hour format for PostgreSQL
def convert_to_24hr_format(time_str):
    return datetime.strptime(time_str, "%I:%M%p").strftime("%H:%M:%S")


# Convert time to 12-hour format for html
def convert_to_12hr_format(time_str):
    return time_str.strftime("%I:%M %p").replace(" ", "")


# Delete existing time conflicts from database
def delete_conflict(netid):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM availability
                WHERE netid = %s
            """,
                (netid,),
            )
            conn.commit()


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
            cursor.execute(
                """
                SELECT day_of_week, start_time, end_time
                FROM availability
                WHERE netid = %s AND is_recurring = TRUE
                ORDER BY day_of_week, start_time
            """,
                (netid,),
            )

            for day, start, end in cursor.fetchall():
                # Convert start and end times from UTC to EST
                start_est = convert_from_utc(start)
                end_est = convert_from_utc(end)

                # Convert to 12-hour format for display
                start = convert_to_12hr_format(start_est)
                end = convert_to_12hr_format(end_est)

                # Append formatted times to the appropriate day
                weekly_conflicts[day].append(f"{start}-{end}")

    return weekly_conflicts


# Get existing one time conflicts from database
def get_one_time_conflict(netid):
    one_time_conflicts = []
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT one_time_date, start_time, end_time
                FROM availability
                WHERE netid = %s AND is_recurring = FALSE
                ORDER BY one_time_date, start_time
            """,
                (netid,),
            )

            for date, start, end in cursor.fetchall():
                date = date.strftime("%m/%d")
                start = convert_to_12hr_format(start)
                end = convert_to_12hr_format(end)
                one_time_conflicts.append(f"{date}.{start}-{end}")

            cursor.execute(
                """
                SELECT notes
                FROM availability
                WHERE netid = %s AND is_recurring = FALSE
                ORDER BY one_time_date, start_time
            """,
                (netid,),
            )

            row = cursor.fetchone()
            if row:
                conflict_notes = row[0]
            else:
                conflict_notes = ""

    if not one_time_conflicts:
        return [], conflict_notes

    else:
        return one_time_conflicts, conflict_notes


# Insert weekly conflict into the database
def insert_weekly_conflict(netid, day, start_time, end_time):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO availability (netid, day_of_week, start_time, 
                           end_time, is_recurring, one_time_date, notes)
                VALUES (%s, %s, %s, %s, TRUE, NULL, NULL)
            """,
                (netid, day, start_time, end_time),
            )
            conn.commit()


# Insert one-time conflict into the database
def insert_one_time_conflict(netid, one_time_date, day, start_time, end_time, notes):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO availability (netid, day_of_week, start_time, 
                           end_time, is_recurring, one_time_date, notes)
                VALUES (%s, %s, %s, %s, FALSE, %s, %s)
            """,
                (netid, day, start_time, end_time, one_time_date, notes),
            )
            conn.commit()
            
# ----------------------------------------------------------------------     
# Setting Updates

def get_user_settings(netid):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT receive_activity_updates, receive_reminders FROM user_settings WHERE user_netid = %s",
                    (netid,),
                )
                row = cur.fetchone()
                if row:
                    return {"activity": bool(row[0]), "reminders": bool(row[1])}
    except Exception as e:
        print(f"Error fetching settings: {e}")
    return {"activity": False, "reminders": False}


def save_user_settings(netid, activity, reminders):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO user_settings (user_netid, receive_activity_updates, receive_reminders)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_netid)
                    DO UPDATE SET receive_activity_updates = EXCLUDED.receive_activity_updates,
                                  receive_reminders = EXCLUDED.receive_reminders
                    """,
                    (netid, activity, reminders),
                )
                conn.commit()
    except Exception as e:
        print(f"Error saving settings: {e}")

# --------------------------------------------------------------------

# Routes
@app.route("/", methods=["GET"])
@app.route("/home", methods=["GET"])
def home():
    user_info = get_user_info()
    is_admin = user_info["is_admin"]
    if is_admin is None:
        return render_template("unauthorized-user.html", user=user_info)
    return render_template("home.html", user=user_info)


@app.route("/settings", methods=["GET"])
def settings():
    user_info = get_user_info()
    user_netid = user_info["user"]
    settings = get_user_settings(user_netid)
    return render_template("settings.html", user=user_info, settings=settings)

@app.route('/update-settings', methods=['POST'])
def update_settings():
    user_info = get_user_info()
    user_netid = user_info["user"]
    selected = request.form.getlist('notifications')
    activity = 'activity' in selected
    reminders = 'reminders' in selected
    save_user_settings(user_netid, activity, reminders)
    return redirect(url_for("settings"))


@app.route("/update-availability", methods=["GET", "POST"])
def update():
    if request.method == "GET":
        user_info = get_user_info()
        user_netid = user_info["user"]

        # Get the current conflicts (weekdays and one-time conflicts)
        weekly_conflicts = get_weekly_conflict(user_netid)
        one_time_conflicts, conflict_notes = get_one_time_conflict(user_netid)

        # Convert the weekly conflicts times from UTC to EST for display
        for day, conflicts in weekly_conflicts.items():
            for idx, conflict in enumerate(conflicts):
                
                start_time, end_time = conflict.split("-")
                start_time = start_time.strip()
                end_time = end_time.strip()

                # Convert to datetime objects (assuming these are stored in UTC in the DB)
                try:
                    start_time_dt = datetime.strptime(start_time, "%I:%M%p")
                    end_time_dt = datetime.strptime(end_time, "%I:%M%p")
                except ValueError as e:
                    print(f"Error parsing time: {e}")
                    continue

                # Convert from UTC to EST for display
                try:
                    start_time_est = convert_from_utc(start_time_dt)
                    end_time_est = convert_from_utc(end_time_dt)
                except ValueError as e:
                    print(f"Error in conversion: {e}")
                    continue

                # Update the conflict with the converted time (in EST)
                conflicts[idx] = f"{start_time_est.strftime('%I:%M%p')}-{end_time_est.strftime('%I:%M%p')}"

        return render_template(
            "update.html",
            user=user_info,
            weekly_conflicts=weekly_conflicts,
            one_time_conflicts=one_time_conflicts,
            conflict_notes=conflict_notes
        )

    else:
        user_info = get_user_info()
        user_netid = user_info["user"]
        
        delete_conflict(user_netid)

        weekly_conflicts = {
            "Monday": request.form["monday_conflicts"],
            "Tuesday": request.form["tuesday_conflicts"],
            "Wednesday": request.form["wednesday_conflicts"],
            "Thursday": request.form["thursday_conflicts"],
            "Friday": request.form["friday_conflicts"],
            "Saturday": request.form["saturday_conflicts"],
            "Sunday": request.form["sunday_conflicts"],
        }
        
        one_time_conflicts = request.form["one_time_conflict"]
        conflict_notes = request.form["conflict_notes"]

        # Parse and insert weekly conflicts, convert times to UTC before saving
        for day, conflicts in weekly_conflicts.items():
            if conflicts:
                for conflict in conflicts.split(";"):
                    start_time, end_time = conflict.split("-")
                    start_time = start_time.strip()
                    end_time = end_time.strip()

                    try:
                        # Convert to naive datetime objects first
                        start_time_est = datetime.strptime(start_time, "%I:%M%p")
                        end_time_est = datetime.strptime(end_time, "%I:%M%p")
                        
                        # Localize to EST (Eastern Standard Time)
                        est = ZoneInfo("US/Eastern")
                        start_time_est = start_time_est.replace(tzinfo=est)
                        end_time_est = end_time_est.replace(tzinfo=est)
                        
                    except ValueError as e:
                        print(f"Error parsing time: {e}")
                        continue
                    
                    # Convert to UTC before saving
                    start_time_utc = convert_to_utc(start_time_est)
                    end_time_utc = convert_to_utc(end_time_est)

                    # Store the conflicts in UTC
                    insert_weekly_conflict(user_netid, day, start_time_utc, end_time_utc)

        # Handle one-time conflicts (same logic as above)
        if one_time_conflicts:
            one_time_list = one_time_conflicts.split(";")
            for conflict in one_time_list:
                date_str, time_range = conflict.split(".")
                date_str = date_str.strip()
                time_range = time_range.strip()

                # Parse the date and convert to datetime
                try:
                    date = datetime.strptime(date_str, "%m/%d").replace(year=datetime.now().year)
                    day = date.strftime("%A")
                except ValueError as e:
                    print(f"Error parsing date: {e}")
                    continue

                # Split the start and end times
                start_time, end_time = time_range.split("-")
                start_time = start_time.strip()
                end_time = end_time.strip()

                try:
                    start_time_est = datetime.strptime(start_time, "%I:%M%p")
                    end_time_est = datetime.strptime(end_time, "%I:%M%p")
                except ValueError as e:
                    print(f"Error parsing time: {e}")
                    continue
                
                # Localize to EST
                est = ZoneInfo("US/Eastern")
                start_time_est = start_time_est.replace(tzinfo=est)
                end_time_est = end_time_est.replace(tzinfo=est)

                # Convert to UTC before saving
                start_time_utc = convert_to_utc(start_time_est)
                end_time_utc = convert_to_utc(end_time_est)
                
                insert_one_time_conflict(user_netid, date, day, start_time_utc, end_time_utc, conflict_notes)

        # Get updated conflicts (converted to UTC for saving)
        weekly_conflicts = get_weekly_conflict(user_netid)
        one_time_conflicts, conflict_notes = get_one_time_conflict(user_netid)

        success_message = "Availability successfully updated!"
        
        return render_template(
            "update.html",
            user=user_info,
            success_message=success_message,
            weekly_conflicts=weekly_conflicts,
            one_time_conflicts=one_time_conflicts,
            conflict_notes=conflict_notes,
        )


@app.route("/view-schedule", methods=["GET"])
def view():
    user_info = get_user_info()
    return render_template("view.html", user=user_info)


@app.route("/upload-data", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part in the request.", "error")
            return redirect(url_for("upload"))

        file = request.files["file"]

        if file.filename == "":
            flash("No file selected. Please choose a file.", "warning")
            return redirect(url_for("upload"))

        if file and allowed_file(file.filename):
            if request.content_length > MAX_FILE_SIZE:
                flash("File size exceeds 5MB. Please upload a smaller file.", "error")
                return redirect(url_for("upload"))

            group_name = "kokopops"
            filename = file.filename

            # Extract events and capture warnings
            try:
                _, calendar_events, warnings = parsedata.extract_schedule(file, filename, group_name)

                # Flash any warnings captured from parsing
                for warning in warnings:
                    flash(f"{warning}", "warning")

            except Exception as e:
                flash(f"Error processing file: {str(e)}", "error")
                return redirect(url_for("upload"))

            # Insert events into PostgreSQL
            try:
                with psycopg2.connect(DATABASE_URL) as conn:
                    with conn.cursor() as cur:
                        for event in calendar_events:
                            start_time = event["start"]
                            end_time = event["end"]

                            # Check if they are naive datetime objects, and convert them to UTC if so
                            start_time_utc = convert_to_utc(start_time)
                            end_time_utc = convert_to_utc(end_time)

                            # Check if event already exists
                            cur.execute(
                                """SELECT id FROM events WHERE start = %s AND "end" = %s AND location = %s""",
                                (start_time_utc, end_time_utc, event["location"]),
                            )
                            existing_events = cur.fetchall()

                            # Delete existing events
                            for e in existing_events:
                                cur.execute("DELETE FROM events WHERE id = %s", (e[0],))

                            # Insert new event
                            cur.execute(
                                """INSERT INTO events (title, start, "end", location, "groupid", created_at) 
                                   VALUES (%s, %s, %s, %s, %s, %s)""",
                                (
                                    event["title"],
                                    start_time_utc,  # Store UTC start time
                                    end_time_utc,  # Store UTC end time
                                    event["location"],
                                    event["groupid"],
                                    datetime.now(ZoneInfo("UTC")),  # Store UTC time for created_at
                                ),
                            )

                        conn.commit()

                flash("File uploaded and events saved successfully!", "success")
                return redirect(url_for("upload"))

            except Exception as e:
                flash(f"Database error: {str(e)}", "error")
                return redirect(url_for("upload"))

        flash("Invalid file type. Only XLSX files are allowed.", "error")
        return redirect(url_for("upload"))

    return render_template("upload.html")


@app.route("/generate-schedule", methods=["GET", "POST"])
def generate():
    user_info = get_user_info()
    if not user_info.get("is_admin", False):
        return redirect(url_for("home"))

    if request.method == "POST":
        # Generate the schedule
        schedule = assign_rehearsals()
        update_events_table(schedule)

        # Redirect to avoid re-executing POST request on refresh
        return redirect(url_for("generate"))

    return render_template("generate.html")


@app.route("/update-event", methods=["POST"])
def update_event():
    user_info = get_user_info()
    if not user_info.get("is_admin", False):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    event_id = data.get("id")
    start = data.get("start")
    end = data.get("end")
    title = data.get("title")
    location = data.get("location")

    if not all([event_id, start, end]):
        return jsonify({"error": "Missing required fields"}), 400

    # Convert start and end times to UTC (assuming the times from the frontend are in local time)
    local_timezone = ZoneInfo("America/New_York")  # Using zoneinfo to define the local timezone (Eastern Time)
    
    # Parse the datetime and localize to the local time zone
    start = datetime.fromisoformat(start).replace(tzinfo=local_timezone).astimezone(ZoneInfo("UTC"))
    end = datetime.fromisoformat(end).replace(tzinfo=local_timezone).astimezone(ZoneInfo("UTC"))

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                update_query = """
                    UPDATE draft_schedule
                    SET title = %s,
                        start = %s,
                        "end" = %s,
                        location = %s
                    WHERE publish_id = %s;
                """
                cur.execute(update_query, (title, start, end, location, event_id))
                conn.commit()

        return jsonify({"message": "Event updated successfully"})

    except Exception as e:
        print("Error updating event:", str(e))
        return jsonify({"error": "Failed to update event"}), 500
    

@app.route("/published-schedule", methods=["GET"])
def publish():
    user_info = get_user_info()
    if user_info.get("is_admin", True):
        return render_template("publish.html", user=user_info)
    else:
        return redirect(url_for("home"))


@app.route("/manage-admins", methods=["GET"])
def manage_users():
    user_info = get_user_info()
    admin_info = get_admin_users()
    if user_info.get("is_admin", True):
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
    if user_info.get("is_admin", True):
        return render_template("manage-groups.html", user=user_info, groups=group_info)
    else:
        return redirect(url_for("home"))


@app.route("/update-group-info", methods=["POST"])
def update_group_name():
    data = request.get_json()
    group_id = data.get("groupId")
    print(group_id)
    group_name = data.get("groupName")
    new_group_name = data.get("newGroupName")
    netids = data.get("netids", [])
    print(netids)

    try:
        if not group_name or not new_group_name:
            return (
                jsonify({"success": False, "message": "Error"}),  # CHANGE MESSAGE
                400,
            )  # Return error with status code 400

        # Connect to the database
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Update the title for given group
                query = """
                    UPDATE rehearsal_groups
                    SET title = %s
                    WHERE title = %s;
                """
                cur.execute(query, (new_group_name, group_name))
                conn.commit()

                # Remove selected members from group
                query = """
                    DELETE FROM group_members
                    WHERE groupid = %s
                    AND netid = ANY(%s);
                """
                cur.execute(query, (group_id, netids))
                conn.commit()

        return jsonify({"success": True}), 200  # Return success with status code 200

    except Exception as e:
        print(f"Error: {e}")
        return (
            jsonify({"error": "Internal Server Error"}),
            500,
        )  # Return error with status code 500


@app.route("/view-availability", methods=["GET", "POST"])
def availability():
    user_info = get_user_info()

    if user_info.get("is_admin", True):
        members = get_all_users()  # Fetch members list

        if request.method == "POST":
            selected_netid = request.form.get("selected_netid")
            if selected_netid:
                selected_member = get_user_by_netid(selected_netid)
                weekly_conflicts = get_weekly_conflict(selected_netid)
                one_time_conflicts, conflict_notes = get_one_time_conflict(
                    selected_netid
                )

                return render_template(
                    "availability.html",
                    user=user_info,
                    members=members,
                    selected_member=selected_member,
                    weekly_conflicts=weekly_conflicts,
                    one_time_conflicts=one_time_conflicts,
                    conflict_notes=conflict_notes,
                )

        return render_template(
            "availability.html",
            user=user_info,
            members=members,
            selected_member=None,
            weekly_conflicts=None,
            one_time_conflicts=None,
            conflict_notes=None,
        )

    return redirect(url_for("home"))


@app.route("/authorize-members", methods=["GET"])
def authorize_members():
    user_info = get_user_info()
    all_members = get_all_users()
    if user_info.get("is_admin", True):
        return render_template("authorize.html", user=user_info, old_members=all_members)
    else:
        return redirect(url_for("home"))

@app.route("/authorize", methods=["POST"])
def authorize():
    try:
        # Get the netid of the user to add as admin from the request body
        data = request.get_json()
        netid = data.get("netid")

        if not netid:
            return (
                jsonify({"success": False, "message": "NetID is required"}),
                400,
            )  # Return error with status code 400
        
        first_name, last_name, email=active_directory_user(netid)
        print("First name: ", first_name)
        print("Last name: ", last_name)
        print("email: ", email)

        if first_name is None:
            return (
                jsonify({"success": False, "message": "NetID does not exist"}),
                400,
            )  # Return error with status code 400

        # Add new user into database
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (netid, email, is_admin, 
                            first_name, last_name)
                    VALUES (%s, %s, False, %s, %s)
                    ON CONFLICT (netid) DO NOTHING
                """,
                    (netid, email, first_name, last_name),
                )
            conn.commit()

        return jsonify({"success": True}), 200  # Return success with status code 200

    except Exception as e:
        print(f"Error: {e}")
        return (
            jsonify({"error": "Internal Server Error"}),
            500,
        )  # Return error with status code 500
    
@app.route("/unauthorize", methods=["POST"])
def unauthorize():
    try:
        # Get the netids of users to remove from admin from the request body
        data = request.get_json()
        netids = data.get("netids", [])

        if not netids:
            return (
                jsonify({"success": False, "message": "NetID(s) required"}),
                400,
            )  # Return error with status code 400

        # Remove associated data from users, group_members, and availability
        # Connect to the database
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Remove specified members from group_members datatable
                query = """DELETE FROM group_members
                WHERE netid = ANY(%s)
                """
                cur.execute(query, (netids,))
                conn.commit()

                # Remove specified member from availability datatable
                query = """DELETE FROM availability
                WHERE netid = ANY(%s)
                """
                cur.execute(query, (netids,))
                conn.commit()

                # Remove specified members from users datatable
                query = """DELETE FROM users
                WHERE netid = ANY(%s)
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


@app.route("/events")
def events():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Fetch events along with their rehearsal space names
                cur.execute(
                    """
                    SELECT e.id, e.title, e.start, e."end", r.name
                    FROM events e
                    LEFT JOIN rehearsal_spaces r ON e.location = r.name
                    ORDER BY e.start ASC
                    """
                )
                events = cur.fetchall()

                # Fetch rehearsal space names (optional)
                cur.execute("SELECT name FROM rehearsal_spaces")
                rehearsal_spaces = cur.fetchall()

        # Convert the events to a list of dictionaries
        event_list = []
        for event in events:
            event_id = event[0]
            title = event[1]
            start = event[2]
            end = event[3]
            location = event[4] if event[4] else ""

            # Ensure start and end are timezone-aware datetime objects
            if isinstance(start, str):
                start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
            if isinstance(end, str):
                end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")

            # Localize to UTC if naive
            if start.tzinfo is None:
                start = start.replace(tzinfo=ZoneInfo("UTC"))
            if end.tzinfo is None:
                end = end.replace(tzinfo=ZoneInfo("UTC"))

            # Convert to local timezone (let FullCalendar handle this)
            # Pass these times as UTC and FullCalendar will handle the conversion
            event_dict = {
                "id": event_id,
                "title": title,
                "start": start.isoformat(),  # ISO format with time zone info
                "end": end.isoformat(),  # ISO format with time zone info
                "location": location,
                "color": COLOR_MAP.get(location, "#CCCCCC"),  # Default gray if unknown
            }

            event_list.append(event_dict)

        return jsonify(event_list)

    except Exception as e:
        print(f"Error fetching events from PostgreSQL: {e}")
        return jsonify({"error": f"Error fetching events: {str(e)}"}), 500

# ----------------------------------------------------------------------

@app.route("/draft-schedule")
def draft():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT d.publish_id, d.title, d.start, d."end", r.name
                    FROM draft_schedule d
                    LEFT JOIN rehearsal_spaces r ON d.location = r.name
                    ORDER BY d.start ASC
                """)
                events = cur.fetchall()

        # Convert the events to a list of dictionaries
        event_list = []
        for event in events:
            event_id = event[0]
            title = event[1]
            start = event[2]
            end = event[3]
            location = event[4] if event[4] else ""

            # Ensure start and end are datetime objects
            if isinstance(start, str):
                start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
            if isinstance(end, str):
                end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")

            # Localize to UTC if naive
            if start.tzinfo is None:
                start = start.replace(tzinfo=ZoneInfo("UTC"))
            if end.tzinfo is None:
                end = end.replace(tzinfo=ZoneInfo("UTC"))

            # Convert start and end times from UTC to local time zone (FullCalendar handles this)
            event_dict = {
                "id": event_id,
                "title": title,
                "start": start.isoformat(),  # ISO format with time zone info
                "end": end.isoformat(),  # ISO format with time zone info
                "location": location,
                "color": COLOR_MAP.get(location, "#CCCCCC"),  # Default gray if unknown
            }

            event_list.append(event_dict)

        return jsonify(event_list)

    except Exception as e:
        print(f"Error fetching events from PostgreSQL: {e}")
        return jsonify({"error": f"Error fetching events: {str(e)}"}), 500

# ----------------------------------------------------------------------

@app.route("/restore-draft-schedule", methods=["POST"])
def restore_draft_schedule():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Delete all rows in draft_schedule table
                cur.execute("DELETE FROM draft_schedule")

                # Copy all events from events table into draft_schedule
                cur.execute(
                    """
                    INSERT INTO draft_schedule (title, start, "end", location, groupid, created_at, publish_id)
                    SELECT title, start, "end", location, groupid, created_at, id
                    FROM events
                """
                )

                # Commit the transaction
                conn.commit()

        return jsonify({"message": "Draft schedule restored successfully!"})

    except Exception as e:
        print(f"Error restoring draft schedule from events table: {e}")
        return jsonify({"error": f"Error restoring draft schedule: {str(e)}"}), 500


@app.route("/publish-draft", methods=["POST"])
def publish_draft():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Updates events table with info from draft_schedule
                cur.execute(
                    """
                    UPDATE events
                    SET 
                        title = draft_schedule.title,
                        start = draft_schedule.start,
                        "end" = draft_schedule.end,
                        groupid = draft_schedule.groupid,
                        created_at = draft_schedule.created_at,
                        location = draft_schedule.location
                    FROM draft_schedule
                    WHERE 
                        events.id = draft_schedule.publish_id;
                """
                )

                # Commit the transaction
                conn.commit()

        return jsonify({"message": "Schedule published successfully!"})

    except Exception as e:
        print(f"Error publishing schedule: {e}")
        return jsonify({"error": f"Error publishing schedule: {str(e)}"}), 500


# -----------------------------------------------------------------------

# If the file is being executed directly, run the app
if __name__ == "__main__":
    app.run(debug=True)
