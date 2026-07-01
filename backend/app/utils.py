import calendar
from datetime import date


def next_day_of_month(today: date, dom: int) -> date:
    """Next occurrence of a given day-of-month strictly after `today`."""
    y, m = today.year, today.month

    def make(yy, mm):
        last = calendar.monthrange(yy, mm)[1]
        return date(yy, mm, min(dom, last))

    cand = make(y, m)
    if cand <= today:
        m += 1
        if m > 12:
            m, y = 1, y + 1
        cand = make(y, m)
    return cand
