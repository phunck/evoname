# Implementation Plan: Transpiler

## Goal
Create a tool (`transpiler.py`) that converts the evolved Python GP tree (the "Champion") into a standalone JavaScript file. This allows the parser to be used in web applications or Node.js backends.

## Input
*   **Source**: `runs/{run_id}/artifacts/champion.pkl` (The pickled DEAP individual).
*   **Context**: Needs `primitive_set.py` loaded to unpickle correctly.

## Output
*   **Target**: `dist/evoname.js`.
*   **Format**: A CommonJS module that requires `./library.js` and exports the parser function.

## Mechanism

1.  **Loading**: Load the champion using `pickle` and `deap`.
2.  **Traversal**: Recursively walk the GP tree.
3.  **Code Generation**:
    *   **Primitives**: Map Python function names to `lib.functionName`.
        *   Example: `extract_given_str(...)` -> `lib.extract_given_str(...)`
    *   **Terminals**:
        *   Strings: Quote them (`"foo"`).
        *   Numbers: Keep as is (`0.5`).
        *   Booleans: `true`/`false`.
        *   Enums: Map `Gender.MALE` -> `lib.Gender.MALE`.
        *   Empty Constants: `lib.EMPTY_STR`, etc.
4.  **Templating**: Wrap the generated expression in a JS function shell.

## Mapping Table (Examples)

| Python | JavaScript |
| :--- | :--- |
| `tokenize(x)` | `lib.tokenize(x)` |
| `if_bool_string(c, a, b)` | `lib.if_bool_string(c, a, b)` |
| `Gender.MALE` | `lib.Gender.MALE` |
| `RegexToken.SALUTATION` | `lib.RegexToken.SALUTATION` |

## CLI Interface
```bash
python transpiler.py --input runs/latest/artifacts/champion.pkl --output dist/evoname.js
```

## Verification
*   Generate `dist/evoname.js`.
*   Run a test script `test_transpiled.js` that requires the generated parser and runs it against test cases.
