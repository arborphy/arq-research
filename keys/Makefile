.PHONY: help validate-json check-sources check-coverage scan-usage

help:
	@echo "Available targets:"
	@echo "  make validate-json   # Validate trait_synonyms.json syntax with jq"
	@echo "  make check-sources   # Verify referenced source IDs exist and list unused sources"
	@echo "  make check-coverage  # Compare synonyms in synonymToSource vs synonymDefinitions"
	@echo "  make scan-usage      # Search .json and .txt files for key terminology"

validate-json:
	@jq -e . trait_synonyms.json >/dev/null \
		&& echo "trait_synonyms.json: JSON OK" \
		|| (echo "trait_synonyms.json: JSON INVALID" >&2; exit 1)

# Compares referenced sources against .sources keys; outputs two sections
check-sources:
	@S=$$(mktemp -t sources); R=$$(mktemp -t refs); \
	jq -r '.sources | keys[]' trait_synonyms.json | sort -u > $$S; \
	jq -r '[ (.synonymToSource | to_entries[] | .value[]), (.synonymDefinitions | .. | objects | .source? // empty) ] | flatten | unique | .[]' trait_synonyms.json | sort -u > $$R; \
	echo "Undefined (referenced but not defined):"; \
	comm -13 $$S $$R || true; \
	echo; echo "Defined but never referenced:"; \
	comm -23 $$S $$R || true; \
	rm -f $$S $$R

# Compares synonym keys present in synonymToSource vs synonymDefinitions
check-coverage:
	@SYN_SRC=$$(mktemp -t syns_src); SYN_DEF=$$(mktemp -t syns_def); \
	jq -r '.synonymToSource | keys[]' trait_synonyms.json | sort -u > $$SYN_SRC; \
	jq -r '.synonymDefinitions | to_entries[] | select(.key != "_metadata") | .value | del(.traitId) | keys[]' trait_synonyms.json | sort -u > $$SYN_DEF; \
	echo "In synonymToSource but missing in synonymDefinitions:"; \
	comm -13 $$SYN_DEF $$SYN_SRC || true; \
	echo; echo "In synonymDefinitions but missing in synonymToSource:"; \
	comm -23 $$SYN_DEF $$SYN_SRC || true; \
	rm -f $$SYN_SRC $$SYN_DEF

# Grep terms across local JSON/TXT files. Uses ripgrep if available, else grep -R
scan-usage:
	@PATTERN='zygomorphic|actinomorphic|alternate|opposite|whorled|basal|rosette|herbaceous|vine|acaulescent|decussate|distichous|capitulum'; \
	if command -v rg >/dev/null 2>&1; then \
		rg -n -i "$$PATTERN" -- *.json *.txt || true; \
	else \
		grep -RniE "$$PATTERN" -- *.json *.txt || true; \
	fi

