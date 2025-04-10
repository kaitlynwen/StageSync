#!/usr/bin/env python

# ----------------------------------------------------------------------
# export_cal.py
# Authors: Kaitlyn Wen, Michael Igbinoba, Timothy Sim
# ----------------------------------------------------------------------

import os
import psycopg2
from ics import Calendar, Event
from datetime import datetime, timezone

# ----------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")
CURRENT_DATETIME = datetime.now(timezone.utc)

# ----------------------------------------------------------------------

def get_calendar_events():
    """Fetch all calendar events occurring on or after the current date."""
    calendar_events = []
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                query = 'SELECT title, start, "end", location FROM events WHERE start >= %s'
                cur.execute(query, (CURRENT_DATETIME,))
                for title, start, end, location in cur.fetchall():
                    calendar_events.append(
                        {
                            "name": title,
                            "begin": start,
                            "end": end,
                            "location": location
                        }
                    )

    except Exception as ex:
        print("Database error:", ex)

    return calendar_events

# ----------------------------------------------------------------------

if __name__ == "__main__":
    calendar_events = get_calendar_events()

    calendar = Calendar()

    for e in calendar_events:
        event = Event()
        event.name = e["name"]
        event.begin = e["begin"]
        event.end = e["end"]
        event.location = e["location"]
        calendar.events.add(event)

    with open('rehearsals.ics', 'w') as f:
        f.write(calendar.serialize())

