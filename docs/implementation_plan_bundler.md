# Implementation Plan: Self-Contained NPM Package

## Goal
Create a single, zero-dependency JavaScript file (`dist/index.js`) that contains the entire parser logic, including the library functions and regex definitions. This file should be usable in Node.js and Browsers without any external file loading.

## Strategy
We will upgrade `transpiler.py` to act as a **Bundler**.

### 1. Modify `library.js`
*   Refactor `loadRegexDefinitions` to accept an optional `definitions` argument or check for a global `INJECTED_REGEX_DEFINITIONS`.
*   Ensure `fs` and `path` imports are only used if we are NOT in the bundled environment (or strip them during bundling).
*   Goal: `library.js` code should run in the browser without `require('fs')`.

### 2. Update `transpiler.py`
Add a bundling mode that performs the following steps:
1.  **Load Regex Definitions**: Read `regex_definitions.json` in Python.
2.  **Load Library Source**: Read `library.js`.
3.  **Sanitize Library**:
    *   Remove `require('fs')`, `require('path')`.
    *   Remove `module.exports`.
4.  **Generate Champion Code**: Transpile the GP tree (as before).
5.  **Assemble Bundle**:
    ```javascript
    // Header
    const REGEX_DEFINITIONS = { ... }; // Injected JSON

    // Library Code (Sanitized)
    // ... functions ...
    // Patch loadRegexDefinitions to use REGEX_DEFINITIONS

    // Champion Logic
    function champion(raw_input) { ... }

    // Public API
    function parseName(input) {
       // ... logic to call tokenize -> champion -> makeNameObj
    }

    // Exports
    module.exports = { parseName };
    ```

### 3. Verification
*   Create `test_bundle.js` that requires the single file and runs tests.
*   Update `demo.html` to use the single file.

## Deliverables
*   Updated `library.js`
*   Updated `transpiler.py`
*   `dist/index.js` (The final product)
