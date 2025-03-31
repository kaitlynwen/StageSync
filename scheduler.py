from datetime import datetime, timedelta
from collections import defaultdict
import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")

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
    return fetch_data("SELECT netid, day_of_week, start_time, end_time, is_recurring, one_time_date FROM availability")

def fetch_group_members():
    return fetch_data("SELECT groupid, netid FROM group_members")

def fetch_events():
    return fetch_data("SELECT id, title, start, \"end\", location, groupid FROM events")

# Preprocess Data
def preprocess_availability():
    raw_availability = fetch_availability()
    availability_dict = defaultdict(list)
    for netid, day, start, end, is_recurring, one_time_date in raw_availability:
        availability_dict[netid].append((day, start, end, is_recurring, one_time_date))
    return availability_dict

def sort_groups_by_priority():
    groups = fetch_rehearsal_groups()
    group_members = fetch_group_members()
    member_count = defaultdict(int)
    
    for groupid, _ in group_members:
        member_count[groupid] += 1
    
    return sorted(groups, key=lambda g: member_count[g[0]], reverse=True)
from datetime import datetime, timedelta

# Function to fetch events from the database, with start and end times in datetime format
def fetch_existing_events():
    query = "SELECT start, \"end\" FROM events"
    events = fetch_data(query)
    existing_event_times = []
    
    # Convert the fetched data into datetime objects for comparison
    for event in events:
        start_time, end_time = event
        existing_event_times.append({'start':start_time, 'end':end_time})
    
    return existing_event_times

def generate_available_slots(members, availability_dict):
    possible_slots = []
    # Fetch existing events' start and end times from the database
    existing_event_times = fetch_existing_events()
    current_date = datetime.today().date()

    for member in members:
        if member in availability_dict:
            for day, start, end, is_recurring, one_time_date in availability_dict[member]:
                # If the slot is recurring, add subsequent weeks
                if is_recurring:
                    # Convert member availability to datetime objects
                    member_event_date = convert_day_to_date(day)
                    member_start_datetime = datetime.combine(member_event_date, start)
                    member_end_datetime = datetime.combine(member_event_date, end)
                    
                    while member_event_date < current_date:
                        member_event_date += timedelta(weeks=1)
                    
                    for event in existing_event_times:
                        if event['start'].date() >= current_date:
                            new_member_date = member_event_date
                            for i in range(0,3): # arbitrary number of weeks
                                new_member_date += timedelta(weeks=1)
                                member_start_datetime = datetime.combine(new_member_date, start)
                                member_end_datetime = datetime.combine(new_member_date, end)

                                start_datetime = datetime.combine(event["start"].date(), event["start"].time())
                                end_datetime = datetime.combine(event["end"].date(), event["end"].time())
                                
                                # If this slot overlaps with the member's personal unavailable time, return False
                                cond1 = (member_start_datetime <= event['end']) and (event['end'] <= member_end_datetime)
                                cond2 = (member_start_datetime <= event['start']) and (event['start'] <= member_end_datetime)
                                
                                if (not cond1 and not cond2) or (member_start_datetime >= event['end']): 
                                    possible_slots.append((start_datetime, end_datetime))
    return possible_slots



# Function to convert the day of the week to the specific date
def convert_day_to_date(day_of_week):
    today = datetime.today()
    day_mapping = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
    
    current_weekday = today.weekday()
    target_weekday = day_mapping.get(day_of_week, None)
    
    if target_weekday is None:
        raise ValueError(f"Invalid day of the week: {day_of_week}")
    
    delta_days = target_weekday - current_weekday
    target_date = today + timedelta(days=delta_days)
    
    return target_date.date()


def assign_rehearsals():
    sorted_groups = sort_groups_by_priority()
    availability_dict = preprocess_availability()
    group_members = fetch_group_members()
    schedule = {}
    used_slots = {}  # Tracks assigned time slots

    for groupid, _ in sorted_groups:
        members = [netid for gid, netid in group_members if gid == groupid]
        
        # Generate available slots based on availability and existing events
        available_slots = generate_available_slots(members, availability_dict)

        if available_slots:
            for best_slot in available_slots:
                start, end = best_slot
                
                # Check if the time slot is already used
                conflict = any(
                    (s <= start < e or s < end <= e) for s, e in used_slots.values()
                )
                
                if not conflict:
                    schedule[groupid] = (start, end)
                    used_slots[groupid] = (start, end)  # Mark the slot as used
                    
                    # Remove this slot from the availability of all members
                    for member in members:
                        if member in availability_dict:
                            availability_dict[member] = [
                                slot for slot in availability_dict[member]
                                if not (start <= datetime.combine(start.date(), slot[1]) <= end)
                            ]
                    break  # Exit loop after assigning a valid slot
            else:
                # If no non-conflicting slots were found
                schedule[groupid] = "Manual Adjustment Required"
        else:
            schedule[groupid] = "Manual Adjustment Required"
            
    return schedule



def update_events_table(schedule):
    try:
        current_datetime = datetime.now()
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                for groupid, slot in schedule.items():
                    if slot != "Manual Adjustment Required":
                        event_start, event_end = slot
                        
                        # Fetch the group title
                        group_title = None
                        group_query = "SELECT title FROM rehearsal_groups WHERE groupid = %s"
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
                                SELECT id FROM events WHERE start = %s AND "end" = %s
                                """
                                cur.execute(event_query, (event_start, event_end))
                                existing_event = cur.fetchone()
                                if existing_event:
                                    # Event exists, so update it
                                    cur.execute(
                                        """
                                        UPDATE events
                                        SET title = %s, start = %s, "end" = %s
                                        WHERE start = %s AND "end" = %s
                                        """,
                                        (group_title, event_start, event_end, event_start, event_end)
                                    )
                                    conn.commit()
    except Exception as e:
        print(f"Database error while updating events: {e}")
