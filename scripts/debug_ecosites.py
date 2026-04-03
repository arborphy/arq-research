"""Debug script: query ecosites directly."""
import kg.loaders.ecosites  # noqa: F401
from relationalai.semantics import where, select
from kg.model.core.h3cell import EcoSite, H3Cell

print("=== Attempt 1: select(EcoSite.ecosite_id) ===")
try:
    df = select(EcoSite.ecosite_id).to_df()
    print(df.head())
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
    print(f"  attrs: {vars(e)}")

print("\n=== Attempt 2: where(ecosite.h3_cells(cell)).select(ecosite.ecosite_id) ===")
try:
    ecosite = EcoSite.ref()
    cell = H3Cell.ref()
    df = where(ecosite.h3_cells(cell)).select(ecosite.ecosite_id).to_df()
    print(df.head())
except Exception as e:
    print(f"FAILED: {e}")

print("\n=== Attempt 3: where(ecosite.ecosite_id).select(ecosite.ecosite_id) ===")
try:
    ecosite = EcoSite.ref()
    df = where(ecosite.ecosite_id).select(ecosite.ecosite_id).to_df()
    print(df.head())
except Exception as e:
    print(f"FAILED: {e}")
