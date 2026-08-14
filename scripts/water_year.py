"""Water year starts Nov 1. WY 2026 = Nov 1 2025 through Oct 31 2026."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")


def today_pacific():
    return datetime.now(PACIFIC).date()


def water_year_start_end(today=None):
    """Return (start_year, end_year), e.g. (2025, 2026) on Aug 14, 2026."""
    today = today or today_pacific()
    start = today.year if today.month >= 11 else today.year - 1
    return start, start + 1


def year_column_for_mmdd(mmdd, start_year, end_year):
    """NRCS POR columns are calendar years; Nov–Dec live in start_year."""
    month = int(str(mmdd).split("-")[0])
    return str(start_year if month >= 11 else end_year)


def plot_year_column(common_years, end_year):
    """Prefer the current WY ending year; ignore an empty next-year column."""
    years = [int(y) for y in common_years]
    if end_year in years:
        return str(end_year)
    prior = [y for y in years if y <= end_year]
    return str(max(prior) if prior else common_years[-1])


def entry_num(entry, key):
    if key not in entry or entry[key] is None:
        return None
    try:
        value = float(entry[key])
    except (ValueError, TypeError):
        return None
    if value != value:  # NaN
        return None
    return value


def obs_date(mmdd, start_year, end_year):
    month, day = map(int, str(mmdd).split("-"))
    year = start_year if month >= 11 else end_year
    return date(year, month, day)


def latest_in_water_year(json_data, start_year, end_year, today):
    """Latest MM-DD in the current water year with a numeric value, not after today."""
    latest_d = None
    latest_date = None
    latest_value = None
    for entry in json_data:
        mmdd = entry.get("date")
        if not mmdd:
            continue
        col = year_column_for_mmdd(mmdd, start_year, end_year)
        value = entry_num(entry, col)
        if value is None:
            continue
        try:
            obs = obs_date(mmdd, start_year, end_year)
        except ValueError:
            continue
        if obs > today:
            continue
        if latest_d is None or obs > latest_d:
            latest_d = obs
            latest_date = mmdd
            latest_value = value
    return latest_date, latest_value


if __name__ == "__main__":
    assert water_year_start_end(date(2025, 11, 1)) == (2025, 2026)
    assert water_year_start_end(date(2025, 10, 31)) == (2024, 2025)
    assert water_year_start_end(date(2026, 8, 14)) == (2025, 2026)
    assert water_year_start_end(date(2026, 11, 1)) == (2026, 2027)
    assert year_column_for_mmdd("11-15", 2025, 2026) == "2025"
    assert year_column_for_mmdd("12-31", 2025, 2026) == "2025"
    assert year_column_for_mmdd("01-15", 2025, 2026) == "2026"
    assert plot_year_column(["2024", "2025", "2026", "2027"], 2026) == "2026"
    assert plot_year_column(["2024", "2025"], 2026) == "2025"
    assert year_column_for_mmdd("11-01", 2026, 2027) == "2026"

    rows = [
        {"date": "11-01", "2024": 1.0, "2025": 10.0, "2026": None},
        {"date": "11-15", "2024": 2.0, "2025": 12.0, "2026": None},
        {"date": "01-15", "2024": 5.0, "2025": 20.0, "2026": 30.0},
    ]
    # Old precip code only read the 2026 column and would miss Nov–Dec
    assert latest_in_water_year(rows, 2025, 2026, date(2025, 11, 20)) == ("11-15", 12.0)
    assert latest_in_water_year(rows, 2025, 2026, date(2026, 1, 20)) == ("01-15", 30.0)
    assert latest_in_water_year(rows, 2025, 2026, date(2025, 11, 10)) == ("11-01", 10.0)
    print("water_year ok")
