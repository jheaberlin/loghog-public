import pytz

def convert_tz(dt, timezone):
    return dt.astimezone(pytz.timezone(timezone)).strftime("%Y-%m-%d %H:%M:%S")

def convert_to_utc(dt, current_timezone):
    # Ensure the datetime is aware by setting its timezone
    local_timezone = pytz.timezone(current_timezone)
    local_dt = local_timezone.localize(dt) if dt.tzinfo is None else dt.astimezone(local_timezone)
    # Convert the datetime to UTC
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt