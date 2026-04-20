from relationalai.semantics import Integer, String

from kg.model import m
from .key import IdentificationKey

GoBotanyKey = m.Concept("GoBotanyKey", extends=[IdentificationKey])

# Identifying properties: one key per (pile, character, value_index)
GoBotanyKey.pile_slug = m.Property(f"{GoBotanyKey} from pile {String:pile_slug}")
GoBotanyKey.character_short_name = m.Property(f"{GoBotanyKey} has character {String:character_short_name}")
GoBotanyKey.value_index = m.Property(f"{GoBotanyKey} has value index {Integer:value_index}")
