# Implementation Plan: CI/CD Pipeline

## Goal
Automate the entire lifecycle of the `evoname` parser using GitHub Actions. The pipeline should run on every push to the `master` branch.

## Workflow Steps (`.github/workflows/pipeline.yml`)

1.  **Setup**:
    *   Checkout code.
    *   Set up Python 3.10.
    *   Set up Node.js 20.
    *   Install Python dependencies (`deap`, `pytest`).

2.  **Data Generation**:
    *   Run `python generate_data.py` to create fresh training/validation data.

3.  **Training**:
    *   Run `python trainer.py --generations 50 --pop-size 300`.
    *   *Note*: In a real scenario, this might run longer. For CI, we keep it moderate to ensure it finishes in a reasonable time.

4.  **Transpilation**:
    *   Identify the latest run directory.
    *   Run `python transpiler.py` to convert the champion to `dist/evoname.js`.

5.  **Verification**:
    *   Run `node test_transpiled.js` to verify the generated JS code works.
    *   (Optional) Run Python unit tests `pytest tests/`.

6.  **Artifacts**:
    *   Upload `dist/evoname.js` and `runs/` as workflow artifacts so the user can download the result of the CI run.

## File Structure
*   `.github/workflows/pipeline.yml`: The workflow definition.

## Future Improvements (Not in Scope)
*   Automatic NPM publishing.
*   Comparison with previous best model (Gatekeeping).
