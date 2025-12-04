## Step 3 - Summer Solstice Observations by Location

**Goal**: Analyze plant observations near the summer solstice to understand peak growing season biodiversity patterns across regions

This kata will help you work with astronomical calendar events (Summer Solstice), hemisphere-aware relationships, and date calculations to analyze phenological patterns

---
**Instructions**:
- Read the query spec below and view the provided query in `kata/step_3/__main__.py`
- Implement the provided query:
    - Find observations occurring within 20 days of the Summer Solstice
    - Match observations to the appropriate hemisphere's summer solstice
    - Count species per family, country, and state/province observed during this period
    - Use the Summer Solstice concept from the solstice/equinox model
    - Use `.alias()` to name columns: species_count, family_name, country_code, state_province
    - The Summer Solstice relationships are defined in `kg/model/core/soleq.py`
- Verify: `uv run -m kata.step_3`
    - Note: you may need to approve Snowflake MFA

---
**Spec**:

Business Question: Which plant families have the most species observed around the summer solstice, and how does this vary by location? This helps understand peak growing season biodiversity and regional phenology patterns during the longest day of the year in each hemisphere.

Acceptance Criteria:
```
Given I am a phenology researcher studying peak growing season patterns,
When I want to see which families have the most species observed near summer solstice by location,
Then I can run a query that counts distinct species per family per region
    within 20 days of the Summer Solstice in the observation's hemisphere
```

---
**Extra Credit**:

The current implementation has a limitation when dealing with Southern Hemisphere observations around the December solstice. Since the summer solstice in the Southern Hemisphere occurs in December (typically around day 355-356), observations within 20 days could span into the following year. However, the query uses `dayofyear` which resets to 1 on January 1st, causing incorrect distance calculations for observations that cross the year boundary.

For example:
- Southern summer solstice: December 21 (day 355)
- Observation on January 5 (day 5 of the next year)
- Current calculation: `ABS(355 - 5) = 350` days (incorrect!)
- Correct calculation: `355 to 365 (10 days) + 1 to 5 (5 days) = 15` days ✓

**Challenge**: Enhance the query and/or model to correctly handle year-boundary crossings for Southern Hemisphere observations.
```
