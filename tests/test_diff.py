"""Tests for the `diff` module."""

import pytest

from griffe.diff import BreakageKind, find_breaking_changes
from tests.helpers import temporary_visited_module


@pytest.mark.parametrize(
    ("old_code", "new_code", "expected_breakages"),
    [
        # (
        #     "var: int",
        #     "var: str",
        #     [BreakageKind.ATTRIBUTE_CHANGED_TYPE],
        # ),
        (
            "a = True",
            "a = False",
            [BreakageKind.ATTRIBUTE_CHANGED_VALUE],
        ),
        (
            "class A(int, str): ...",
            "class A(int): ...",
            [BreakageKind.CLASS_REMOVED_BASE],
        ),
        (
            "A = 0",
            "class A: ...",
            [BreakageKind.OBJECT_CHANGED_KIND],
        ),
        (
            "a = True",
            "",
            [BreakageKind.OBJECT_REMOVED],
        ),
        (
            "def a(): ...",
            "def a(x): ...",
            [BreakageKind.PARAMETER_ADDED_REQUIRED],
        ),
        (
            "def a(x=0): ...",
            "def a(x=1): ...",
            [BreakageKind.PARAMETER_CHANGED_DEFAULT],
        ),
        (
            "def a(x): ...",
            "def a(*, x): ...",
            [BreakageKind.PARAMETER_CHANGED_KIND],
        ),
        (
            "def a(x=1): ...",
            "def a(x): ...",
            [BreakageKind.PARAMETER_CHANGED_REQUIRED],
        ),
        (
            "def a(x, y): ...",
            "def a(y, x): ...",
            [BreakageKind.PARAMETER_MOVED],
        ),
        (
            "def a(x, y): ...",
            "def a(x): ...",
            [BreakageKind.PARAMETER_REMOVED],
        ),
        (
            "def a() -> int: ...",
            "def a() -> str: ...",
            [BreakageKind.RETURN_CHANGED_TYPE],
        ),
    ],
)
def test_diff_griffe(old_code, new_code, expected_breakages):
    """Test the different incompatibility finders.

    Parameters:
        old_code: Parametrized code of the old module version.
        new_code: Parametrized code of the new module version.
        expected_breakages: A list of breakage kinds to expect.
    """
    with temporary_visited_module(old_code) as old_module:
        with temporary_visited_module(new_code) as new_module:
            breaking = list(find_breaking_changes(old_module, new_module))
    for breakage, expected_kind in zip(breaking, expected_breakages):
        assert breakage.kind is expected_kind
