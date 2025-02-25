from datetime import date, datetime


def get_date_timestamp(target_date: date) -> int:
    # Convert today's date to a datetime object (with time set to 00:00:00)
    today_datetime = datetime.combine(target_date, datetime.min.time())

    # Get the integer timestamp (seconds since Unix epoch)
    timestamp = int(today_datetime.timestamp()) * 1000
    return timestamp


def timestamp_to_date(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp / 1000).date()