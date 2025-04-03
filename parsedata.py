from datetime import datetime, timedelta
import io
import os
import pandas as pd
import re

########################################################################


def parse_time(time_str):
    """Convert a time string like '07:00PM' to a datetime object."""
    try:
        time_str = time_str.strip()
        return datetime.strptime(time_str, "%I:%M%p")
    except ValueError as e:
        print(f"Error parsing time: {e}")
        print(f"Time string that failed: {time_str}")
        return None  # Return None if there's a parsing error


########################################################################


def parse_time_range(time_range_str):
    """Parse a time range string like '07:00PM-07:30PM'."""
    start_time_str, end_time_str = time_range_str.split("-")

    start_time = parse_time(start_time_str.strip())
    end_time = parse_time(end_time_str.strip())

    return start_time, end_time


########################################################################


def adjust_event_date(event_date, start_time, end_time):
    """Adjust the event date if the end time crosses midnight."""
    # If the event ends exactly at midnight, we need to adjust the end date properly
    start_date = event_date
    end_date = event_date

    if end_time.hour == 0 and end_time.minute >= 0:
        end_date += timedelta(days=1)  # Shift to the next day

    if start_time.hour == 0 and start_time.minute >= 0:
        start_date += timedelta(days=1)  # Shift to the next day
        if start_date > end_date:
            end_date += timedelta(days=1)  # Shift to the next day

    return start_date, end_date


########################################################################


def combine_consecutive_slots(schedule):
    """Combine consecutive time slots into a single event."""
    combined_schedule = []

    schedule.sort(key=lambda x: (x["Location"], x["Start Date"], parse_time(x["Start"])))

    previous_event = None
    for event in schedule:
        if previous_event is None:
            previous_event = event
        else:
            prev_end_time = parse_time(previous_event["End"])
            current_start_time = parse_time(event["Start"])

            # Check if the events are consecutive (i.e., one ends exactly when the next starts)
            if (
                current_start_time == prev_end_time
                and event["Location"] == previous_event["Location"]
            ):
                # Combine events by updating the previous event's end time
                previous_event["End"] = event["End"]
                previous_event["End Date"] = event["End Date"]
            else:
                combined_schedule.append(previous_event)
                previous_event = event

    if previous_event is not None:
        combined_schedule.append(previous_event)

    return combined_schedule


########################################################################


def convert_schedule_to_calendar_events(schedule):
    """Convert schedule into FullCalendar event format using the Date and Time fields."""
    calendar_events = []

    for entry in schedule:
        start_date = datetime.strptime(entry["Start Date"], "%Y-%m-%d")
        end_date = datetime.strptime(entry["End Date"], "%Y-%m-%d")
        start_time = parse_time(entry["Start"])
        end_time = parse_time(entry["End"])

        start_datetime = datetime.combine(start_date.date(), start_time.time())
        end_datetime = datetime.combine(end_date.date(), end_time.time())

        calendar_events.append(
            {
                "title": entry["Location"],  # Use Location as title
                "start": start_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": end_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                "location": entry["Location"],
                "groupid": None
            }
        )

    return calendar_events


########################################################################

def extract_schedule(file, filename, group_name):
    warnings = []  # Store warnings to flash later
    
    # Extract date range
    date_range_match = re.search(r"\((\d{1,2}_\d{1,2}-\d{1,2}_\d{1,2})\)", filename)
    date_range = date_range_match.group(1) if date_range_match else "Unknown"

    try:
        start_date_str, end_date_str = date_range.split("-")
        start_date = datetime.strptime(start_date_str, "%m_%d").replace(year=datetime.now().year)
        end_date = datetime.strptime(end_date_str, "%m_%d").replace(year=datetime.now().year)
        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    except ValueError:
        warnings.append("Invalid date range format in filename.")
        dates = []

    # Read Excel File
    xl = pd.ExcelFile(io.BytesIO(file.read()))
    schedule = []

    for sheet_name in xl.sheet_names:
        if sheet_name.lower() == "info":
            continue

        df = xl.parse(sheet_name)
        df.dropna(how="all", subset=df.columns[1:], inplace=True)
        df = df.astype(str).fillna("")  # Replace NaN with empty string

        time_col = df.columns[0]  # First column is the time slots

        for col in df.columns[1:]:
            for idx, cell in df[col].items():
                if group_name.lower() in str(cell).lower():
                    try:
                        time_range = df[time_col][idx]
                        start_time, end_time = parse_time_range(time_range)

                        event_dates = [date for date in dates if date.strftime("%A").lower() == sheet_name.lower()]
                        if not event_dates:
                            warnings.append(f"Could not match sheet '{sheet_name}' to a valid date.")
                            continue

                        for event_date in event_dates:
                            start_date, end_date = adjust_event_date(event_date, start_time, end_time)
                            schedule.append({
                                "Start Date": start_date.strftime("%Y-%m-%d"),
                                "End Date": end_date.strftime("%Y-%m-%d"),
                                "Start": f"{start_time.strftime('%I:%M%p')}",
                                "End": f"{end_time.strftime('%I:%M%p')}",
                                "Location": col,
                                "GroupId": None,
                            })
                    except Exception as e:
                        warnings.append(f"Error processing row {idx} in sheet '{sheet_name}': {str(e)}")

    # Combine consecutive time slots
    schedule = combine_consecutive_slots(schedule)

    # Convert schedule into FullCalendar event format
    calendar_events = convert_schedule_to_calendar_events(schedule)

    return date_range, calendar_events, warnings


########################################################################

if __name__ == "__main__":
    # Ensure the file path is correct and exists
    file_path = "sample pac data/Spring Rehearsal Schedule (3_30-4_05).xlsx"  # Update if needed
    # file_path = "sample pac data/Spring Rehearsal Schedule (3_17-3_23).xlsx"  # Update if needed
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
    else:
        group_name = "kokopops"
        
        # Open the Excel file in binary mode ('rb') and pass it to extract_schedule
        with open(file_path, 'rb') as file:
            date_range, calendar_events, warnings = extract_schedule(file, file_path, group_name)

            # Output the results
            print(f"Schedule for {group_name} (Valid for {date_range}):\n")
            for event in calendar_events:
                print(f"Title: {event['title']} | Start: {event['start']} | End: {event['end']}")
