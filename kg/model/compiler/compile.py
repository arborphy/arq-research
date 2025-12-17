from __future__ import annotations

from typing import Any, Type, cast

import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table

from .dsl import EntitySpec, _Field


def _getattr_any(obj: Any, name: str) -> Any:
    return getattr(obj, name)


def _ensure_value_concept(m_any: Any, *, name: str, extends: Any | None, create: bool) -> Any:
    if not create:
        return _getattr_any(m_any, name)

    if hasattr(m_any, name):
        return _getattr_any(m_any, name)

    if extends is None:
        raise ValueError(f"Missing extends for value concept {name}")

    c = m_any.Concept(name, extends=[extends])
    setattr(m_any, name, c)
    return c


def _ensure_entity_concept(m_any: Any, *, entity: str, id_concept: Any) -> Any:
    if hasattr(m_any, entity):
        return _getattr_any(m_any, entity)

    c = m_any.Concept(entity, identify_by={"id": id_concept})
    setattr(m_any, entity, c)
    return c


def compile_entity(*, m: rai.Model, source: Table, spec: Type[EntitySpec]) -> None:
    """Compile a declarative entity spec into schema + bindings.

    This implements the *common case*:
    - create entity id concept
    - create entity concept identified by id
    - create functional properties and bind from source columns
    - create reference properties and bind via filter_by on target key

    Exceptions are handled by passing explicit column names / target info.
    """

    m_any = cast(Any, m)
    entity_name = spec.__entity__
    fields: dict[str, _Field] = dict(spec.__fields__)

    # 1) Identify the key field
    key_items = [(k, f) for k, f in fields.items() if f.kind == "key"]
    if len(key_items) != 1:
        raise ValueError(f"{entity_name} must have exactly one Key field; found {len(key_items)}")

    key_attr, key_field = key_items[0]
    if not key_field.column or not key_field.value_concept:
        raise ValueError(f"{entity_name}.{key_attr}: Key must declare column and id concept")

    id_concept = _ensure_value_concept(
        m_any,
        name=key_field.value_concept,
        extends=key_field.value_extends,
        create=True,
    )

    entity_concept = _ensure_entity_concept(m_any, entity=entity_name, id_concept=id_concept)

    # 2) Define properties/relationships on the entity concept
    for attr, field in fields.items():
        if field.kind == "key":
            continue

        if field.kind in ("prop", "ref"):
            rel_factory = m_any.Property if field.functional else m_any.Relationship
            rel = rel_factory(field.label)
            setattr(entity_concept, attr, rel)
        else:
            raise ValueError(f"Unknown field kind: {field.kind}")

        if field.kind == "prop":
            if not field.value_concept:
                raise ValueError(f"{entity_name}.{attr}: Prop must declare value_concept")
            _ensure_value_concept(
                m_any,
                name=field.value_concept,
                extends=field.value_extends,
                create=field.create_value_concept,
            )

    # 3) Bind from source
    id_col = _getattr_any(source, key_field.column)
    rai.define(entity_concept.new(id=id_col))
    row = rai.where(entity_concept.id == id_col)

    for attr, field in fields.items():
        if field.kind == "key":
            continue
        if not field.column:
            raise ValueError(f"{entity_name}.{attr}: missing column")

        if field.kind == "prop":
            col = _getattr_any(source, field.column)
            row.define(_getattr_any(entity_concept, attr)(col))
        elif field.kind == "ref":
            if not field.target:
                raise ValueError(f"{entity_name}.{attr}: Ref missing target")
            col = _getattr_any(source, field.column)
            target_concept = _getattr_any(m_any, field.target)
            row.define(_getattr_any(entity_concept, attr)(target_concept.filter_by(**{field.target_key: col})))
        else:
            raise ValueError(f"Unknown field kind: {field.kind}")
