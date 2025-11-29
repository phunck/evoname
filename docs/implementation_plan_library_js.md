# Implementation Plan: library.js

## Goal
Implement the JavaScript runtime environment (`library.js`) that mirrors `primitive_set.py`. This allows the Python-evolved logic trees to be transpiled and executed in a browser or Node.js environment.

## Core Requirement: Parity
Every function in `primitive_set.py` must have an exact equivalent in `library.js` with the same name, arguments, and behavior.

## Components

### 1. Types & Data Structures
*   **`NameObj`**: JS Object or Class.
    *   Fields: `raw`, `given`, `family`, `middle` (Array), `title` (Array), `salutation`, `gender`, `suffix` (Array), `particles` (Array), `confidence`.
*   **`Token`**: JS Object.
    *   Fields: `value`, `type`, `span` (Array [start, end]), `index`.
*   **`RegexToken`**: JS Object (Enum-like) mapping names to integers or strings.
*   **`Gender`**: JS Object (Enum-like).

### 2. Regex Loader
*   Load `regex_definitions.json`.
*   **Challenge**: Python `re` vs JS `RegExp`.
    *   Most simple patterns are compatible.
    *   Named groups (`?P<name>`) might need adjustment if used (we mostly use standard groups).
    *   Flags: Python `(?i)` -> JS `/.../i`.
*   **Implementation**: A function `loadRegexes(locale)` that compiles the patterns.

### 3. Primitives (Porting from Python)

#### Control Flow
*   `if_bool_string(cond, a, b)`
*   `if_bool_tokenlist(cond, a, b)`

#### String & List Ops
*   `trim(s)`
*   `to_lower(s)`
*   `split_on_comma(s)`
*   `get_first_string(list)`
*   `get_last_string(list)`
*   `get_first_token(list)`
*   `get_last_token(list)`
*   `slice_tokens(list, start, end)`
*   `len_tokens(list)`
*   `drop_first(list)`
*   `drop_last(list)`
*   `remove_type(list, type)`
*   `index_of_type(list, type)`
*   `get_remainder_tokens(original, used)`

#### Token Muscles
*   `tokenize(s, locale)`: The complex logic. Needs to implement the same priority loop as Python.
*   `filter_by_type(list, type)`
*   `count_type(list, type)`
*   `get_gender_from_salutation(token)`

#### Feature Detectors
*   `has_comma(s)`
*   `is_title(token)`
*   `is_salutation(token)`
*   `identity_token_type(t)`

#### Macro-Primitives (Boosters)
*   `extract_salutation_str(list)`
*   `extract_title_list(list)`
*   `extract_given_str(list)`
*   `extract_family_str(list)`

#### Object Builder
*   `make_name_obj(...)`
*   `set_confidence(obj, val)`

### 4. Constants & Terminals
*   `EMPTY_STR`, `EMPTY_STR_LIST`, `EMPTY_TOK_LIST`, `EMPTY_NAME_OBJ`, `EMPTY_TOKEN`.
*   `TRUE`, `FALSE`.

## Testing Strategy
*   Create a simple Node.js script `test_library.js`.
*   Manually verify a few critical functions (`tokenize`, `make_name_obj`).
*   (Later) Automated cross-language testing.

## File Structure
*   `library.js`: The main library file (CommonJS or ES Module). Let's use CommonJS for easy Node testing, or a hybrid.

