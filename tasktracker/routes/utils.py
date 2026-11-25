"""
Utility functions for routing modules.
"""

from datetime import datetime


def parse_datetime_string(datetime_str):
    """
    Parse datetime string from various formats.
    Args:
        datetime_str (str): Datetime string in formats like:
            "2026-01-01 12:00:00"
            "2026-01-01T12:00"
            "2026-01-01T12:00:00"

    Returns:
        datetime: Parsed datetime object

    Raises:
        ValueError: If the format is invalid
    """
    if "T" in datetime_str:
        datetime_str = datetime_str.replace("T", " ")
    if len(datetime_str) == 16:
        datetime_str += ":00"
    datetime_str = datetime_str[:19]
    return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")


def filter_tasks(tasks, status_filter="all", date_filter="all", now=None):
    now = now or datetime.now()
    filtered = []

    for task in tasks:
        # STATUS
        if status_filter == "completed" and not task.completed:
            continue
        if status_filter == "pending" and task.completed:
            continue

        # DATE
        deadline = task.deadline

        if date_filter == "today":
            if deadline.date() != now.date():
                continue

        elif date_filter == "week":
            diff = (deadline - now).total_seconds() / (60 * 60 * 24)
            if diff < 0 or diff > 7:
                continue

        filtered.append(task)

    return filtered
