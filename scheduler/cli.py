"""Command-line interface for the school timetable generator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import School
from .report import write_csv, write_html
from .solver import Scheduler, SchedulingError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orar",
        description="Generate a conflict-free whole-school weekly timetable.",
    )
    parser.add_argument("--input", "-i", type=Path, default=Path("data/sample_school.json"),
                         help="Path to the school definition JSON file.")
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("output"),
                         help="Directory to write the generated CSV/HTML timetable to.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    parser.add_argument("--max-attempts", type=int, default=25,
                         help="Number of restart attempts before giving up.")
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 1

    data = json.loads(args.input.read_text(encoding="utf-8"))
    school = School.from_dict(data)

    scheduler = Scheduler(school, seed=args.seed, max_attempts=args.max_attempts)
    try:
        lessons = scheduler.solve()
    except SchedulingError as exc:
        print(f"Failed to generate a timetable: {exc}", file=sys.stderr)
        return 2

    write_csv(school, lessons, args.output_dir)
    write_html(school, lessons, args.output_dir)

    print(f"Generated timetable for {len(school.classes)} class(es), "
          f"{len(school.teachers)} teacher(s): {len(lessons)} lessons placed.")
    print(f"Output written to {args.output_dir}/ (timetable.csv, index.html, ...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
