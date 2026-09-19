# Orar Scolar - School Timetable Generator

A whole-school timetable generator/optimizer. Given a list of classes, teachers,
rooms, and weekly subject-hour requirements, it produces a conflict-free
weekly schedule: no class, teacher, or room is ever double-booked, teacher
unavailability is respected, and each subject's hours are spread across the
week rather than crammed into one day.

Pure Python standard library - no external dependencies to run the generator.

## How it works

The problem is modeled as a constraint-satisfaction problem:

- Every `(class, subject)` requirement with `hours_per_week: N` expands into
  `N` individual lessons that need a `(day, period, room)` slot.
- A backtracking search assigns slots to lessons, using a most-constrained-
  variable heuristic (the lesson with the fewest legal remaining slots is
  placed first) with forward checking, so conflicts are caught immediately
  instead of at the end of a search branch.
- Hard constraints enforced: no class/teacher/room double-booking, teacher
  unavailability windows, an optional per-teacher daily lesson cap, and a
  per-subject daily cap (`ceil(hours_per_week / num_days)`) so a subject's
  hours don't all land on the same day.
- If a search gets stuck, the solver restarts with a reshuffled lesson order
  (up to `--max-attempts` times) before reporting which lessons couldn't be
  placed.

See `scheduler/solver.py` for the implementation.

## Usage

```bash
# Generate a timetable from the sample school definition
python3 -m scheduler.cli --input data/sample_school.json --output-dir output --seed 42

# Run the test suite
pip install pytest
python3 -m pytest
```

This writes to `output/`:

- `timetable.csv` - flat list of every lesson (class, day, period, subject, teacher, room)
- `index.html`, `class_<id>.html`, `teacher_<id>.html` - browsable weekly grids per class and per teacher

## Defining a school

Input is a JSON file (see `data/sample_school.json` for a full example):

```json
{
  "days": ["Luni", "Marti", "Miercuri", "Joi", "Vineri"],
  "periods": ["08:00-08:50", "09:00-09:50"],
  "rooms": [{ "id": "R1", "name": "Sala 101", "capacity": 30 }],
  "teachers": [
    {
      "id": "T1",
      "name": "Prof. Ionescu",
      "subjects": ["Matematica"],
      "unavailable": [["Vineri", 5]],
      "max_lessons_per_day": 4
    }
  ],
  "classes": [
    {
      "id": "C1",
      "name": "Clasa a V-a A",
      "subjects": [
        { "subject": "Matematica", "teacher": "T1", "hours_per_week": 4, "room": "R1" }
      ]
    }
  ]
}
```

`room` on a subject requirement pins that subject to a specific room; omit it
to let the solver pick any free room from `rooms` at each slot. `unavailable`
and `max_lessons_per_day` on a teacher are optional.

## Project layout

- `scheduler/models.py` - data model (`School`, `Teacher`, `Room`, `SchoolClass`, `SubjectRequirement`)
- `scheduler/solver.py` - the backtracking CSP solver
- `scheduler/report.py` - CSV/HTML export
- `scheduler/cli.py` - command-line entry point
- `data/sample_school.json` - example input (3 classes, 6 teachers, 4 rooms)
- `tests/test_solver.py` - conflict-freedom and constraint tests
