"""Export a solved timetable to CSV and HTML grids."""

from __future__ import annotations

import csv
import html
from pathlib import Path

from .models import School
from .solver import Lesson


def _cell_text(lesson: Lesson, school: School, *, show_class: bool) -> str:
    parts = [lesson.class_name if show_class else lesson.subject]
    if show_class:
        parts.append(lesson.subject)
    teacher = school.teacher_by_id(lesson.teacher_id)
    parts.append(teacher.name)
    if lesson.room_id:
        parts.append(school.room_by_id(lesson.room_id).name)
    return " / ".join(parts)


def _grid(school: School, lessons: list[Lesson], key: str, key_value: str) -> list[list[str]]:
    grid = [["" for _ in school.periods] for _ in school.days]
    day_index = {d: i for i, d in enumerate(school.days)}
    for lesson in lessons:
        if getattr(lesson, key) != key_value:
            continue
        text = _cell_text(lesson, school, show_class=(key == "teacher_id"))
        grid[day_index[lesson.day]][lesson.period] = text
    return grid


def write_csv(school: School, lessons: list[Lesson], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "timetable.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Class", "Day", "Period", "Subject", "Teacher", "Room"])
        for lesson in sorted(lessons, key=lambda l: (l.class_name, school.days.index(l.day), l.period)):
            teacher = school.teacher_by_id(lesson.teacher_id)
            room_name = school.room_by_id(lesson.room_id).name if lesson.room_id else ""
            writer.writerow([
                lesson.class_name,
                lesson.day,
                school.periods[lesson.period],
                lesson.subject,
                teacher.name,
                room_name,
            ])


def _grid_html(school: School, grid: list[list[str]], title: str) -> str:
    rows = []
    header = "".join(f"<th>{html.escape(p)}</th>" for p in school.periods)
    rows.append(f"<tr><th>Zi \\ Ora</th>{header}</tr>")
    for day, row in zip(school.days, grid):
        cells = "".join(f"<td>{html.escape(c) if c else ''}</td>" for c in row)
        rows.append(f"<tr><th>{html.escape(day)}</th>{cells}</tr>")
    return (
        f"<h2>{html.escape(title)}</h2>\n"
        f"<table class=\"timetable\">\n" + "\n".join(rows) + "\n</table>"
    )


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ font-family: sans-serif; margin: 2rem; color: #222; }}
  table.timetable {{ border-collapse: collapse; margin-bottom: 2rem; width: 100%; }}
  table.timetable th, table.timetable td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; font-size: 0.85rem; }}
  table.timetable th {{ background: #f0f0f0; }}
  nav a {{ margin-right: 1rem; }}
</style>
</head>
<body>
<h1>{title}</h1>
<nav>{nav}</nav>
{body}
</body>
</html>
"""


def write_html(school: School, lessons: list[Lesson], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    class_links = "".join(f'<a href="class_{c.id}.html">{html.escape(c.name)}</a>' for c in school.classes)
    teacher_links = "".join(f'<a href="teacher_{t.id}.html">{html.escape(t.name)}</a>' for t in school.teachers)
    nav = f"<strong>Clase:</strong> {class_links} &nbsp; <strong>Profesori:</strong> {teacher_links}"

    for sc in school.classes:
        grid = _grid(school, lessons, "class_id", sc.id)
        body = _grid_html(school, grid, f"Orar - {sc.name}")
        page = _PAGE_TEMPLATE.format(title=f"Orar - {sc.name}", nav=nav, body=body)
        (output_dir / f"class_{sc.id}.html").write_text(page, encoding="utf-8")

    for t in school.teachers:
        grid = _grid(school, lessons, "teacher_id", t.id)
        body = _grid_html(school, grid, f"Orar profesor - {t.name}")
        page = _PAGE_TEMPLATE.format(title=f"Orar profesor - {t.name}", nav=nav, body=body)
        (output_dir / f"teacher_{t.id}.html").write_text(page, encoding="utf-8")

    index_body = "<p>Selecteaza o clasa sau un profesor din meniul de mai sus.</p>"
    index_page = _PAGE_TEMPLATE.format(title="Orar scolar", nav=nav, body=index_body)
    (output_dir / "index.html").write_text(index_page, encoding="utf-8")
