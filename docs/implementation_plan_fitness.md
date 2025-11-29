# Implementation Plan: Fitness Function Overhaul

## Goal
Replace the simple, harsh fitness function with a nuanced, reward-based system that encourages specific complex behaviors (middle names, multiple titles, double surnames) while maintaining basic accuracy.

## Fitness Formula
`Fitness = CORE_SCORE + BONUS_SCORE - PENALTY`

### 1. CORE_SCORE (The Foundation)
*   **Weights**:
    *   Family Name: 0.4
    *   Given Name: 0.4
    *   Title: 0.1
    *   Gender: 0.1
*   **Calculation**: Weighted average of F1 scores for these fields.

### 2. BONUS_SCORE (The Incentive)
*   **Exact Match Bonus** (`0.05 * ExactRate`):
    *   +1 if ALL fields (salutation, title, given, middle, family, suffix, particles, gender) match perfectly.
*   **Coverage Bonus** (`0.05 * CoverageScore`):
    *   Reward for correctly identifying optional fields (middle, suffix, particles) when they exist.
*   **Uncertainty Bonus** (`0.02 * UnknownHandlingScore`):
    *   Reward for correctly leaving fields empty/unknown when the truth is empty/unknown (prevents guessing).

### 3. PENALTY (The Stick)
*   **Hallucination Penalty** (`0.1 * HallucinationRate`):
    *   Punishment if a field is predicted as non-empty when the truth is empty.
*   **Bloat Penalty** (`0.0005 * tree_size`):
    *   Slight pressure against large trees.
*   **Hard Constraints**:
    *   If `family` or `given` is empty in prediction but present in truth: `Fitness *= 0.5` (Severe penalty, but not death).

## Implementation Details

### 1. Modify `trainer.py` -> `evaluate_individual`
*   Implement the detailed metric collection (Exact matches, Hallucinations per field, etc.).
*   Apply the formula.

### 2. Update `primitive_set.py`
*   Add `extract_middle_str` primitive (Heuristic: everything between first and last) to aid the "Coverage" goal.
