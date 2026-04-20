"""Translation layer between Newcomb group numbers and their key properties.

The Newcomb key encodes a 3-level decision path in the group number:

    Digit 1 → Flower Type   (e.g. "5" → "5 Regular Parts")
    Digit 2 → Plant Type    (e.g. "3" → "Wildflowers - Alternate Leaves")
    Digit 3 → Leaf Type     (e.g. "2" → "Leaves Entire")

A "0" in any position means the level is not applicable (wildcard).

    "532" → FlowerType=5, PlantType=3, LeafType=2  (fully resolved)
    "400" → FlowerType=4, PlantType=any, LeafType=any  (partial key)
    "000" → no level resolved  (Asters, Goldenrods — special cases)

Range groups like "733-734" have ambiguous leaf type; the first value is used.

Usage:
    import kg.model.core.keys.newcomb_translation  # load rules into model

    # Set flower/plant/leaf codes at load time:
    nk.flower_code("5"), nk.plant_code("3"), nk.leaf_code("2")

    # Then flower_type, plant_type, leaf_type are derived automatically.
"""

from relationalai.semantics import Integer, String, define, where

from kg.model import m
from kg.model.core.keys.newcomb import NewcombKey

# ── Digit code map ─────────────────────────────────────────────────────────────
# Concept identifying each (level, digit) pair with a human-readable label.
# Level 1 = Flower Type, Level 2 = Plant Type, Level 3 = Leaf Type.

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

# ── Digit code properties ──────────────────────────────────────────────────────
# Stored at load time (Python-side extraction from group_number).
# "0" means the level is not applicable for this key entry.

NewcombKey.flower_code = m.Property(f"{NewcombKey} has flower code {String:flower_code}")
NewcombKey.plant_code  = m.Property(f"{NewcombKey} has plant code {String:plant_code}")
NewcombKey.leaf_code   = m.Property(f"{NewcombKey} has leaf code {String:leaf_code}")

# ── Derived rules: code → label ────────────────────────────────────────────────
# Only fires when the code is non-zero (i.e. level is resolved).

where(
    nk := NewcombKey.ref(),
    nk.flower_code != "0",
    dm := NewcombDigitMap.filter_by(level=1, code=nk.flower_code),
).define(nk.flower_type(dm.label))

where(
    nk := NewcombKey.ref(),
    nk.plant_code != "0",
    dm := NewcombDigitMap.filter_by(level=2, code=nk.plant_code),
).define(nk.plant_type(dm.label))

where(
    nk := NewcombKey.ref(),
    nk.leaf_code != "0",
    dm := NewcombDigitMap.filter_by(level=3, code=nk.leaf_code),
).define(nk.leaf_type(dm.label))


# ── Helper: parse group number (Python-side, used in loaders) ─────────────────

def parse_group_number(group_number: str) -> tuple[str, str, str]:
    """Extract (flower_code, plant_code, leaf_code) from a Newcomb group number.

    Handles:
        "532"     → ("5", "3", "2")
        "400"     → ("4", "0", "0")  partial key: plant/leaf unresolved
        "733-734" → ("7", "3", "3")  range: take lower bound
        "000"     → ("0", "0", "0")  Asters/Goldenrods: no levels apply

    Args:
        group_number: raw group number string from Newcomb data.

    Returns:
        Three single-character strings, one per key level.
    """
    base = group_number.split("-")[0].strip()  # "733-734" → "733"
    base = base.zfill(3)                        # safety: ensure 3 chars
    return base[0], base[1], base[2]
