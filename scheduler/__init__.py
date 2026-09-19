"""Orar Scolar - whole-school timetable generator/optimizer."""

from .models import School, Teacher, Room, SchoolClass, SubjectRequirement
from .solver import Scheduler, SchedulingError

__all__ = [
    "School",
    "Teacher",
    "Room",
    "SchoolClass",
    "SubjectRequirement",
    "Scheduler",
    "SchedulingError",
]
