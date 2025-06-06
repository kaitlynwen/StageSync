from datetime import datetime, timedelta
from collections import defaultdict
import psycopg2
import os

from datetime_helpers import *

# ----------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

# ----------------------------------------------------------------------

# Fetch Data from Database
def fetch_data(query, params=(), warnings=None):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
    except Exception as e:
        msg = f"Database error: {e}"
        if warnings is not None:
            warnings.append((msg, "error"))
        else:
            print(msg)
        return []



def fetch_rehearsal_groups(warnings=None):
    return fetch_data("SELECT groupid, title FROM rehearsal_groups", warnings=warnings)


def fetch_availability(warnings=None):
    return fetch_data(
        "SELECT netid, day_of_week, start_time, end_time, is_recurring, one_time_date FROM availability",
        warnings=warnings
    )


def fetch_group_members(warnings=None):
    return fetch_data("SELECT groupid, netid FROM group_members", warnings=warnings)


def fetch_draft_schedule(warnings=None):
    return fetch_data(
        'SELECT id, title, start, "end", location, groupid FROM draft_schedule', warnings=warnings
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

                    # Convert start and end times to UTC and ensure they're aware
                    start_datetime_utc = add_utc_zone(start_datetime)
                    end_datetime_utc = add_utc_zone(end_datetime)

                    possible_slots.append((start_datetime_utc, end_datetime_utc, event["location"]))
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
                            member_start_datetime = datetime.combine(new_member_date, start.time())
                            member_end_datetime = datetime.combine(new_member_date, end.time())

                            # Convert member start/end times to UTC and ensure they're aware
                            member_start_datetime_utc = add_utc_zone(member_start_datetime)
                            member_end_datetime_utc = add_utc_zone(member_end_datetime)

                            start_datetime = datetime.combine(
                                event["start"].date(), event["start"].time()
                            )
                            end_datetime = datetime.combine(
                                event["end"].date(), event["end"].time()
                            )

                            # Convert event start/end times to UTC and ensure they're aware
                            event_start_utc = add_utc_zone(start_datetime)
                            event_end_utc = add_utc_zone(end_datetime)

                            if not is_conflicting(
                                member_start_datetime_utc, member_end_datetime_utc, event
                            ):
                                possible_slots.append(
                                    (event_start_utc, event_end_utc, event["location"])
                                )

            else:
                if one_time_date:
                    member_start_datetime = datetime.combine(one_time_date, start.time())
                    member_end_datetime = datetime.combine(one_time_date, end.time())

                    # Convert member start/end times to UTC and ensure they're aware
                    member_start_datetime_utc = add_utc_zone(member_start_datetime)
                    member_end_datetime_utc = add_utc_zone(member_end_datetime)


                    for event in possible_slots:
                        if event[0].date() == one_time_date:
                            conflict_found = is_conflicting(member_start_datetime_utc, member_end_datetime_utc, 
                                                            {'start':event[0],
                                                            'end':event[1],
                                                            'location':event[2]})

                            if conflict_found:
                                possible_slots.remove(event)

    return possible_slots


# ----------------------------------------------------------------------

def assign_rehearsals():
    warnings = []
    sorted_groups = sort_groups_by_priority()  # Prioritize groups by size
    unavailable_dict = preprocess_availability()
    group_members = fetch_group_members()
    schedule = {}
    group_available_slots = {}
    slots_remaining = True

    # Convert group_members into a dictionary for quick lookup
    group_members_dict = defaultdict(list)
    for gid, netid in group_members:
        group_members_dict[gid].append(netid)

    # Track the days each group has already been scheduled
    group_scheduled_days = defaultdict(set)

    # Assign available slots for each group
    missing_slot_groups = []

    for groupid, _ in sorted_groups:
        members = group_members_dict[groupid]
        available_slots = generate_available_slots(members, unavailable_dict)

        if not available_slots:
            missing_slot_groups.append(groupid)  # or fetch the name if needed

        group_available_slots[groupid] = list(set(available_slots))

    # After the loop, build one warning if needed
    if missing_slot_groups:
        group_titles = [
            fetch_data("SELECT title FROM rehearsal_groups WHERE groupid = %s", (gid,))[0][0]
            for gid in missing_slot_groups
        ]
        warnings.append((
            f"No available rehearsal slots could be found for the following groups: {', '.join(group_titles)}.", "warning"
        ))


    while slots_remaining:
        newly_scheduled = set()
        slots_remaining = False

        for groupid, _ in sorted_groups:
            available_slots = group_available_slots[groupid]

            if len(available_slots) > 0:
                # Check for a valid slot, making sure it's not already assigned on the same day
                selected_slot = None
                for slot in available_slots:
                    start, end, location = slot
                    slot_day = convert_from_utc(start).date()  # Get the date of the rehearsal slot
                    
                    # Check if the group already has a rehearsal scheduled on this day
                    conflict_found = False

                    for member in group_members_dict[groupid]:
                        conflicts = unavailable_dict.get(member, [])
                        for _, conflict_start, conflict_end, is_recurring, one_time_date in conflicts:
                            conflict_start = add_utc_zone(conflict_start)
                            conflict_end = add_utc_zone(conflict_end)

                            if not is_recurring and (slot_day == convert_from_utc(conflict_start).date()):
                                # One-time conflict
                                if is_conflicting(conflict_start, conflict_end, {"start": start, "end": end}):
                                    conflict_found = True
                                    break
                        if conflict_found:
                            break

                    if not conflict_found and slot_day not in group_scheduled_days[groupid]:
                        selected_slot = slot
                        break

                if selected_slot:
                    # Assign this slot to the group
                    start, end, location = selected_slot

                    if groupid not in schedule.keys():
                        schedule[groupid] = []
                    schedule[groupid].append((start, end, location))

                    # Mark this day as scheduled for the group
                    group_scheduled_days[groupid].add(start.date())

                    # Remove assigned slot from all groups
                    for other_group in sorted_groups:
                        if selected_slot in group_available_slots[other_group[0]]:
                            group_available_slots[other_group[0]].remove(selected_slot)

                    newly_scheduled.add(groupid)

                    if len(available_slots) > 0:
                        slots_remaining = True

                    # Add this slot to the conflicts of all members
                    for member in group_members_dict[groupid]:
                        if member in unavailable_dict:
                            start, end, location = selected_slot
                            unavailable_dict[member].append((None, start, end, False, start.date()))

        if not newly_scheduled:
            break
        
    return schedule, warnings


# ----------------------------------------------------------------------

def update_events_table(schedule):
    warnings = []
    try:
        current_datetime = datetime.now()
        current_datetime = convert_to_utc(current_datetime)
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
                                if event_start >= current_datetime:
                                    # Check if the event already exists
                                    event_query = """
                                    SELECT id, location FROM draft_schedule WHERE start = %s AND "end" = %s
                                    """
                                    cur.execute(event_query, (event_start, event_end))
                                    existing_event = cur.fetchone()
                                    if existing_event:
                                        cur.execute(
                                            """
                                            UPDATE draft_schedule
                                            SET title = %s, start = %s, "end" = %s, groupid = %s
                                            WHERE start = %s AND "end" = %s AND "location" = %s
                                            """,
                                            (
                                                group_title + " | " + existing_event[1],
                                                event_start,
                                                event_end,
                                                groupid,
                                                event_start,
                                                event_end,
                                                location,
                                            ),
                                        )
                                        conn.commit()
    except Exception as e:
        warnings.append((f"Database error while updating draft_schedule: {e}", "error"))

    return warnings
