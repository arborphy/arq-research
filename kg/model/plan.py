from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table

from kg.model.compiler import EntitySpec, compile_entity


SourceFn = Callable[[str], Table]


@dataclass(frozen=True)
class Step:
    name: str

    def apply(self, m: rai.Model, source: SourceFn) -> None:  # pragma: no cover
        raise NotImplementedError


@dataclass(frozen=True)
class NoSourceStep(Step):
    fn: Callable[[rai.Model], None]

    def apply(self, m: rai.Model, source: SourceFn) -> None:
        self.fn(m)


@dataclass(frozen=True)
class TableStep(Step):
    fn: Callable[[rai.Model, Table], None]
    table: str

    def apply(self, m: rai.Model, source: SourceFn) -> None:
        self.fn(m, source(self.table))


@dataclass(frozen=True)
class EntitySpecStep(Step):
    spec: type[EntitySpec]
    table: str

    def apply(self, m: rai.Model, source: SourceFn) -> None:
        compile_entity(m=m, source=source(self.table), spec=self.spec)


@dataclass(frozen=True)
class ModelPlan:
    steps: Sequence[Step]

    def apply(self, m: rai.Model, *, db: str, schema: str) -> None:
        src = lambda t: Table(f"{db}.{schema}.{t}")
        for step in self.steps:
            step.apply(m, src)
