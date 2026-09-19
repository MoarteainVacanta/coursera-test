import json
from collections import Counter
from pathlib import Path

import pytest

from scheduler.models import School
from scheduler.solver import Scheduler, SchedulingError

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_school.json"


def load_sample() -> School:
    data = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    return School.from_dict(data)


def test_sample_school_is_solvable():
    school = load_sample()
    scheduler = Scheduler(school, seed=1)
    lessons = scheduler.solve()

    total_hours = sum(req.hours_per_week for c in school.classes for req in c.subjects)
    assert len(lessons) == total_hours
    assert all(l.day is not None and l.room_id is not None or l.day is not None for l in lessons)


def test_no_class_double_booked():
    school = load_sample()
    lessons = Scheduler(school, seed=2).solve()

    seen = Counter((l.class_id, l.day, l.period) for l in lessons)
    assert all(count == 1 for count in seen.values())


def test_no_teacher_double_booked():
    school = load_sample()
    lessons = Scheduler(school, seed=3).solve()

    seen = Counter((l.teacher_id, l.day, l.period) for l in lessons)
    assert all(count == 1 for count in seen.values())


def test_no_room_double_booked():
    school = load_sample()
    lessons = Scheduler(school, seed=4).solve()

    seen = Counter((l.room_id, l.day, l.period) for l in lessons if l.room_id)
    assert all(count == 1 for count in seen.values())


def test_teacher_unavailability_respected():
    school = load_sample()
    lessons = Scheduler(school, seed=5).solve()

    for l in lessons:
        teacher = school.teacher_by_id(l.teacher_id)
        assert (l.day, l.period) not in teacher.unavailable


def test_teacher_daily_cap_respected():
    school = load_sample()
    lessons = Scheduler(school, seed=6).solve()

    per_day = Counter((l.teacher_id, l.day) for l in lessons)
    for teacher in school.teachers:
        if teacher.max_lessons_per_day is None:
            continue
        for day in school.days:
            assert per_day[(teacher.id, day)] <= teacher.max_lessons_per_day


def test_subject_hours_spread_across_week():
    school = load_sample()
    lessons = Scheduler(school, seed=7).solve()

    for sc in school.classes:
        for req in sc.subjects:
            cap = req.max_per_day(len(school.days))
            per_day = Counter(
                l.day for l in lessons if l.class_id == sc.id and l.subject == req.subject
            )
            assert all(count <= cap for count in per_day.values())


def test_correct_total_hours_per_class_subject():
    school = load_sample()
    lessons = Scheduler(school, seed=8).solve()

    for sc in school.classes:
        for req in sc.subjects:
            count = sum(1 for l in lessons if l.class_id == sc.id and l.subject == req.subject)
            assert count == req.hours_per_week


def test_unsolvable_school_raises():
    # Two classes both need a single shared teacher at the only available slot.
    school = School.from_dict(
        {
            "days": ["Luni"],
            "periods": ["08:00-08:50"],
            "rooms": [],
            "teachers": [{"id": "T1", "name": "Prof. X", "subjects": ["Matematica"]}],
            "classes": [
                {
                    "id": "C1",
                    "name": "Clasa A",
                    "subjects": [{"subject": "Matematica", "teacher": "T1", "hours_per_week": 1}],
                },
                {
                    "id": "C2",
                    "name": "Clasa B",
                    "subjects": [{"subject": "Matematica", "teacher": "T1", "hours_per_week": 1}],
                },
            ],
        }
    )
    with pytest.raises(SchedulingError):
        Scheduler(school, seed=1, max_attempts=2).solve()
