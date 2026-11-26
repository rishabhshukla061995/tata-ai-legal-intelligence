"""Turn extracted deadlines into real dates and an .ics calendar file."""
from datetime import date, datetime, timedelta, timezone
from typing import Optional


def schedule(deadlines: list[dict], start: date, end: Optional[date] = None, today: Optional[date] = None) -> list[dict]:
    """Add `due_date` (ISO string or None) and `status` to each deadline."""
    today = today or date.today()
    rows = []
    for d in deadlines or []:
        if not isinstance(d, dict):
            continue
        raw_days = d.get("days")
        days = None
        if isinstance(raw_days, (int, float)):
            days = int(raw_days)
        elif isinstance(raw_days, str) and raw_days.strip().lstrip("-").isdigit():
            days = int(raw_days.strip())
        anchor = str(d.get("anchor") or "event").lower().strip()
        due = None
        if days is not None:
            if anchor == "start":
                due = start + timedelta(days=days)
            elif anchor == "end" and end:
                due = end - timedelta(days=days)
        if due is None:
            status = "Event-based" if anchor == "event" else "Needs end date"
        elif due < today:
            status = "Passed"
        elif (due - today).days <= 30:
            status = "Due within 30 days"
        else:
            status = "Upcoming"
        rows.append({**d, "due_date": due.isoformat() if due else None, "status": status})
    rows.sort(key=lambda r: (r["due_date"] is None, r["due_date"] or ""))
    return rows


def _esc(text: str) -> str:
    return str(text or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def build_ics(rows: list[dict], contract: str = "Contract") -> str:
    """An iCalendar file (opens in Google Calendar, Outlook, Apple Calendar) with a
    reminder 3 days before each dated deadline."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Tata AI Legal//Deadlines//EN", "CALSCALE:GREGORIAN"]
    for i, r in enumerate(x for x in (rows or []) if isinstance(x, dict) and x.get("due_date")):
        try:
            day = str(r["due_date"]).replace("-", "")
            nxt = (date.fromisoformat(str(r["due_date"])) + timedelta(days=1)).strftime("%Y%m%d")
        except ValueError:
            continue
        lines += [
            "BEGIN:VEVENT",
            f"UID:{day}-{i}@tata-ai-legal",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{day}",
            f"DTEND;VALUE=DATE:{nxt}",
            f"SUMMARY:{_esc(contract)}: {_esc(r.get('term') or 'Deadline')}",
            f"DESCRIPTION:{_esc(r.get('description') or '')} [{_esc(r.get('source') or '')}]",
            "BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:Contract deadline", "TRIGGER:-P3D", "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
