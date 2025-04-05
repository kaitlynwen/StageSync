from datetime import datetime, timedelta
from collections import defaultdict
import psycopg2
import os

# ----------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

# ----------------------------------------------------------------------


# Fetch Data from Database
def fetch_data(query, params=()):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        return []


def fetch_rehearsal_groups():
    return fetch_data("SELECT groupid, title FROM rehearsal_groups")


def fetch_availability():
    return fetch_data(
        "SELECT netid, day_of_week, start_time, end_time, is_recurring, one_time_date FROM availability"
    )


def fetch_group_members():
    return fetch_data("SELECT groupid, netid FROM group_members")


def fetch_draft_schedule():
    return fetch_data(
        'SELECT id, title, start, "end", location, groupid FROM draft_schedule'
    )


# ----------------------------------------------------------------------


# Preprocess Data
def preprocess_availability():
    raw_availability = fetch_availability()
    unavailable_dict = defaultdict(list)

    for netid, day, start, end, is_recurring, one_time_date in raw_availability:
        unavailable_dict[netid].append((day, start, end, is_recurring, one_time_date))

    # add empty list for users with no entries (assumed to be available all the time)
    all_users = fetch_data("SELECT netid FROM users")
    for user in all_users:
        netid = user[0]
        if netid not in unavailable_dict:
            unavailable_dict[netid] = []

    return unavailable_dict


def sort_groups_by_priority():
    groups = fetch_rehearsal_groups()
    group_members = fetch_group_members()
    member_count = defaultdict(int)

    for groupid, _ in group_members:
        member_count[groupid] += 1

    return sorted(groups, key=lambda g: member_count[g[0]], reverse=True)


# ----------------------------------------------------------------------


# Function to fetch draft_schedule from the database, with start and end times in datetime format
def fetch_existing_draft_schedule():
    query = 'SELECT start, "end", location FROM draft_schedule'
    draft_schedule = fetch_data(query)
    existing_event_times = []

    # Convert the fetched data into datetime objects for comparison
    for event in draft_schedule:
        start_time, end_time, location = event
        existing_event_times.append(
            {"start": start_time, "end": end_time, "location": location}
        )

    return existing_event_times


# ----------------------------------------------------------------------


def is_conflicting(start_dt, end_dt, event):
    """
    Check if the given start and end time conflicts with an existing event.
    """
    cond1 = (start_dt <= event["end"]) and (event["end"] <= end_dt)
    cond2 = (start_dt <= event["start"]) and (event["start"] <= end_dt)

    return (cond1 and not cond2) or (start_dt < event["end"])


# ----------------------------------------------------------------------


def generate_available_slots(members, unavailable_dict):
    possible_slots = []
    # Fetch existing draft_schedule' start and end times from the database
    existing_event_times = fetch_existing_draft_schedule()
    current_date = datetime.today().date()

    for member in members:
        # check if a member is available all the time
        if member not in unavailable_dict or not unavailable_dict[member]:
            for event in existing_event_times:
                if event["start"].date() >= current_date:
                    start_datetime = datetime.combine(event["start"].date(), event["start"].time())
                    end_datetime = datetime.combine(event["end"].date(), event["end"].time())
                    possible_slots.append((start_datetime, end_datetime, event["location"]))
            continue

        # case that member has time conflicts
        for day, start, end, is_recurring, one_time_date in unavailable_dict[member]:
            # If the slot is recurring, add subsequent weeks
            if is_recurring:
                # Convert member availability to datetime objects
                member_event_date = convert_day_to_date(day)

                while member_event_date < current_date:
                    member_event_date += timedelta(weeks=1)

                for event in existing_event_times:
                    if event["start"].date() >= current_date:
                        new_member_date = member_event_date
                        for _ in range(3):  # arbitrary number of weeks
                            new_member_date += timedelta(weeks=1)
                            member_start_datetime = datetime.combine(
                                new_member_date, start
                            )
                            member_end_datetime = datetime.combine(new_member_date, end)

                            start_datetime = datetime.combine(
                                event["start"].date(), event["start"].time()
                            )
                            end_datetime = datetime.combine(
                                event["end"].date(), event["end"].time()
                            )

                            if not is_conflicting(
                                member_start_datetime, member_end_datetime, event
                            ):
                                possible_slots.append(
                                    (start_datetime, end_datetime, event["location"])
                                )

                    else:
                        if one_time_date:
                            member_start_datetime = datetime.combine(
                                one_time_date, start
                            )
                            member_end_datetime = datetime.combine(one_time_date, end)

                            conflict_found = any(
                                is_conflicting(
                                    member_start_datetime, member_end_datetime, event
                                )
                                for event in existing_event_times
                            )

                            start_datetime = datetime.combine(
                                event["start"].date(), event["start"].time()
                            )
                            end_datetime = datetime.combine(
                                event["end"].date(), event["end"].time()
                            )

                            if not conflict_found:
                                possible_slots.append(
                                    (start_datetime, end_datetime, event["location"])
                                )

    return possible_slots


# ----------------------------------------------------------------------


# Function to convert the day of the week to the specific date
def convert_day_to_date(day_of_week):
    today = datetime.today()
    day_mapping = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6,
    }

    current_weekday = today.weekday()
    target_weekday = day_mapping.get(day_of_week, None)

    if target_weekday is None:
        raise ValueError(f"Invalid day of the week: {day_of_week}")

    delta_days = target_weekday - current_weekday
    target_date = today + timedelta(days=delta_days)

    return target_date.date()


# ----------------------------------------------------------------------


def assign_rehearsals():
    sorted_groups = sort_groups_by_priority()  # Prioritize groups by size
    unavailable_dict = preprocess_availability()
    group_members = fetch_group_members()
    schedule = {}
    group_available_slots = {}
    slots_remaining = True

    # Open a file for logging
    log_file = open("debug_log.txt", "w")

    def log(message):
        """Helper function to write logs to file."""
        log_file.write(message + "\n")

    # Convert group_members into a dictionary for quick lookup
    group_members_dict = defaultdict(list)
    for gid, netid in group_members:
        group_members_dict[gid].append(netid)

    # Track the days each group has already been scheduled
    group_scheduled_days = defaultdict(set)

    # Assign available slots for each group
    for groupid, _ in sorted_groups:
        members = group_members_dict[groupid]
        available_slots = generate_available_slots(members, unavailable_dict)

        group_available_slots[groupid] = list(set(available_slots))

        log(
            f"Group {groupid} initial available slots ({len(group_available_slots[groupid])} slots): {group_available_slots[groupid]}"
        )

    while slots_remaining:
        newly_scheduled = set()
        slots_remaining = False

        for groupid, _ in sorted_groups:
            log(f"\nChecking group {groupid}")
            available_slots = group_available_slots[groupid]

            if len(available_slots) > 0:
                # Check for a valid slot, making sure it's not already assigned on the same day
                selected_slot = None
                for slot in available_slots:
                    start, end, location = slot
                    slot_day = start.date()  # Get the date of the rehearsal slot

                    # Check if the group already has a rehearsal scheduled on this day
                    if slot_day not in group_scheduled_days[groupid]:
                        selected_slot = slot
                        break

                if selected_slot:
                    # Assign this slot to the group
                    start, end, location = selected_slot
                    if groupid not in schedule.keys():
                        schedule[groupid] = []
                    schedule[groupid].append((start, end, location))

                    # Log the assigned slot
                    log(f"Group {groupid} assigned slot: {selected_slot}")

                    # Mark this day as scheduled for the group
                    group_scheduled_days[groupid].add(start.date())

                    # Remove assigned slot from all groups
                    for other_group in sorted_groups:
                        if selected_slot in group_available_slots[other_group[0]]:
                            log(
                                f"Removing slot {selected_slot} from group {other_group[0]} (before: {len(group_available_slots[other_group[0]])} slots)"
                            )
                            group_available_slots[other_group[0]].remove(selected_slot)
                            log(
                                f"Group {other_group[0]} now has {len(group_available_slots[other_group[0]])} slots remaining"
                            )

                    newly_scheduled.add(groupid)

                if len(available_slots) > 0:
                    slots_remaining = True

                # Add this slot to the conflicts of all members
                for member in group_members_dict[groupid]:
                    if member in unavailable_dict:
                        before_removal = len(unavailable_dict[member])
                        unavailable_dict[member].append(selected_slot)
                        after_removal = len(unavailable_dict[member])
                        log(
                            f"Updated availability for member {member}, before: {before_removal}, after: {after_removal}"
                        )

        if not newly_scheduled:
            log("\nNo new groups scheduled in this iteration, stopping loop.")
            break

        log(f"\nCurrent schedule: {schedule}")
        log(f"Remaining available slots: {group_available_slots}")

    log(f"\nFinal schedule: {schedule}")

    # Close the log file
    log_file.close()
    return schedule


# ----------------------------------------------------------------------


def update_events_table(schedule):
    try:
        current_datetime = datetime.now()
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                for groupid, slots in schedule.items():
                    for slot in slots:
                        if slot != "Manual Adjustment Required":
                            event_start, event_end, location = slot

                            # Fetch the group title
                            group_title = None
                            group_query = (
                                "SELECT title FROM rehearsal_groups WHERE groupid = %s"
                            )
                            cur.execute(group_query, (groupid,))
                            result = cur.fetchone()
                            if result:
                                group_title = result[0]

                            # If a group title was found, proceed with updating the event
                            if group_title:
                                # Only update the event if its start time is after the current time
                                if event_start >= current_datetime:
                                    # Check if the event already exists based on the start and end times (ignoring groupid)
                                    event_query = """
                                    SELECT id, location FROM draft_schedule WHERE start = %s AND "end" = %s
                                    """
                                    cur.execute(event_query, (event_start, event_end))
                                    existing_event = cur.fetchone()
                                    if existing_event:
                                        # Event exists, so update it
                                        cur.execute(
                                            """
                                            UPDATE draft_schedule
                                            SET title = %s, start = %s, "end" = %s
                                            WHERE start = %s AND "end" = %s AND "location" = %s
                                            """,
                                            (
                                                group_title + " | " + existing_event[1],
                                                event_start,
                                                event_end,
                                                event_start,
                                                event_end,
                                                location,
                                            ),
                                        )
                                        conn.commit()
    except Exception as e:
        print(f"Database error while updating draft_schedule: {e}")
