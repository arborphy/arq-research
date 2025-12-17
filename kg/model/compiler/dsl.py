from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Optional


@dataclass(frozen=True)
class _Field:
    kind: str
    label: str
    column: Optional[str] = None

    # Cardinality behavior
    # - functional=True  => Property (subject maps to at most one object)
    # - functional=False => Relationship (subject may map to many objects)
    functional: bool = True

    # Value concept behavior
    value_concept: Optional[str] = None
    value_extends: Optional[Any] = None  # typically rai.String / rai.Integer / ...
    create_value_concept: bool = True

    # Reference behavior (for edges to other entities)
    target: Optional[str] = None
    target_key: str = "id"

    # For entities
    identify_by: Optional[str] = None


class Key(_Field):
    def __init__(
        self,
        *,
        label: str,
        column: str,
        id_concept: str,
        id_extends: Any,
    ):
        super().__init__(
            kind="key",
            label=label,
            column=column,
            value_concept=id_concept,
            value_extends=id_extends,
            create_value_concept=True,
            identify_by="id",
        )


class Prop(_Field):
    def __init__(
        self,
        *,
        label: str,
        column: str,
        value_concept: str,
        value_extends: Any | None = None,
        create_value_concept: bool = True,
        functional: bool = True,
    ):
        super().__init__(
            kind="prop",
            label=label,
            column=column,
            functional=functional,
            value_concept=value_concept,
            value_extends=value_extends,
            create_value_concept=create_value_concept,
        )


class Ref(_Field):
    def __init__(
        self,
        *,
        label: str,
        column: str,
        target: str,
        target_key: str = "id",
        functional: bool = True,
    ):
        super().__init__(
            kind="ref",
            label=label,
            column=column,
            functional=functional,
            target=target,
            target_key=target_key,
        )


class Rel(Prop):
    """Non-functional value edge.

    Convenience wrapper around Prop(functional=False).
    """

    def __init__(
        self,
        *,
        label: str,
        column: str,
        value_concept: str,
        value_extends: Any | None = None,
        create_value_concept: bool = True,
    ):
        super().__init__(
            label=label,
            column=column,
            value_concept=value_concept,
            value_extends=value_extends,
            create_value_concept=create_value_concept,
            functional=False,
        )


class RelRef(Ref):
    """Non-functional reference edge.

    Convenience wrapper around Ref(functional=False).
    """

    def __init__(
        self,
        *,
        label: str,
        column: str,
        target: str,
        target_key: str = "id",
    ):
        super().__init__(
            label=label,
            column=column,
            target=target,
            target_key=target_key,
            functional=False,
        )


class EntitySpecMeta(type):
    def __new__(mcls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]):
        fields: Dict[str, _Field] = {}
        for base in bases:
            base_fields = getattr(base, "__fields__", None)
            if isinstance(base_fields, dict):
                fields.update(base_fields)

        for k, v in list(namespace.items()):
            if isinstance(v, _Field):
                fields[k] = v

        namespace["__fields__"] = fields
        if "__entity__" not in namespace:
            namespace["__entity__"] = name

        return super().__new__(mcls, name, bases, namespace)


class EntitySpec(metaclass=EntitySpecMeta):
    """Declarative spec for one entity concept.

    Subclasses declare fields as class attributes using Key/Prop/Ref.
    """

    __entity__: ClassVar[str]
    __fields__: ClassVar[Dict[str, _Field]]
