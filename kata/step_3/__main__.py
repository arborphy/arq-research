import pandas as pd
from rich.console import Console
import relationalai.semantics as rai
import relationalai.semantics.std as std
from kg.model import ARQModel, define_arq

"""
Step 3: Summer Solstice Observations by Location
- Find observations within 20 days of Summer Solstice
- Count distinct species per family, country, and state/province
- Show regional patterns in peak growing season phenology
- Name the columns "species_count", "family_name", "country_code", "state_province"
"""
def early_bloomers_query(arq: ARQModel) -> rai.Fragment:
    dayofyear = std.datetime.datetime.dayofyear
    delta_days = std.math.abs(dayofyear(arq.Solstice.datetime) - dayofyear(arq.Observation.event_datetime))

    return rai.where(
        arq.Observation.classification(arq.Species),
        arq.Species.family(arq.Family),
        arq.Solstice.summer(arq.Observation.hemisphere),
        delta_days < 20,
        species_count := rai.count(arq.Species).per(
            arq.Family,
            arq.Observation.country_code,
            arq.Observation.state_province,
        ),
    ).select(
        species_count.alias("species_count"),
        arq.Family.canonical_name.alias("family_name"),
        arq.Observation.country_code.alias("country_code"),
        arq.Observation.state_province.alias("state_province"),
    )


def test_solution(result: pd.DataFrame) -> None:
    expected = pd.read_csv("kata/step_3/expected_results.csv")
    result["species_count"] = result["species_count"].astype("int64")
    pd.testing.assert_frame_equal(result, expected)
    console.print("✅ Query result is correct!")
    console.print("[dim]Congratulations! You've completed Step 3![/dim]\n")


if __name__ == "__main__":
    console = Console()
    console.print("\n[bold blue]Testing Kata Step 3...")
    arq = define_arq(rai.Model(f"kata_step_3"))
    result = early_bloomers_query(arq).to_df()
    console.print("Step [white]3[/white] - Early Bloomers by Location Result", style="bold")
    console.print("-" * 50 + "\n" + str(result) + "\n")
    test_solution(result)
