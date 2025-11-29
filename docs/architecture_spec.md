# Architecture Specification: evoname

## 1. Core Philosophy: Hybrid Evolution & GitOps
The system combines **Genetic Programming (GP)** for logical structure with **Regex Tokens** for pattern recognition. The entire lifecycle from training to release is automated ("Self-Publishing Factory").

## 2. System Components

### A. The Trainer (Python / DEAP)
*   **Role**: The "Brain" that breeds the parsers.
*   **Method**: Genetic Programming (Tree-based) with **Typed DSL**.
*   **Input**:
    *   `Primitive Set`: Typed DSL building blocks (Control Flow, String Ops, Regex Tokens).
    *   `Training Data`: Split into **Train** (Evolution), **Validation** (Selection/Hyperparameter), and **Hidden Test** (Release Decision).
*   **Performance & Caching**:
    *   **Fitness Caching**: Storing results for identical trees/sub-trees.
    *   **Regex Caching**: `TOKENIZE` runs only once per unique string.
*   **Anti-Bloat & Constraints**:
    *   **Parsimony Pressure**: Penalty for excessive tree size (Fitness = F1 - λ * size).
    *   **Hard Constraints (Veto)**: Fitness = 0 if e.g. `lastname` is empty or `title` > 20 chars.
*   **Checkpointing vs. Warmstart**:
    *   **Checkpointing (Resume)**:
        *   *Goal*: Crash Recovery & continuing long runs.
        *   *Content*: Complete State (Population, HallOfFame, Logbook, Random State, Config).
        *   *Storage*: `runs/{date}_{id}/checkpoints/gen_X.pkl`.
    *   **Warmstart (Seeding)**:
        *   *Goal*: Transfer Learning for new data or changed parameters.
        *   *Strategy*: Injecting old champions into a new population (e.g., 10% Seed, 90% Random).
        *   *Prerequisite*: Compatible Primitive Set.

### B. The Transpiler (Python)
*   **Role**: Translates the Abstract Syntax Tree (AST) of the DSL into production JavaScript code.
*   **Mechanism**: Pattern-Matching on DSL Node Types -> JS Snippet.
*   **Risk Mitigation (Regex Compatibility)**:
    *   **Lowest Common Denominator**: Using a Regex subset that works identically in Python (`re`) and JS (`RegExp`).
    *   **Cross-Language Testing**: Unit tests ensure every token matches exactly the same in both languages.
*   **Post-Processing**:
    *   The transpiler automatically adds a "Cleaner" step (Trim, Whitespace-Normalization) to relieve the EA.

### C. The Factory (Git & CI/CD)
*   **Trigger**: Completion of an evolution epoch.
*   **Validation**: Test against the Hidden Test Set.
*   **Reproducibility**:
    *   Fixed Random Seeds for GP and Data Shuffling.
    *   `metrics.json` contains versions of Data, Primitive Set, and Trainer Commit.
*   **Action**:
    *   If `Score > CurrentHighscore`:
        *   Transpile code to `output/index.js`.
        *   Generate `metrics.json` (incl. `data_version`).
        *   Git Commit & Push.
    *   If `Score > ReleaseThreshold` (e.g., 95%):
        *   Create Git Tag.
        *   GitHub Action triggers `npm publish`.

### D. Run Organization
*   **Folder Structure**:
    ```text
    runs/
      2025-11-29_01a2b3c4/       # Unique Run ID
        config.yaml              # Parameters
        primitive_set_version.txt
        data_version.txt
        checkpoints/             # Internal States
          gen_050.pkl
        artifacts/               # Output for Factory
          champion_gen_050.js
          metrics_gen_050.json
    ```

## 3. Scope & Internationalization
*   **Phase 1**: Focus on DACH + US/UK (Western naming conventions).
*   **Phase 2**: Expansion to complex cases (e.g., Spanish double surnames, Asian order).
*   **Unknown Strategy**: Introduction of a `confidence` score or `status: "uncertain"` for ambiguous cases.
*   **Gender Strategy**:
    *   **Phase 1 (Explicit)**: Detection solely via Salutation Tokens ("Herr" -> "m").
    *   **Phase 2 (Implicit)**: Optional add-on module (Lookup/ML) for given-name-based detection (not part of the Core Parser).

## 4. Metrics & Fitness (Detailed)
*   **Fitness Function**: Weighted F1-Score minus Parsimony Pressure.
    *   `Fitness = (0.4 * F1_family + 0.4 * F1_given + 0.1 * F1_titles + 0.1 * F1_gender) - (λ * tree_size)`
*   **Metrics Handling**:
    *   `gender=null` in Ground Truth is ignored for F1_gender (no penalty).
    *   Use of Macro-F1 in case of strong class imbalance.
*   **Overfitting Check**:
    *   Comparison of Train-F1 vs. Validation-F1.
    *   If Delta > Threshold -> Run is discarded (not released).

## 5. Governance & Lifecycle
*   **Primitive Set Versioning**: Changes to the Primitive Set require a new version (e.g., `v2.0`) and invalidate old checkpoints (no Warmstart possible).
*   **Data Governance**:
    *   Datasets are versioned (`data_v1`).
    *   **Error Analysis Loop**: Failed parses -> "Hard Cases" Dataset -> Retraining (Warmstart).
*   **Implementation Note**:
    *   `regex_definitions.json` as Single Source of Truth for Python and JS.
    *   **Priority**: Salutation Tokens must be matched before Title Tokens (e.g., "Mr." before "Dr.") to correctly separate "Mr. Dr.".
    *   **Locale Awareness**: `regex_definitions.json` can contain language-specific patterns (e.g., "de", "en"). The Tokenizer loads the appropriate profile based on `locale_hint` (Fallback to Default). The DSL and GP Tree remain unaffected.

## 6. Product / API Design (JavaScript)
*   **API Options**:
    ```typescript
    parseName(input: string, options?: {
      locale?: string;
      predictGender?: boolean;       // default: true
      genderMode?: "basic" | "full"; // "basic" (m/f/d/null), "full" (+ candidates)
    }): NameObj
    ```
*   **SemVer Strategy**:
    *   **Patch**: Better weights/logic, same schema.
    *   **Minor**: New fields in `NameObj` (backward compatible).
    *   **Major**: Breaking Changes in API or Output Structure.
*   **Runtime Constraints**:
    *   Goal: < 10ms per name in the browser.
    *   Limiting tree depth also serves performance assurance.

## 7. Data Flow
1.  **Raw Strings** -> **GP Engine** (Population of DSL Trees)
2.  **Tree Execution** -> **Fitness Score** (Weighted F1 - SizePenalty)
3.  **Best Tree** -> **Transpiler** -> **JavaScript Code**
4.  **JavaScript Code** -> **NPM Registry**

## 8. Technology Stack
*   **Evolution**: Python 3.10+, DEAP library.
*   **Testing**: Pytest (Python side), Jest (JS side validation).
*   **Target**: Node.js / Browser (Universal JS).
*   **VCS**: Git.
