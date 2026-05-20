"""Translation layer for Newcomb group numbers.

The Newcomb key encodes a 3-level decision path in the group number:

    Digit 1 → Flower Type   (e.g. "5" → "5 Regular Parts")
    Digit 2 → Plant Type    (e.g. "3" → "Wildflowers - Alternate Leaves")
    Digit 3 → Leaf Type     (e.g. "2" → "Leaves Entire")

A "0" in any position means the level is not applicable (wildcard).

Usage:
    from kg.model.core.keys.newcomb_translation import parse_group_number, NewcombDigitMap
"""
from relationalai.semantics import Integer, String, define

from kg.model import m

NewcombDigitMap = m.Concept("NewcombDigitMap", identify_by={"level": Integer, "code": String})
NewcombDigitMap.label = m.Property(f"{NewcombDigitMap} maps to {String:label}")

_CODES: dict[int, dict[str, str]] = {
    1: {  # Flower Type — first digit
        "1": "Irregular Flowers",
        "3": "3 Regular Parts",
        "4": "4 Regular Parts",
        "5": "5 Regular Parts",
        "6": "6 Regular Parts",
        "7": "7 or More Regular Parts",
        "8": "Parts Indistinguishable",
    },
    2: {  # Plant Type — second digit
        "1": "Wildflowers - No Apparent Leaves",
        "2": "Wildflowers - Basal Leaves Only",
        "3": "Wildflowers - Alternate Leaves",
        "4": "Wildflowers - Opposite or Whorled Leaves",
        "5": "Shrubs",
        "6": "Vines",
    },
    3: {  # Leaf Type — third digit
        "1": "No Apparent Leaves",
        "2": "Leaves Entire",
        "3": "Leaves Toothed or Lobed",
        "4": "Leaves Divided",
    },
}

for _level, _codes in _CODES.items():
    for _code, _label in _codes.items():
        define(dm := NewcombDigitMap.new(level=_level, code=_code), dm.label(_label))


def parse_group_number(group_number: str) -> tuple[str, str, str]:
    """Extract (flower_code, plant_code, leaf_code) from a Newcomb group number.

    Handles:
        "532"     → ("5", "3", "2")
        "400"     → ("4", "0", "0")  partial key: plant/leaf unresolved
        "733-734" → ("7", "3", "3")  range: take lower bound
        "000"     → ("0", "0", "0")  Asters/Goldenrods: no levels apply
    """
    base = group_number.split("-")[0].strip()
    base = base.zfill(3)
    return base[0], base[1], base[2]
