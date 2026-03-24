from kg.model import m
from relationalai.semantics import String
from .key import IdentificationKey

NewcombKey = m.Concept("NewcombKey", extends=[IdentificationKey])

# Newcomb-specific properties
NewcombKey.flower_type = m.Property(f"{NewcombKey} has flower type {String:flower_type}")
NewcombKey.plant_type = m.Property(f"{NewcombKey} has plant type {String:plant_type}")
NewcombKey.leaf_type = m.Property(f"{NewcombKey} has leaf type {String:leaf_type}")
NewcombKey.group_number = m.Property(f"{NewcombKey} has group number {String:group_number}")
