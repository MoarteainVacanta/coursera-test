"""Data model for the school timetable generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from typing import Optional


@dataclass(frozen=True)
class TimeSlot:
    day: str
    period: int  # index into School.periods

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.day} #{self.period}"


@dataclass
class Room:
    id: str
    name: str
    capacity: Optional[int] = None


@dataclass
class Teacher:
    id: str
    name: str
    subjects: list[str] = field(default_factory=list)
    unavailable: set[tuple[str, int]] = field(default_factory=set)
    max_lessons_per_day: Optional[int] = None


@dataclass
class SubjectRequirement:
    subject: str
    teacher: str  # Teacher.id
    hours_per_week: int
    room: Optional[str] = None  # preferred/required Room.id

    def max_per_day(self, num_days: int) -> int:
        """Spread lessons across the week: at most ceil(hours/days) per day."""
        return max(1, ceil(self.hours_per_week / max(1, num_days)))


@dataclass
class SchoolClass:
    id: str
    name: str
    subjects: list[SubjectRequirement] = field(default_factory=list)


@dataclass
class School:
    days: list[str]
    periods: list[str]
    rooms: list[Room] = field(default_factory=list)
    teachers: list[Teacher] = field(default_factory=list)
    classes: list[SchoolClass] = field(default_factory=list)

    @property
    def slots(self) -> list[TimeSlot]:
        return [
            TimeSlot(day, period_idx)
            for day in self.days
            for period_idx in range(len(self.periods))
        ]

    def teacher_by_id(self, teacher_id: str) -> Teacher:
        for t in self.teachers:
            if t.id == teacher_id:
                return t
        raise KeyError(f"Unknown teacher id: {teacher_id!r}")

    def room_by_id(self, room_id: str) -> Room:
        for r in self.rooms:
            if r.id == room_id:
                return r
        raise KeyError(f"Unknown room id: {room_id!r}")

    @classmethod
    def from_dict(cls, data: dict) -> "School":
        rooms = [Room(**r) for r in data.get("rooms", [])]

        teachers = []
        for t in data.get("teachers", []):
            unavailable = {tuple(pair) for pair in t.get("unavailable", [])}
            teachers.append(
                Teacher(
                    id=t["id"],
                    name=t["name"],
                    subjects=t.get("subjects", []),
                    unavailable=unavailable,
                    max_lessons_per_day=t.get("max_lessons_per_day"),
                )
            )

        classes = []
        for c in data.get("classes", []):
            reqs = [
                SubjectRequirement(
                    subject=s["subject"],
                    teacher=s["teacher"],
                    hours_per_week=s["hours_per_week"],
                    room=s.get("room"),
                )
                for s in c.get("subjects", [])
            ]
            classes.append(SchoolClass(id=c["id"], name=c["name"], subjects=reqs))

        return cls(
            days=data["days"],
            periods=data["periods"],
            rooms=rooms,
            teachers=teachers,
            classes=classes,
        )
