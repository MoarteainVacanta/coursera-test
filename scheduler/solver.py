"""Constraint-based backtracking solver for the school timetable problem.

Hard constraints enforced:
  * a class never has two lessons in the same slot
  * a teacher never teaches two lessons in the same slot
  * a teacher is never scheduled during a declared-unavailable slot
  * a room never hosts two lessons in the same slot
  * a teacher's daily lesson count never exceeds ``max_lessons_per_day``
  * a subject's lessons for a given class are spread across the week
    (at most ``ceil(hours_per_week / num_days)`` per day), so e.g. a
    4-hour/week subject isn't dumped entirely into one day.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from .models import School, TimeSlot


class SchedulingError(Exception):
    """Raised when no feasible timetable could be found."""


@dataclass
class Lesson:
    class_id: str
    class_name: str
    subject: str
    teacher_id: str
    fixed_room: Optional[str]
    seq: int  # which weekly occurrence of this subject (0-based)
    max_per_day: int

    day: Optional[str] = None
    period: Optional[int] = None
    room_id: Optional[str] = None

    @property
    def slot(self) -> Optional[TimeSlot]:
        if self.day is None:
            return None
        return TimeSlot(self.day, self.period)


class _AttemptExhausted(Exception):
    """Internal signal: this attempt used up its search-step budget."""


class Scheduler:
    def __init__(self, school: School, seed: Optional[int] = None, max_attempts: int = 25,
                 max_steps_per_attempt: int = 150_000):
        self.school = school
        self.rng = random.Random(seed)
        self.max_attempts = max_attempts
        self.max_steps_per_attempt = max_steps_per_attempt

    def _build_lessons(self) -> list[Lesson]:
        lessons: list[Lesson] = []
        num_days = len(self.school.days)
        for sc in self.school.classes:
            for req in sc.subjects:
                max_per_day = req.max_per_day(num_days)
                for seq in range(req.hours_per_week):
                    lessons.append(
                        Lesson(
                            class_id=sc.id,
                            class_name=sc.name,
                            subject=req.subject,
                            teacher_id=req.teacher,
                            fixed_room=req.room,
                            seq=seq,
                            max_per_day=max_per_day,
                        )
                    )
        return lessons

    def solve(self) -> list[Lesson]:
        base_lessons = self._build_lessons()
        if not base_lessons:
            return []

        room_ids = [r.id for r in self.school.rooms]

        last_error: Optional[str] = None
        for attempt in range(self.max_attempts):
            lessons = [
                Lesson(l.class_id, l.class_name, l.subject, l.teacher_id,
                       l.fixed_room, l.seq, l.max_per_day)
                for l in base_lessons
            ]
            self.rng.shuffle(lessons)
            steps = [0]
            try:
                ok = self._backtrack(lessons, room_ids, steps)
            except _AttemptExhausted:
                ok = False
            if ok:
                lessons.sort(key=lambda l: (l.class_id, l.subject, l.seq))
                return lessons
            last_error = self._diagnose(lessons, room_ids)

        raise SchedulingError(
            "Could not find a conflict-free timetable after "
            f"{self.max_attempts} attempts. Last diagnostic: {last_error}"
        )

    # -- backtracking core -------------------------------------------------

    def _backtrack(self, lessons: list[Lesson], room_ids: list[str], steps: list[int]) -> bool:
        class_occ: set[tuple[str, str, int]] = set()
        teacher_occ: set[tuple[str, str, int]] = set()
        room_occ: set[tuple[str, str, int]] = set()
        subject_day_count: dict[tuple[str, str, str], int] = defaultdict(int)
        teacher_day_count: dict[tuple[str, str], int] = defaultdict(int)

        unassigned = list(range(len(lessons)))

        def candidates(idx: int) -> list[tuple[str, int, Optional[str]]]:
            lesson = lessons[idx]
            teacher = self.school.teacher_by_id(lesson.teacher_id)
            out = []
            for day in self.school.days:
                if subject_day_count[(lesson.class_id, lesson.subject, day)] >= lesson.max_per_day:
                    continue
                if teacher.max_lessons_per_day is not None and (
                    teacher_day_count[(lesson.teacher_id, day)] >= teacher.max_lessons_per_day
                ):
                    continue
                for period in range(len(self.school.periods)):
                    if (day, period) in teacher.unavailable:
                        continue
                    if (lesson.class_id, day, period) in class_occ:
                        continue
                    if (lesson.teacher_id, day, period) in teacher_occ:
                        continue
                    if lesson.fixed_room:
                        if (lesson.fixed_room, day, period) in room_occ:
                            continue
                        out.append((day, period, lesson.fixed_room))
                    elif room_ids:
                        free_room = next(
                            (r for r in room_ids if (r, day, period) not in room_occ), None
                        )
                        if free_room is None:
                            continue
                        out.append((day, period, free_room))
                    else:
                        out.append((day, period, None))
            return out

        def place(idx: int, day: str, period: int, room: Optional[str]) -> None:
            lesson = lessons[idx]
            lesson.day, lesson.period, lesson.room_id = day, period, room
            class_occ.add((lesson.class_id, day, period))
            teacher_occ.add((lesson.teacher_id, day, period))
            if room:
                room_occ.add((room, day, period))
            subject_day_count[(lesson.class_id, lesson.subject, day)] += 1
            teacher_day_count[(lesson.teacher_id, day)] += 1

        def unplace(idx: int) -> None:
            lesson = lessons[idx]
            day, period, room = lesson.day, lesson.period, lesson.room_id
            class_occ.discard((lesson.class_id, day, period))
            teacher_occ.discard((lesson.teacher_id, day, period))
            if room:
                room_occ.discard((room, day, period))
            subject_day_count[(lesson.class_id, lesson.subject, day)] -= 1
            teacher_day_count[(lesson.teacher_id, day)] -= 1
            lesson.day = lesson.period = lesson.room_id = None

        def recurse(remaining: list[int]) -> bool:
            steps[0] += 1
            if steps[0] > self.max_steps_per_attempt:
                raise _AttemptExhausted()
            if not remaining:
                return True

            # MRV: pick the unassigned lesson with the fewest legal candidates.
            best_idx = None
            best_candidates = None
            for idx in remaining:
                cands = candidates(idx)
                if best_candidates is None or len(cands) < len(best_candidates):
                    best_idx, best_candidates = idx, cands
                    if not cands:
                        break

            if not best_candidates:
                return False

            self.rng.shuffle(best_candidates)
            rest = [i for i in remaining if i != best_idx]
            for day, period, room in best_candidates:
                place(best_idx, day, period, room)
                if recurse(rest):
                    return True
                unplace(best_idx)
            return False

        return recurse(unassigned)

    def _diagnose(self, lessons: list[Lesson], room_ids: list[str]) -> str:
        unplaced = [l for l in lessons if l.day is None]
        if not unplaced:
            return "no unplaced lessons (constraint violated some other way)"
        sample = unplaced[0]
        return (
            f"{len(unplaced)} lesson(s) unplaced, e.g. class {sample.class_name!r} "
            f"subject {sample.subject!r} (teacher {sample.teacher_id!r})"
        )
