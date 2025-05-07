#!/usr/bin/env python

# ----------------------------------------------------------------------
# stagesync.py
# Author: Kaitlyn Wen, Michael Igbinoba, Timothy Sim
# ----------------------------------------------------------------------

import os
import psycopg2
import re
import parsedata
from io import BytesIO
from flask import (
    json,
    render_template,
    redirect,
    send_file,
    url_for,
    request,
    jsonify,
    flash,
)
from datetime import datetime
from ics import Calendar, Event
from req_lib import ReqLib
from zoneinfo import ZoneInfo
from psycopg2.extras import execute_values
from markupsafe import escape


from top import app, csrf
from scheduler import assign_rehearsals, update_events_table
from export_cal import get_calendar_events
from datetime_helpers import *
from db_helpers import *


# ----------------------------------------------------------------------

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
        name = req[0]["displayname"].split()
        email = req[0]["mail"]
        first_name = name[0]
        last_name = name[-1]
        return first_name, last_name, email


# --------------------------------------------------------------------


def is_oauth(request):
    # Skip CSRF for OAuth callback route
    if request.path.startswith("/oauth/"):
        return True

    # Skip CSRF for API requests
    if request.path.startswith("/api/"):
        return True

    # Skip CSRF for specific methods
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return True

    return False



# --------------------------------------------------------------------

# Strip suspicious characters, then escape


def clean_text(text):
    return escape(re.sub(r"[^\w\s.,!?@#%&()\-:;'/\"|]+", "", text))

def sanitize_notes(notes):
    return escape(re.sub(r"[^\w\s.,!?@#%&()\-:;'/\"|]+", "", notes))



# --------------------------------------------------------------------




# Force HTTPS request
@app.before_request
def before_request():
    if (not app.debug) and (not request.is_secure):
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)
    return None

# Check CSRF token
@app.before_request
def check_csrf():
    if not is_oauth(request):
        csrf.protect()


# --------------------------------------------------------------------

@app.before_request
def check_admin():
    if (request.path.startswith("/static/")
        or request.path.startswith("/unauthorized")
        or request.path.startswith("/logoutcas")):
        return
    user_info = get_user_info()

    if user_info.get("is_admin") is None:
        return redirect(url_for("unauthorized"))

# --------------------------------------------------------------------

@app.route("/unauthorized")
def unauthorized():
    user_info = get_user_info()
    return render_template("unauthorized-user.html", user=user_info)

# --------------------------------------------------------------------

# Routes
@app.route("/", methods=["GET"])
@app.route("/home", methods=["GET"])
def home():
    user_info = get_user_info()
    return render_template("home.html", user=user_info)

@app.route("/settings", methods=["GET"])
def settings():
    user_info = get_user_info()
    user_netid = user_info["user"]
    settings = get_user_settings(user_netid)
    return render_template("settings.html", user=user_info, settings=settings)


@app.route("/update-settings", methods=["POST"])
def update_settings():
    user_info = get_user_info()
    user_netid = user_info["user"]
    selected = request.form.getlist("notifications")
    activity = "activity" in selected
    reminders = "reminders" in selected
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

                # Update the conflict with the converted time (in EST)
                conflicts[idx] = (
                    f"{start_time_dt.strftime('%I:%M%p')}-{end_time_dt.strftime('%I:%M%p')}"
                )
                
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

        # Access and sanitize raw inputs first
        raw_weekly_conflicts = {
            "Monday": request.form["monday_conflicts"],
            "Tuesday": request.form["tuesday_conflicts"],
            "Wednesday": request.form["wednesday_conflicts"],
            "Thursday": request.form["thursday_conflicts"],
            "Friday": request.form["friday_conflicts"],
            "Saturday": request.form["saturday_conflicts"],
            "Sunday": request.form["sunday_conflicts"],
        }

        one_time_raw = request.form["one_time_conflict"]
        notes_raw = request.form["conflict_notes"]

        # Character limit checks 
        for day, val in raw_weekly_conflicts.items():
            if len(val) > 100:
                flash(f"{day} conflicts exceed 100 characters. Please shorten your input.", "error")
                for d, val in raw_weekly_conflicts.items():
                    raw_weekly_conflicts[d] = [v.strip() for v in val.split(";") if v.strip()]
                    one_time_list = [v.strip() for v in one_time_raw.split(";") if v.strip()]
                return render_template(
                    "update.html",
                    user=user_info,
                    weekly_conflicts=raw_weekly_conflicts,
                    one_time_conflicts=one_time_list,
                    conflict_notes=notes_raw
                )

        if len(one_time_raw) > 100:
            flash("One-time conflicts exceed 100 characters. Please shorten your input.", "error")
            for d, val in raw_weekly_conflicts.items():
                raw_weekly_conflicts[d] = [v.strip() for v in val.split(";") if v.strip()]
                one_time_list = [v.strip() for v in one_time_raw.split(";") if v.strip()]
            return render_template(
                "update.html",
                user=user_info,
                weekly_conflicts=raw_weekly_conflicts,
                one_time_conflicts=one_time_list,
                conflict_notes=notes_raw
            )

        if len(notes_raw) > 100:
            flash("Conflict notes exceed 100 characters. Please shorten your input.", "error")
            for d, val in raw_weekly_conflicts.items():
                raw_weekly_conflicts[d] = [v.strip() for v in val.split(";") if v.strip()]
                one_time_list = [v.strip() for v in one_time_raw.split(";") if v.strip()]
            
            return render_template(
                "update.html",
                user=user_info,
                weekly_conflicts=raw_weekly_conflicts,
                one_time_conflicts=one_time_list,
                conflict_notes=notes_raw
            )

        # If all inputs are valid, sanitize and begin database operations
        delete_conflict(user_netid)

        weekly_conflicts = {day: escape(val) for day, val in raw_weekly_conflicts.items()}
        one_time_conflicts = escape(one_time_raw)
        conflict_notes = sanitize_notes(notes_raw)

        # Parse and insert weekly conflicts, convert times to UTC before saving
        for day, conflicts in weekly_conflicts.items():
            if conflicts:
                for conflict in conflicts.split(";"):
                    start_time, end_time = conflict.split("-")
                    start_time = start_time.strip()
                    end_time = end_time.strip()

                    try:
                        start_time_est = datetime.strptime(start_time, "%I:%M%p")
                        end_time_est = datetime.strptime(end_time, "%I:%M%p")
                        est = ZoneInfo("US/Eastern")
                        start_time_utc = convert_to_utc(start_time_est.replace(tzinfo=est))
                        end_time_utc = convert_to_utc(end_time_est.replace(tzinfo=est))
                        insert_weekly_conflict(user_netid, day, start_time_utc, end_time_utc)
                    except ValueError as e:
                        print(f"Error parsing time: {e}")
                        continue

        if one_time_conflicts:
            for conflict in one_time_conflicts.split(";"):
                date_str, time_range = conflict.split(".")
                date_str = date_str.strip()
                time_range = time_range.strip()

                try:
                    date = datetime.strptime(date_str, "%m/%d").replace(year=datetime.now().year)
                    day = date.strftime("%A")
                except ValueError as e:
                    print(f"Error parsing date: {e}")
                    continue

                start_time, end_time = time_range.split("-")
                start_time = start_time.strip()
                end_time = end_time.strip()

                try:
                    start_time_est = datetime.strptime(start_time, "%I:%M%p")
                    end_time_est = datetime.strptime(end_time, "%I:%M%p")
                    est = ZoneInfo("US/Eastern")
                    start_time_utc = convert_to_utc(start_time_est.replace(tzinfo=est))
                    end_time_utc = convert_to_utc(end_time_est.replace(tzinfo=est))
                    insert_one_time_conflict(user_netid, date, day, start_time_utc, end_time_utc, conflict_notes)
                except ValueError as e:
                    print(f"Error parsing time: {e}")
                    continue

        weekly_conflicts = get_weekly_conflict(user_netid)
        one_time_conflicts, conflict_notes = get_one_time_conflict(user_netid)
        success_message = "Availability successfully updated!"
        notify_admins_user_updated(user_netid)

        flash(success_message, "success")
        return redirect(url_for("update"))


@app.route("/upload-data", methods=["GET", "POST"])
def upload():
    user_info = get_user_info()
    if not user_info.get("is_admin", False):
        return redirect(url_for("home"))
    
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
                _, calendar_events, warnings = parsedata.extract_schedule(
                    file, filename, group_name
                )

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
                                """SELECT id FROM draft_schedule WHERE start = %s AND "end" = %s AND location = %s""",
                                (start_time_utc, end_time_utc, event["location"]),
                            )
                            existing_events = cur.fetchall()

                            # If an event already exists, update it
                            for e in existing_events:
                                cur.execute(
                                    """UPDATE draft_schedule
                                    SET title = %s, start = %s, "end" = %s, location = %s, groupid = %s, created_at = %s
                                    WHERE id = %s""",
                                    (
                                        event["title"],
                                        start_time_utc,  # Store UTC start time
                                        end_time_utc,  # Store UTC end time
                                        event["location"],
                                        event["groupid"],
                                        datetime.now(ZoneInfo("UTC")),  # Store UTC time for created_at
                                        e[0],  # ID of the existing event
                                    ),
                                )

                            # If no existing event was found, insert a new one
                            if not existing_events:
                                cur.execute(
                                    """INSERT INTO draft_schedule (title, start, "end", location, groupid, created_at)
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

                flash("File uploaded and events saved successfully!", "success")
                return redirect(url_for("upload"))

            except Exception as e:
                flash(f"Database error: {str(e)}", "error")
                return redirect(url_for("upload"))

        flash("Invalid file type. Only XLSX files are allowed.", "error")
        return redirect(url_for("upload"))

    return render_template("upload.html", user=user_info)


@app.route("/generate-schedule", methods=["GET", "POST"])
def generate():
    user_info = get_user_info()
    if not user_info.get("is_admin", False):
        return redirect(url_for("home"))

    group_names = get_group_names()

    if request.method == "POST":
        schedule, warnings = assign_rehearsals()
        event_update_warnings = update_events_table(schedule) or []
        warnings = warnings or []
        warnings.extend(event_update_warnings)

        for warning, category in warnings:
            flash(escape(warning), category=escape(category))

        send_schedule_update_email()
        
        has_error = any(category == "error" for _, category in warnings)
        
        if not has_error:
            flash("Schedule has been successfully generated!", category="success")
        return redirect(url_for("generate"))

    return render_template("generate.html", user=user_info, group_names=group_names)


@app.route("/update-event", methods=["POST"])
def update_event():
    user_info = get_user_info()
    if not user_info.get("is_admin", False):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    event_id = data.get("id")
    start = data.get("start")
    end = data.get("end")
    title = clean_text(data.get("title", ""))
    location = clean_text(data.get("location", ""))
    groupid = data.get("groupid")

    if len(title) > 100:
        return jsonify({"error": "Event title too long"}), 400

    if groupid == "":
        groupid = None

    elif groupid is not None:
        try:
            groupid = int(groupid)
        except ValueError:
            return jsonify({"error": "Invalid group ID"}), 400

    if not all([event_id, start, end]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                update_query = """
                    UPDATE draft_schedule
                    SET title = %s,
                        start = %s,
                        "end" = %s,
                        location = %s,
                        groupid = %s
                    WHERE id = %s;
                """
                cur.execute(update_query, (title, start, end, location, groupid, event_id))
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


@app.route("/manage-admins", methods=["GET", "POST"])
def manage_users():
    user_info = get_user_info()
    admin_info = get_admin_users()

    if not user_info.get("is_admin", True):
        return redirect(url_for("home"))

    members = get_all_users()

    if request.method == "POST":
        netids_to_remove = request.form.get("netids_to_remove")
        if netids_to_remove:
            try:
                netids = json.loads(netids_to_remove)
                cs_netids = [n for n in netids if n.startswith("cs-")]

                if cs_netids:
                    flash("Cannot remove admin netids with prefix 'cs-': " + ", ".join(cs_netids), "error")
                    return redirect(url_for("manage_users"))

                with psycopg2.connect(DATABASE_URL) as conn:
                    with conn.cursor() as cur:
                        query = """
                            UPDATE users
                            SET is_admin = FALSE
                            WHERE netid = ANY(%s);
                        """
                        cur.execute(query, (netids,))
                        conn.commit()

                flash("Admin permissions removed successfully.", "success")
                return redirect(url_for("manage_users"))

            except Exception as e:
                print(f"Error removing admins: {e}")
                flash("Failed to remove admin(s).", "error")
                return redirect(url_for("manage_users"))

        # Otherwise, it's an add-admin request
        selected_netid = request.form.get("selected_netid")
        if selected_netid:
            response = add_admin(selected_netid)

            if isinstance(response, tuple):
                data, status_code = response
            else:
                data = response
                status_code = 200

            result = data.get_json()
            if status_code == 200 and result.get("success"):
                flash("Admin added successfully!", "success")
            else:
                message = result.get("message") or result.get("error") or "Something went wrong."
                flash(message, "error")

            return redirect(url_for("manage_users"))

    return render_template(
        "manage-admins.html",
        user=user_info,
        members=members,
        admins=admin_info
    )

@app.route("/manage-groups", methods=["GET"])
def manage_groups():
    user_info = get_user_info()
    group_info = get_groups()
    members = get_all_users()
    if user_info.get("is_admin", True):
        return render_template(
            "manage-groups.html", user=user_info, groups=group_info, allMembers=members
        )
    else:
        return redirect(url_for("home"))


@app.route("/update-group-info", methods=["POST"])
def update_group_name():
    data = request.get_json()
    group_id = data.get("groupId")
    group_name = data.get("groupName", "").strip()
    new_group_name = data.get("newGroupName", "").strip()
    remove = data.get("remove", [])
    add = data.get("add", [])

    try:
        if not group_name or not new_group_name:
            return (
                jsonify({"success": False, "message": "Error"}),  # CHANGE MESSAGE
                400,
            )  # Return error with status code 400

        # Connect to the database
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                #Check if Group already exists
                if group_name != new_group_name:
                    query = """
                        SELECT 1 
                        FROM rehearsal_groups 
                        WHERE title = %s
                    """
                    cur.execute(query, (new_group_name,))
                    if cur.fetchone():
                        return jsonify({"error": "Group name already exists"}), 400
                    
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
                cur.execute(query, (group_id, remove))
                conn.commit()

                # Add selected members to group
                query = """
                    INSERT INTO group_members (groupid, netid)
                    VALUES %s
                    ON CONFLICT DO NOTHING
                """
                params = [(group_id, netid) for netid in add]
                execute_values(cur, query, params)
                conn.commit()
        flash("Changes for \"" + group_name + "\" saved!", "success")
        return jsonify({"success": True}), 200  # Return success with status code 200

    except Exception as e:
        print(f"Error: {e}")
        return (
            jsonify({"error": "Internal Server Error"}),
            500,
        )  # Return error with status code 500


@app.route("/create-group", methods=["POST"])
def create_group():
    data = request.get_json()
    group_name = data.get("groupName", "").strip()

    try:
        # Connect to the database
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                #Check if Group already exists
                query = """
                    SELECT 1 
                    FROM rehearsal_groups 
                    WHERE title = %s
                """
                cur.execute(query, (group_name,))
                if cur.fetchone():
                    return jsonify({"error": "Group name already exists"}), 400
                
                # Create new group
                query = """
                    INSERT INTO rehearsal_groups (title)
                    VALUES (%s)
                """
                cur.execute(query, (group_name,))
                conn.commit()
        flash("Group \"" + group_name + "\" successfully created", "success")
        return jsonify({"success": True}), 200  # Return success with status code 200

    except Exception as e:
        print(f"Error: {e}")
        return (
            jsonify({"error": "Internal Server Error"}),
            500,
        )  # Return error with status code 500


@app.route("/delete-group", methods=["POST"])
def delete_group():
    data = request.get_json()
    group_id = data.get("groupId")

    try:
        # Connect to the database
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Delete group from draft_schedule
                query = """
                    DELETE FROM draft_schedule 
                    WHERE groupid = %s
                """
                cur.execute(query, (group_id,))
                conn.commit()

                # Delete group from events
                query = """
                    DELETE FROM events 
                    WHERE groupid = %s
                """
                cur.execute(query, (group_id,))
                conn.commit()

                # Delete group from group_members
                query = """
                    DELETE FROM group_members 
                    WHERE groupid = %s
                """
                cur.execute(query, (group_id,))
                conn.commit()

                # Delete group from rehearsal_groups
                query = """
                    DELETE FROM rehearsal_groups 
                    WHERE groupid = %s
                """
                cur.execute(query, (group_id,))
                conn.commit()
        flash("Group successfully deleted", "success")
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


@app.route("/user-access", methods=["GET"])
def user_access():
    user_info = get_user_info()
    all_members = get_all_users()
    if user_info.get("is_admin", True):
        return render_template(
            "user-access.html", user=user_info, old_members=all_members
        )
    else:
        return redirect(url_for("home"))


@app.route("/authorize", methods=["POST"])
def authorize():
    try:
        # Get the netid of the user to authorize from the request body
        data = request.get_json()
        netid = data.get("netid")

        if not netid:
            return (
                jsonify({"success": False, "message": "NetID is required"}),
                400,
            )  # Return error with status code 400

        first_name, last_name, email = active_directory_user(netid)

        if first_name is None:
            flash("User with NetID \"" + netid + "\" does not exist", "error")
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
        flash("User with NetID \"" + netid + "\" successfully added", "success")
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
        # Get the netids of users to unauthorize from the request body
        data = request.get_json()
        netids = data.get("netids", [])

        cs_netids = [n for n in netids if n.startswith("cs-")]
        if cs_netids:
            flash("Cannot remove netids with prefix 'cs-': " + ", ".join(cs_netids), "error")
            return (
                jsonify({"success": False, "message": "Cannot remove admin netids with prefix 'cs-': " + ", ".join(cs_netids)}),
                400,
            )
        
        # Prevent developers from being removed for grading purposes
        stagesync_netids = [n for n in netids if n in {"kw8166", "ts2188", "mi0894"}]
        if stagesync_netids:
            flash("Cannot remove developer(s): " + ", ".join(stagesync_netids), "error")
            return (
                jsonify({"success": False, "message": "Cannot remove developers(s): " + ", ".join(stagesync_netids)}),
                400,
            )

        if not netids:
            flash("NetdID(s) required")
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
        flash("Selected NetID(s) successfully removed", "success")
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
                cur.execute("SELECT name FROM rehearsal_spaces ORDER BY name")
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
                "color": COLOR_MAP.get(location, "#262626"),  # Default gray if unknown
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
                cur.execute(
                    """
                    SELECT d.id, d.title, d.start, d."end", d.groupid, r.name
                    FROM draft_schedule d
                    LEFT JOIN rehearsal_spaces r ON d.location = r.name
                    ORDER BY d.start ASC
                """
                )
                events = cur.fetchall()

        # Convert the events to a list of dictionaries
        event_list = []
        for event in events:
            event_id = event[0]
            title = event[1]
            start = event[2]
            end = event[3]
            groupid = event[4]
            location = event[5] if event[5] else ""

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
                "groupid": groupid,
                "color": COLOR_MAP.get(location, "#262626"),  # Default gray if unknown
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
                # Copy all events from events table into draft_schedule
                cur.execute(
                    """
                   UPDATE draft_schedule d
                    SET
                        title = e.title,
                        start = e.start,
                        "end" = e."end",
                        location = e.location,
                        groupid = e.groupid,
                        created_at = e.created_at
                    FROM events e
                    WHERE d.id = e.publishid;
                """
                )
                
                cur.execute(
                    """
                    INSERT INTO draft_schedule (id, title, start, "end", location, groupid, created_at)
                    SELECT 
                        e.publishid, e.title, e.start, e."end", e.location, e.groupid, e.created_at
                    FROM events e
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM draft_schedule d
                        WHERE d.id = e.publishid
                    );
                    """
                )
                
                cur.execute(
                    """
                    DELETE FROM draft_schedule
                    WHERE id NOT IN (
                        SELECT publishid FROM events
                        WHERE publishid IS NOT NULL
                    );
                    """
                )

        return jsonify({"message": "Draft schedule restored successfully!"})

    except Exception as e:
        print(f"Error restoring draft schedule from events table: {e}")
        return jsonify({"error": f"Error restoring draft schedule: {str(e)}"}), 500


@app.route("/publish-draft", methods=["POST"])
def publish_draft():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM events")
                cur.execute(
                    """
                    INSERT INTO events (title, start, "end", location, groupid, created_at, publishid)
                    SELECT title, start, "end", location, groupid, NOW(), id
                    FROM draft_schedule;"""
                )

        return jsonify({"message": "Schedule published successfully!"})

    except Exception as e:
        print(f"Error publishing schedule: {e}")
        return jsonify({"error": f"Error publishing schedule: {str(e)}"}), 500


@app.route("/add-event", methods=["POST"])
def add_event():
    user_info = get_user_info()
    if not user_info.get("is_admin", False):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    # Retrieve the event data from the request
    title = data.get("title")
    location = data.get("location")
    start = data.get("start")
    end = data.get("end")
    group_id = data.get("group_id")

    if group_id == "":
        group_id = None
        
    print(group_id)
        
    # Validate required fields
    if not all([title, location, start, end]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Parse the start and end times from the request (assuming ISO format)
        start = datetime.fromisoformat(start)
        end = datetime.fromisoformat(end)
    except ValueError:
        return jsonify({"error": "Invalid datetime format"}), 400

    # Insert the new event into the draft_schedule table (not the events table yet)
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                insert_query = """
                    INSERT INTO draft_schedule (title, location, start, "end", groupid)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, title, location, start, "end", groupid;
                """
                cur.execute(insert_query, (title, location, start, end, group_id))
                event = cur.fetchone()
                conn.commit()

        # Return the added event as a response
        event_response = {
            "id": event[0],
            "title": event[1],
            "location": event[2],
            "start": event[3].isoformat(),
            "end": event[4].isoformat(),
            "group_id": event[5]
        }

        return (
            jsonify({"message": "Event added successfully", "event": event_response}),
            201,
        )

    except Exception as e:
        print("Error adding event:", str(e))
        return jsonify({"error": "Failed to add event"}), 500



@app.route("/delete-event", methods=["POST"])
def delete_event():
    user_info = get_user_info()
    if not user_info.get("is_admin", False):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    # Retrieve the event data from the request
    event_id = data.get("event_id")
        
    # Validate required fields
    if not event_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                delete_query = """
                    DELETE FROM draft_schedule
                    WHERE id = %s;
                """
                cur.execute(delete_query, (event_id,))
                conn.commit() 

        return (
            jsonify({"message": "Event removed successfully"}),
            201,
        )

    except Exception as e:
        print("Error adding event:", str(e))
        return jsonify({"error": "Failed to delete event"}), 500


@app.route("/download-calendar", methods=["GET"])
def download_calendar():
    calendar_events = get_calendar_events()
    calendar = Calendar()

    for e in calendar_events:
        event = Event()
        event.name = e["name"]
        event.begin = e["begin"]
        event.end = e["end"]
        event.location = e["location"]
        calendar.events.add(event)

    # Use an in-memory buffer
    buffer = BytesIO()
    buffer.write(calendar.serialize().encode("utf-8"))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="rehearsals.ics",
        mimetype="text/calendar",
    )


# -----------------------------------------------------------------------

# If the file is being executed directly, run the app
if __name__ == "__main__":
    app.run(debug=True)
