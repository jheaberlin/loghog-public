from datetime import datetime
from .convert_tz import convert_to_utc


def try_int(value):
    try:
        return int(value), True
    except Exception:
        return value, False

def try_float(value):
    try:
        return float(value), True
    except Exception:
        return value, False

def try_list(value):
    try:
        if value.startswith('[') and value.endswith(']'):
            return eval(value, {"__builtins__":{}}, {}), True
    except Exception:
        pass
    return value, False

def try_dict(value):
    try:
        if value.startswith('{') and value.endswith('}'):
            return eval(value, {"__builtins__":{}}, {}), True
    except Exception:
        pass
    return value, False

def try_datetime(value, user_timezone):
    try:
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return convert_to_utc(dt, user_timezone), True
    except Exception:
        return value, False

def convert_type(value, user_timezone):
    for func in [try_int, try_float, try_list, try_dict, lambda v: try_datetime(v, user_timezone)]:
        value, success = func(value)
        if success:
            break
    return value