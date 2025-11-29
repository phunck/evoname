# Implementation Plan: primitive_set.py

## Goal
Implement the `primitive_set.py` module, which defines the DEAP Primitive Set, the Typed DSL, and the Regex Loader.

## Key Changes (Adaptation to User's Regex Definitions)
The user has updated `regex_definitions.json` with a nested structure:
```json
"TOKEN_TYPE": {
    "locale": {
        "pattern": "...",
        "flags": "i",
        "description": "..."
    }
}
```
The `RegexLoader` must be adapted to parse this structure.

## Components

### 1. Regex Loader (`load_regex_definitions`)
*   **Input**: `locale` (str, default="de").
*   **Logic**:
    *   Load `regex_definitions.json`.
    *   Iterate over all `TOKEN_TYPE` keys.
    *   Try to fetch the entry for the given `locale`.
    *   If missing, fallback to "en" (or raise error? Fallback seems safer for now, or maybe "de" is the fallback since it's a German project primarily). Let's use "en" as a generic fallback if "de" is missing, or just fail if the requested locale isn't there. Given the file has "de", "en", "fr" for all, we can strict load.
    *   Extract `pattern` and `flags`.
    *   Convert `flags` string (e.g., "i") to Python `re` flags (`re.IGNORECASE`).
    *   Compile `re.compile(pattern, flags)`.
    *   Return a dictionary `Dict[str, Pattern]`.

### 2. Types (DEAP)
*   Define classes for `Token`, `TokenList`, `NameObj`, `Gender` (Enum).
*   `Token` class should hold: `value` (str), `type` (str/enum), `span` (tuple).

### 3. Primitives
*   Implement all functions from `docs/primitive_set.md`.
*   **Crucial**: `TOKENIZE(s: str)` must use the loaded regex patterns.
    *   *Strategy*: Combined Regex? Or iterative matching?
    *   *Iterative*: Loop through all Token Types, find match at current position. Priority matters!
    *   *Priority*: As defined in Architecture Spec: Salutation > Title > ...
    *   *Implementation*: Create a master regex or try them in order.
*   `GET_GENDER_FROM_SALUTATION`: Needs a mapping.
    *   *Source*: The user's JSON has "category": "salutation" but no explicit gender mapping in the JSON (only "Herr" in examples).
    *   *Solution*: Hardcode a small dictionary in `primitive_set.py` for Phase 1, as agreed. `{"Herr": "m", "Frau": "f", "Mr.": "m", ...}`.

### 4. DEAP Registration
*   `gp.PrimitiveSetTyped("MAIN", [str], NameObj)`
*   Register all functions and terminals.

## Verification
*   Create a simple test script `tests/test_primitives.py`.
*   Test `TOKENIZE` with different locales.
*   Test `MAKE_NAME_OBJ`.
