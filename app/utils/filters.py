from datetime import datetime

def datetime_filter(value):
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    return datetime.fromisoformat(value).strftime("%H:%M")

def format_time(hours):
    if not isinstance(hours, (int, float)) or hours < 0:
        return "00:00"
    return f"{int(hours):02d}:{int((hours % 1) * 60):02d}"

filters = {
    "datetime": datetime_filter,
    "format_time": format_time
}
