"""This module exports "breaking changes" related utilities."""

from __future__ import annotations

import builtins
import contextlib
import enum
from typing import Any, Iterable, Iterator, NewType, Union
from hashlib import sha256

from griffe.dataclasses import Alias, Attribute, Class, Function, Object, Parameter, ParameterKind
from griffe.expressions import Expression, Name

BUILTIN_NAMES = dir(builtins)
POSITIONAL = frozenset((ParameterKind.positional_only, ParameterKind.positional_or_keyword))

Reason = NewType("Reason", str)
Return = Union[str, Name, Expression, None]


class BreakageKind(enum.Enum):
    """An enumeration of the possible breakages."""

    PARAMETER_MOVED: str = "Positional parameter was moved"
    PARAMETER_REMOVED: str = "Parameter was removed"
    PARAMETER_CHANGED_KIND: str = "Parameter kind was changed to incompatible kind"
    PARAMETER_CHANGED_DEFAULT: str = "Parameter default was changed"
    PARAMETER_CHANGED_REQUIRED: str = "Parameter is now required"
    PARAMETER_ADDED_REQUIRED: str = "Required parameter was added"
    RETURN_CHANGED_TYPE: str = "Return types are incompatible"
    OBJECT_REMOVED: str = "Public name has been removed or changed"
    OBJECT_CHANGED_KIND: str = "Public name points to a different kind of object"
    ATTRIBUTE_CHANGED_TYPE: str = "Attribute types are incompatible"
    ATTRIBUTE_CHANGED_VALUE: str = "Attribute value was changed"
    CLASS_REMOVED_BASE: str = "Base class was removed"


class Severity(enum.Enum):
    """An enumeration of the possible breakage severities."""

    VERY_LOW: str = "very low"
    LOW: str = "low"
    MEDIUM: str = "medium"
    HIGH: str = "high"
    VERY_HIGH: str = "very high"

    def up(self):
        return {
            Severity.VERY_LOW: Severity.LOW,
            Severity.LOW: Severity.MEDIUM,
            Severity.MEDIUM: Severity.HIGH,
            Severity.HIGH: Severity.VERY_HIGH,
            Severity.VERY_HIGH: Severity.VERY_HIGH,
        }[self]

    def down(self):
        return {
            Severity.VERY_LOW: Severity.VERY_LOW,
            Severity.LOW: Severity.VERY_LOW,
            Severity.MEDIUM: Severity.LOW,
            Severity.HIGH: Severity.MEDIUM,
            Severity.VERY_HIGH: Severity.HIGH,
        }[self]

class Breakage:
    """Breakages can explain what broke from a version to another."""

    kind: BreakageKind
    default_severity: Severity

    def __init__(self, obj: Object, old_value: Any, new_value: Any, details: str = "") -> None:
        """Initialize the breakage.

        Parameters:
            obj: The object related to the breakage.
            old_value: The old value.
            new_value: The new, incompatible value.
        """
        self.obj = obj
        self.old_value = old_value
        self.new_value = new_value
        self.details = details

    def __str__(self) -> str:
        return f"{self.kind.value}"

    def __repr__(self) -> str:
        return f"<{self.kind.name}>"

    @property
    def severity(self) -> Severity:
        return self.default_severity

    def explain(self) -> str:
        """Explain the breakage by showing old and new value.

        Returns:
            An explanation.
        """
        return "\n".join((
            f"{self.obj.filepath}:{self.obj.lineno}: {self.obj.canonical_path}",
            f"{self.kind.value} ({self.severity.value} severity):",
            f"  Old: {self.old_value}",
            f"  New: {self.new_value}",
            f"  Details: {self.details}\n" if self.details else "",
        ))

    def as_dict(self, full: bool = False, **kwargs: Any) -> dict[str, Any]:
        """Return this object's data as a dictionary.

        Parameters:
            full: Whether to return full info, or just base info.
            **kwargs: Additional serialization options.

        Returns:
            A dictionary.
        """
        return {
            "kind": self.kind,
            "object_path": self.obj.path,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


class ParameterMovedBreakage(Breakage):
    """Specific breakage class for moved parameters."""

    kind: BreakageKind = BreakageKind.PARAMETER_MOVED
    default_severity: Severity = Severity.VERY_HIGH
    explanation: str = "The severity is {} because moving a parameter "
    "can silently break your users' code "
    "and lead to incorrect behavior without errors, "
    "making it harder to detect and fix potential issues."

    @property
    def severity(self) -> Severity:
        if self.old_value.default is None:
            return self.default_severity.up()


class ParameterRemovedBreakage(Breakage):
    """Specific breakage class for removed parameters."""

    kind: BreakageKind = BreakageKind.PARAMETER_REMOVED
    default_severity: Severity = Severity.MEDIUM
    explanation: str = "The severity is {} because removing a non-required parameter "
    "is an immediate (though visible) breakage for a part of your users' code."


class ParameterChangedKindBreakage(Breakage):
    """Specific breakage class for parameters whose kind changed."""

    kind: BreakageKind = BreakageKind.PARAMETER_CHANGED_KIND
    default_severity: Severity = Severity.MEDIUM
    explanation: str = "The severity is {} because changing the kind of a parameter "
    "(to positional/keyword -only) is an immediate (though visible) breakage for a part of your users' code."


class ParameterChangedDefaultBreakage(Breakage):
    """Specific breakage class for parameters whose default value changed."""

    kind: BreakageKind = BreakageKind.PARAMETER_CHANGED_DEFAULT
    default_severity: Severity = Severity.VERY_HIGH


class ParameterChangedRequiredBreakage(Breakage):
    """Specific breakage class for parameters which became required."""

    kind: BreakageKind = BreakageKind.PARAMETER_CHANGED_REQUIRED
    default_severity: Severity = Severity.MEDIUM


class ParameterAddedRequiredBreakage(Breakage):
    """Specific breakage class for new parameters added as required."""

    kind: BreakageKind = BreakageKind.PARAMETER_ADDED_REQUIRED
    default_severity: Severity = Severity.HIGH


class ReturnChangedTypeBreakage(Breakage):
    """Specific breakage class for return values which changed type.."""

    kind: BreakageKind = BreakageKind.RETURN_CHANGED_TYPE
    default_severity: Severity = Severity.MEDIUM


class ObjectRemovedBreakage(Breakage):
    """Specific breakage class for removed objects."""

    kind: BreakageKind = BreakageKind.OBJECT_REMOVED
    default_severity: Severity = Severity.MEDIUM


class ObjectChangedKindBreakage(Breakage):
    """Specific breakage class for objects whose kind changed."""

    kind: BreakageKind = BreakageKind.OBJECT_CHANGED_KIND
    default_severity: Severity = Severity.LOW


class AttributeChangedTypeBreakage(Breakage):
    """Specific breakage class for attributes whose type changed."""

    kind: BreakageKind = BreakageKind.ATTRIBUTE_CHANGED_TYPE
    default_severity: Severity = Severity.VERY_HIGH


class AttributeChangedValueBreakage(Breakage):
    """Specific breakage class for attributes whose value changed."""

    kind: BreakageKind = BreakageKind.ATTRIBUTE_CHANGED_VALUE
    default_severity: Severity = Severity.LOW


class ClassRemovedBaseBreakage(Breakage):
    """Specific breakage class for removed base classes."""

    kind: BreakageKind = BreakageKind.CLASS_REMOVED_BASE
    default_severity: Severity = Severity.LOW


# TODO: decorators!
def _class_incompatibilities(old_class: Class, new_class: Class, ignore_private: bool = True) -> Iterable[Breakage]:
    yield from ()  # noqa: WPS353
    if new_class.bases != old_class.bases:
        if len(new_class.bases) < len(old_class.bases):
            yield ClassRemovedBaseBreakage(new_class, old_class.bases, new_class.bases)
        else:
            # TODO: check mro
            ...
    yield from _member_incompatibilities(old_class, new_class, ignore_private=ignore_private)


# TODO: decorators!
def _function_incompatibilities(old_function: Function, new_function: Function) -> Iterator[Breakage]:  # noqa: WPS231
    new_param_names = [param.name for param in new_function.parameters]

    for old_index, old_param in enumerate(old_function.parameters):
        if old_param.name not in new_function.parameters:
            yield ParameterRemovedBreakage(new_function, old_param, None)
            continue

        new_param = new_function.parameters[old_param.name]
        if _is_param_required(new_param) and not _is_param_required(old_param):
            yield ParameterChangedRequiredBreakage(new_function, old_param, new_param)

        if old_param.kind in POSITIONAL:
            if new_param.kind not in POSITIONAL:
                yield ParameterChangedKindBreakage(new_function, old_param, new_param)
            else:
                new_index = new_param_names.index(old_param.name)
                if new_index != old_index:
                    details = f"position: from {old_index} to {new_index} ({new_index - old_index:+})"
                    yield ParameterMovedBreakage(new_function, old_param, new_param, details=details)

        breakage = ParameterChangedDefaultBreakage(new_function, old_param, new_param)
        try:
            if old_param.default != new_param.default:
                yield breakage
        except Exception:  # equality checks sometimes fail, e.g. numpy arrays
            # TODO: emitting breakage on a failed comparison could be a preference
            yield breakage

    for new_param in new_function.parameters:  # noqa: WPS440
        if new_param.name not in old_function.parameters and _is_param_required(new_param):
            yield ParameterAddedRequiredBreakage(new_function, None, new_param)

    if not _returns_are_compatible(old_function, new_function):
        yield ReturnChangedTypeBreakage(new_function, old_function.returns, new_function.returns)


def _attribute_incompatibilities(old_attribute: Attribute, new_attribute: Attribute) -> Iterable[Breakage]:
    # TODO: use beartype.peps.resolve_pep563 and beartype.door.is_subhint?
    # if old_attribute.annotation is not None and new_attribute.annotation is not None:
    #     if not is_subhint(new_attribute.annotation, old_attribute.annotation):
    #         yield AttributeChangedTypeBreakage(new_attribute, old_attribute.annotation, new_attribute.annotation)
    if old_attribute.value != new_attribute.value:
        yield AttributeChangedValueBreakage(new_attribute, old_attribute.value, new_attribute.value)


def _member_incompatibilities(  # noqa: WPS231
    old_obj: Object | Alias,
    new_obj: Object | Alias,
    ignore_private: bool = True,
) -> Iterator[Breakage]:
    for name, old_member in old_obj.members.items():
        if ignore_private and name.startswith("_"):
            continue

        try:
            new_member = new_obj.members[name]
        except KeyError:
            if old_member.is_exported(explicitely=False):
                yield ObjectRemovedBreakage(old_member, old_member, None)  # type: ignore[arg-type]
            continue

        if old_member.is_alias:
            continue  # TODO

        if new_member.kind != old_member.kind:
            yield ObjectChangedKindBreakage(new_member, old_member.kind, new_member.kind)  # type: ignore[arg-type]
        elif old_member.is_module:
            yield from _member_incompatibilities(old_member, new_member, ignore_private=ignore_private)  # type: ignore[arg-type]
        elif old_member.is_class:
            yield from _class_incompatibilities(old_member, new_member, ignore_private=ignore_private)  # type: ignore[arg-type]
        elif old_member.is_function:
            yield from _function_incompatibilities(old_member, new_member)  # type: ignore[arg-type]
        elif old_member.is_attribute:
            yield from _attribute_incompatibilities(old_member, new_member)  # type: ignore[arg-type]


def _is_param_required(param: Parameter) -> bool:
    return param.kind in POSITIONAL and param.default is None


def _returns_are_compatible(old_function: Function, new_function: Function) -> bool:
    if old_function.returns is None:
        return True
    if new_function.returns is None:
        # TODO: it should be configurable to allow/disallow removing a return type
        return False

    with contextlib.suppress(AttributeError):
        if new_function.returns == old_function.returns:
            return True

    # TODO: use beartype.peps.resolve_pep563 and beartype.door.is_subhint?
    return True


find_breaking_changes = _member_incompatibilities
