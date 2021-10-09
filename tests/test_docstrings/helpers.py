"""This module contains helpers for testing docstring parsing."""

from __future__ import annotations

from typing import Any, Callable, List, Tuple, Union

from griffe.dataclasses import Class, Data, Docstring, Function, Module
from griffe.docstrings.dataclasses import DocstringArgument, DocstringAttribute, DocstringElement, DocstringSection

ParentType = Union[Module, Class, Function, Data, None]
ParseResultType = Tuple[List[DocstringSection], List[str]]


def parser(parser_module) -> Callable[[str, ParentType, Any], ParseResultType]:
    """Wrap a parser to help testing.

    Arguments:
        parser_module: The parser module containing a `parse` function.

    Returns:
        The wrapped function.
    """

    def parse(docstring: str, parent: ParentType = None, **parser_opts: Any) -> ParseResultType:  # noqa: WPS430
        """Parse a doctring.

        Arguments:
            docstring: The docstring to parse.
            parent: The docstring's parent object.
            **parser_opts: Additional options accepted by the parser.

        Returns:
            The parsed sections, and warnings.
        """
        docstring_object = Docstring(docstring, lineno=1, endlineno=None)
        docstring_object.endlineno = len(docstring_object.lines) + 1
        if parent:
            docstring_object.parent = parent
            parent.docstring = docstring_object
        warnings = []
        parser_module._warn = lambda _docstring, _offset, message: warnings.append(message)  # noqa: WPS437
        sections = parser_module.parse(docstring_object, **parser_opts)
        return sections, warnings

    return parse  # type: ignore


def assert_argument_equal(actual: DocstringArgument, expected: DocstringArgument) -> None:
    """Help assert docstring arguments are equal.

    Arguments:
        actual: The actual argument.
        expected: The expected argument.
    """
    assert actual.name == expected.name
    assert_element_equal(actual, expected)
    assert actual.value == expected.value


def assert_attribute_equal(actual: DocstringAttribute, expected: DocstringAttribute) -> None:
    """Help assert docstring attributes are equal.

    Arguments:
        actual: The actual attribute.
        expected: The expected attribute.
    """
    assert actual.name == expected.name
    assert_element_equal(actual, expected)


def assert_element_equal(actual: DocstringElement, expected: DocstringElement) -> None:
    """Help assert docstring elements are equal.

    Arguments:
        actual: The actual element.
        expected: The expected element.
    """
    assert actual.annotation == expected.annotation
    assert actual.description == expected.description
