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


def _ensure_entity_concept_identify_by(m_any: Any, *, entity: str, identify_by: dict[str, Any]) -> Any:
    if hasattr(m_any, entity):
        return _getattr_any(m_any, entity)

    c = m_any.Concept(entity, identify_by=identify_by)
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

    composite_identify_by = getattr(spec, "__identify_by__", None)
    composite_identity_attrs: set[str] = set(composite_identify_by or {})

    # 1) Identify the entity identity
    key_items = [(k, f) for k, f in fields.items() if f.kind == "key"]
    if composite_identify_by is not None and len(key_items) > 0:
        raise ValueError(f"{entity_name} cannot define both Key and __identify_by__")

    identity_cols: dict[str, Any] = {}

    if len(key_items) == 1:
        # Single-id entity
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
        identity_cols = {"id": _getattr_any(source, key_field.column)}
    elif len(key_items) == 0 and composite_identify_by:
        # Composite identity entity
        identify_by_concepts: dict[str, Any] = {}
        for attr, value_concept_name in composite_identify_by.items():
            field = fields.get(attr)
            if field is None:
                raise ValueError(f"{entity_name}.__identify_by__ references unknown field: {attr}")
            if field.kind != "prop":
                raise ValueError(f"{entity_name}.{attr}: identity fields must be declared as Prop")
            if not field.column:
                raise ValueError(f"{entity_name}.{attr}: identity Prop missing column")
            if field.value_concept and field.value_concept != value_concept_name:
                raise ValueError(
                    f"{entity_name}.{attr}: value_concept ({field.value_concept}) must match __identify_by__ ({value_concept_name})"
                )

            concept_obj = _ensure_value_concept(
                m_any,
                name=value_concept_name,
                extends=field.value_extends,
                create=field.create_value_concept,
            )
            identify_by_concepts[attr] = concept_obj
            identity_cols[attr] = _getattr_any(source, field.column)

        entity_concept = _ensure_entity_concept_identify_by(m_any, entity=entity_name, identify_by=identify_by_concepts)
    else:
        raise ValueError(
            f"{entity_name} must declare either exactly one Key field or a non-empty __identify_by__; found keys={len(key_items)}"
        )

    # 2) Define properties/relationships on the entity concept
    for attr, field in fields.items():
        if field.kind == "key":
            continue
        if attr in composite_identity_attrs:
            # Composite identity fields are defined implicitly by identify_by.
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
    rai.define(entity_concept.new(**identity_cols))
    row = rai.where(*[(getattr(entity_concept, k) == v) for k, v in identity_cols.items()])

    for attr, field in fields.items():
        if field.kind == "key":
            continue
        if not field.column:
            raise ValueError(f"{entity_name}.{attr}: missing column")

        if field.kind == "prop":
            if attr in identity_cols:
                # Identity fields are bound via `entity_concept.new(...)`.
                continue
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
