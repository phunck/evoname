# evoname

**Evolutionary Name Parser**

`evoname` is an experimental project to build a robust name parser (splitting strings like "Dr. Hans Müller" into structured JSON) using **Genetic Programming (GP)** and **Regular Expressions**.

Instead of manually writing thousands of rules, we "breed" the parser logic using an evolutionary algorithm (DEAP).

## 🏗 Architecture

*   **Hybrid Approach**: GP handles the control flow (logic tree), while Regex handles the pattern matching (tokens).
*   **Strictly Typed DSL**: Prevents invalid trees and ensures robustness.
*   **Island Model**: We evolve three separate populations ("Islands") in parallel to maintain diversity and specialize in different aspects of the problem.
*   **Active Learning**: An automated loop (`active_trainer.py`) continuously regenerates data to target the model's weaknesses.

## 🏝️ The Island Model

To prevent premature convergence and encourage specialization, `evoname` uses a multi-island approach:

1.  **Main Island**: The generalist population. Optimized for overall F1 score.
2.  **Detail Island**: Specialized in extracting "hard" fields like suffixes, particles, and middle names.
3.  **Structure Island**: Specialized in understanding the overall structure (e.g., correct splitting of Given vs. Family name).

Islands exchange genetic material (migration) every few generations, allowing the Main Island to integrate specialized traits.

## 🛡️ Robustness & Anti-Overfitting

We employ several strategies to ensure the model generalizes well:

*   **Curriculum Learning**: The difficulty of the fitness function increases over time ("Bootstrap" -> "Ramp" -> "Strict").
*   **Adaptive Weighting**: The system automatically adjusts the importance of different components (e.g., Title vs. Suffix) based on their performance in the previous cycle, focusing the model on its current weaknesses.
*   **Fresh Blood Injection**: If phenotypic diversity drops below 20% (stagnation), the satellite islands are automatically reset to inject random genetic material, while the main champion is preserved.
*   **Hall of Shame**: We track the "hardest" examples (those the best model consistently fails on) and use **Targeted Data Generation** to oversample them in the next training batch.
*   **Validation Set**: A separate dataset is used to validate the champion model, ensuring it hasn't just memorized the training data.

## 🧩 Primitives & Features

The parser has access to a rich set of primitives:

*   **Basic**: `tokenize`, `split_on_comma`, `trim`, `to_lower`.
*   **Contextual**: `get_tokens_before_comma`, `get_tokens_after_comma`.
*   **Statistical**: `token_length`, `is_short`, `is_all_caps`.
*   **Shape & N-Grams**: `get_token_shape` ("Xx."), `ends_with_ngram` ("-ski"), `is_shape`.
*   **Feature Detectors**: `is_initial`, `has_hyphen`, `has_period`, `is_roman_numeral`, `is_conjunction`.
*   **Lexicon**: `is_common_given_name`, `is_common_family_name`.
*   **Advanced**: `merge_particles`, `extract_degree_list`.
*   **Post-Processing**: A deterministic repair layer fixes obvious errors (e.g., "2 words, no title -> Given Family") before evaluation.

## 📂 Project Structure

*   `docs/`: Detailed documentation (Architecture, Data Schema, Concept).
*   `primitive_set.py`: The core DSL and Regex definitions.
*   `regex_definitions.json`: Single Source of Truth for Regex patterns (Locale-aware).
*   `data/`: Training and validation datasets.
*   `tests/`: Unit tests.

## 🚀 Getting Started

### Prerequisites
*   Python 3.10+
*   Node.js (for the JS transpiler target)

### Installation
```bash
# Clone the repository
git clone https://github.com/phunck/evoname.git
cd evoname

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install deap pytest rich
```

### Running Tests
```bash
python -m pytest tests/

# JavaScript Tests
node test_library.js
node tests/test_primitives_stats.js
node tests/test_primitives_advanced.js
```

### Training & Building

1.  **Generate Data** (Optional, creates fresh synthetic names):
    ```bash
    python generate_data.py
    ```

2.  **Train Model**:
    ```bash
    python trainer.py --generations 300 --pop-size 1000 --jobs 8
    ```
    The best model is saved to `runs/LATEST/artifacts/champion.pkl`.

3.  **Active Learning Loop (Recommended)**:
    To prevent stagnation, use the active trainer. It automatically regenerates data based on the model's weaknesses ("Hall of Shame") and retrains in cycles.
    ```bash
    python active_trainer.py --cycles 10 --gens-per-cycle 30 --jobs 8
    ```
    **Arguments:**
    *   `--cycles`: Number of generate-train loops (default: 10).
    *   `--gens-per-cycle`: Generations per loop (default: 30).
    *   `--pop-size`: Population size (default: 300).
    *   `--jobs`: Parallel jobs (default: 8).
    *   `--swap`: Migration interval in generations (default: 5). Also triggers LLM mutation.

4.  **Save Champion (Best Practice)**:
    To share your best model or use it on other machines, copy it to the `model/` directory and commit it:
    ```bash
    cp runs/LATEST/artifacts/champion.pkl model/champion.pkl
    git add model/champion.pkl
    git commit -m "Update champion model"
    ```

### 🛠️ Analysis Tools

To inspect the performance of your champion model in detail (including F1 scores per field and color-coded diffs):

```bash
python analyze_champion.py --model model/champion.pkl --data data/train.json
```

This will output a report grouping examples by performance (Perfect, Good, Okay, Bad) and showing exactly where the model failed (e.g., `Given: Hans / Hans-Peter`).

5.  **Transpile to JavaScript**:
    ```bash
    python transpiler.py --input model/champion.pkl --output dist/evoname.js
    ```

### JavaScript Runtime (Self-Contained)
The generated `dist/evoname.js` is a **zero-dependency** file. It contains the parser logic, the runtime library, and all regex definitions.

**Node.js:**
```javascript
const { parseName } = require('./dist/evoname');
console.log(parseName("Dr. Hans Müller"));
```

**Browser:**
```html
<script src="dist/evoname.js"></script>
<script>
    console.log(EvoName.parseName("Dr. Hans Müller"));
</script>
```

Verify the build locally:
```bash
node test_bundle.js
```

## 📅 Roadmap
- [x] Concept & Specs
- [x] Primitive Set & Regex Loader
- [x] Data Generation (Synthetic)
- [x] Trainer Implementation
- [x] JavaScript Runtime (`library.js`)
- [x] Transpiler (Python -> JS)
- [x] Advanced Primitives (Contextual, Positional, Lexicon)
- [x] Post-Processing Layer (Deterministic Repair)
- [x] Targeted Data Generation (Hall of Shame)
- [x] Statistical & Feature Primitives
- [x] **Experiment**: LLM-assisted Mutation (Ollama/Qwen)

## 🧪 Experimental: LLM-assisted Mutation (PAUSED)
We have integrated a local LLM (via Ollama) to intelligently repair/mutate individuals. **Note: This feature is currently PAUSED until further notice.**

**How it works:**
*   **Trigger:** Dynamic chance (0-5%) ONLY during migration generations (to save time).
*   **Process:** The system sends the broken code + a failure case to `qwen2.5-coder`.
*   **Result:** The LLM returns a repaired DEAP expression, which replaces the old one.

**The "LLM Surgeon" Workflow:**
1.  **Diagnose (Hall of Shame):** The system identifies a specific name that many individuals fail to parse (e.g., "Mr Dr. med. James Fischer").
2.  **The Patient:** A random individual (code tree) is selected. It might be too simple, e.g., `make_name_obj(split(raw), ...)`.
3.  **The Oracle (Hinting):** The system asks a rule-based `OracleParser` for the "perfect" solution (Optional/Comparison only).
4.  **The Consultation:** The system prompts the local LLM: *"You are an expert. Here is code that fails on 'Mr Dr. med. James Fischer'. The Oracle says the result should be {...}. Rewrite the code using these primitives."*
5.  **The Operation:** The LLM rewrites the code, potentially adding logic like `extract_title_list` or `get_tokens_before_comma`.
5.  **Transplantation:**
    *   **Success:** If the new code is valid and compiles to a `NameObj`, it replaces the old individual.
    *   **Rejection:** If the LLM produces invalid code or text, the operation is aborted, and the original individual remains unchanged.

**Setup:**
1. Install [Ollama](https://ollama.com/).
2. Pull the model: `ollama run qwen2.5-coder:1.5b`.
3. Run training: `python active_trainer.py`. (If Ollama is offline, it gracefully falls back to standard mutation).

## 👥 Credits
Created by **Paul Hunck**.

## 📄 License
MIT
