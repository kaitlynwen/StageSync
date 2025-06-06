# ----------------------------------------------------------------------
# db_helpers.py
# Author: Kaitlyn Wen, Michael Igbinoba, Timothy Sim
#
# Description: contains helper functions for stagesync.py that
# contain queries to the PostgreSQL database
# ----------------------------------------------------------------------


import os
import requests
import psycopg2
from email.message import EmailMessage
from flask import jsonify, request
from dotenv import load_dotenv
from datetime_helpers import *
import auth


# ----------------------------------------------------------------------

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM = "cs-stagesync@princeton.edu"

# ----------------------------------------------------------------------

# Define user info function
def get_user_info():
    user_info = auth.authenticate()
    netid = user_info["user"]
    is_admin = None  # Default None

    # Based on PostgreSQL/authorsearch.py
    try:
        with psycopg2.connect(DATABASE_URL) as conn:

            with conn.cursor() as cur:
                query = "SELECT is_admin FROM users "
                query += "WHERE netid = %s"
                cur.execute(query, (netid,))

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
                    WHERE netid = %s ORDER BY last_name, first_name
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
                    "SELECT netid, first_name, last_name FROM users WHERE is_admin = TRUE ORDER BY last_name, first_name"
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
                        FROM rehearsal_groups
                        LEFT JOIN group_members ON group_members.groupid = rehearsal_groups.groupid
                        LEFT JOIN users ON group_members.netid = users.netid
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
                    # Only append members if members exist in the group
                    if netid:
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


def get_group_names():
    """Fetch all group names."""
    groups = {}

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT 
                            rehearsal_groups.title AS group_name, 
                            rehearsal_groups.groupid
                        FROM rehearsal_groups
                        ORDER BY rehearsal_groups.title;
                    """
                )
                for (
                    group_name,
                    group_id,
                ) in cur.fetchall():
                    if group_id not in groups:
                        groups[group_id] = group_name
    except Exception as ex:
        print("Database error:", ex)

    return groups


# ----------------------------------------------------------------------


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


# ----------------------------------------------------------------------


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



# ----------------------------------------------------------------------


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
                
                start_est = convert_from_utc(start)
                end_est = convert_from_utc(end)
                
                start = convert_to_12hr_format(start_est)
                end = convert_to_12hr_format(end_est)
                
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


# ----------------------------------------------------------------------


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



# ----------------------------------------------------------------------


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


def get_user_settings(netid):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT receive_activity_updates, receive_reminders, receive_availability_updates FROM user_settings WHERE user_netid = %s",
                    (netid,),
                )
                row = cur.fetchone()
                if row:
                    return {
                        "activity": bool(row[0]),
                        "reminders": bool(row[1]),
                        "availability": bool(row[2])
                    }
    except Exception as e:
        print(f"Error fetching settings: {e}")
    return {"activity": False, "reminders": False, "availability": False}



# ----------------------------------------------------------------------


def save_user_settings(netid, activity, reminders, availability):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO user_settings (user_netid, receive_activity_updates, receive_reminders, receive_availability_updates)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_netid)
                    DO UPDATE SET receive_activity_updates = EXCLUDED.receive_activity_updates,
                                  receive_reminders = EXCLUDED.receive_reminders,
                                  receive_availability_updates = EXCLUDED.receive_availability_updates
                    """,
                    (netid, activity, reminders, availability),
                )
                conn.commit()
    except Exception as e:
        print(f"Error saving settings: {e}")

# ------------------------------------------------------------

def get_reminder_emails():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_netid FROM user_settings
                    WHERE receive_activity_updates = TRUE
                """)
                rows = cur.fetchall()
                return [f"{netid}@princeton.edu" for (netid,) in rows]
    except Exception as e:
        print(f"Error fetching reminder emails: {e}")
        return []
    
# ----------------------------------------------------------------------

def send_email_sendgrid(subject, recipients, body):
    if not SENDGRID_API_KEY:
        print("Missing SendGrid API key.")
        return

    for to_email in recipients:
        try:
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {SENDGRID_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [
                        {
                            "to": [{"email": to_email}],
                            "subject": subject
                        }
                    ],
                    "from": {"email": SENDGRID_FROM},
                    "content": [
                        {
                            "type": "text/plain",
                            "value": body
                        }
                    ]
                }
            )
            if response.status_code >= 400:
                print(f"Failed to send email to {to_email}: {response.text}")
            else:
                print(f"Email sent to {to_email} via SendGrid API.")
        except Exception as e:
            print(f"Error sending to {to_email}: {e}")

# ----------------------------------------------------------------------

def send_schedule_update_email():
    recipients = get_reminder_emails()
    if not recipients:
        print("No recipients for schedule update email.")
        return

    subject = "Schedule Updated"
    body = (
        "Hello,\n\n"
        "The rehearsal schedule on StageSync has been updated.\n"
        "Please log in to check your updated availability and group assignments.\n\n"
        "Thanks,\nThe StageSync Team"
    )

    send_email_sendgrid(subject, recipients, body)

# ----------------------------------------------------------------------

def notify_admins_user_updated(netid):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.email
                    FROM users u
                    JOIN user_settings us ON u.netid = us.user_netid
                    WHERE u.is_admin = TRUE AND us.receive_availability_updates = TRUE
                """)
                rows = cur.fetchall()
                emails = [email for (email,) in rows]

        if not emails:
            return

        subject = f"{netid} Updated Availability"
        body = (
            f"Hello Admin,\n\n"
            f"User {netid} has just updated their availability on StageSync.\n"
            "You may want to review their status or regenerate the schedule if needed.\n\n"
            "Best,\nStageSync Notification"
        )

        send_email_sendgrid(subject, emails, body)

    except Exception as e:
        print(f"Failed to notify admins: {e}")
# ------------------------------------------------------------

def send_event_reminders():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:

                # Target events that begin exactly 1 day from now 
                cur.execute("""
                    SELECT e.title, e.start, e.location, u.email
                    FROM events e
                    JOIN group_members gm ON e.groupid = gm.groupid
                    JOIN user_settings us ON gm.netid = us.user_netid
                    JOIN users u ON gm.netid = u.netid
                    WHERE us.receive_reminders = TRUE
                    AND e.start BETWEEN NOW() + INTERVAL '23 hours' AND NOW() + INTERVAL '25 hours'
                """)
                rows = cur.fetchall()

        grouped = {}
        for title, start, location, email in rows:
            if email not in grouped:
                grouped[email] = []
            grouped[email].append((title, start, location))

        for email, events in grouped.items():
            message = "You have the following event(s) scheduled for tomorrow:\n\n"
            for title, start, location in events:
                local_time = convert_from_utc(start)
                message += f"- {title} at {local_time.strftime('%I:%M %p')} in {location}\n"
            message += "\nThanks,\nThe StageSync Team"
            send_email_sendgrid("Reminder: Tomorrow's Events", [email], message)

    except Exception as e:
        print(f"Error sending reminders: {e}")

# --------------------------------------------------------------------------------------------

def add_admin(netid):
    if not netid:
        return jsonify({"success": False, "message": "NetID is required"}), 400
    
    try:
        # Check if the user exists in the database
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT EXISTS(SELECT 1 FROM users WHERE netid = %s);
                """
                cur.execute(query, (netid,))
                exists = cur.fetchone()[0]

                if not exists:
                    return jsonify({"success": False, "message": "NetID does not exist"}), 400

                # Update the is_admin flag to True for the selected user
                update_query = """
                    UPDATE users
                    SET is_admin = TRUE
                    WHERE netid = %s;
                """
                cur.execute(update_query, (netid,))
                conn.commit()

        return jsonify({"success": True}), 200  # Return success with status code 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500  # Return error with status code 500


# ----------------------------------------------------------------------


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
