#!/usr/bin/env python

# ----------------------------------------------------------------------
# datetime_helpers.py
# Author: Kaitlyn Wen, Michael Igbinoba, Timothy Sim
#
# Description: contains helper functions for stagesync.py and
# db_helpers.py that deal with handling dates, timezones, etc.
# ----------------------------------------------------------------------

from datetime import datetime
from zoneinfo import ZoneInfo

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


# ----------------------------------------------------------------------


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


# Convert time to 24-hour format for PostgreSQL
def convert_to_24hr_format(time_str):
    return datetime.strptime(time_str, "%I:%M%p").strftime("%H:%M:%S")


# ----------------------------------------------------------------------


# Convert time to 12-hour format for html
def convert_to_12hr_format(time_str):
    return time_str.strftime("%I:%M %p").replace(" ", "")
