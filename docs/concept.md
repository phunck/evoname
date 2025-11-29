# Brainstorm Concept: Evolutionary Name Parser

## 1. Introduction and Objective
The goal is to develop a system that decomposes unstructured name strings (e.g., "Dr. med. Hans Müller-Lüdenscheidt", "John Doe", "Doe, John") into structured components (Title, Given Name, Family Name, Suffix, etc.). Instead of manually coding rules, an **Evolutionary Algorithm (EA)** or **Genetic Programming (GP)** will be used to "breed" optimal parsing rules or regex patterns.

## 2. The Evolutionary Idea in Context
What makes this project "evolutionary"?
*   **Population**: A set of potential solutions (parsers). Initially, these can be randomly generated.
*   **Genotype**: The internal representation of a parser.
    *   *Option A (Regex Evolution)*: A chain of Regex building blocks.
    *   *Option B (Genetic Programming)*: A syntax tree of operations (Split, Match, Assign).
*   **Phenotype**: The executable code that takes a string and returns a JSON object.
*   **Fitness Function**: The core. How well does an individual parse a list of known names?
    *   Comparison of output with "Ground Truth" (correct decomposition).
    *   High Fitness = High Agreement.
*   **Selection, Crossover & Mutation**: The best parsers "mate" (exchange rules/regex parts) and mutate (random changes) to hopefully produce better offspring.

## 3. Challenges and Considerations
*   **Data Quality**: "Garbage in, Garbage out". We need a high-quality, labeled dataset (Ground Truth).
*   **Cultural Variance**: "Juan Carlos Garcia", "Dr. Wang Wei", "O'Connor". The parser must be flexible.
*   **Overfitting**: A parser could memorize the training data but fail on new names. -> Use Validation Set.
*   **Performance**: Evolution takes time. Fitness evaluation must be fast.

## 4. Benchmark & Testing
How do we measure success?
*   **Metrics**:
    *   **Precision**: How many of the parts identified as "Given Name" are really given names?
    *   **Recall**: How many of the real given names were found?
    *   **F1-Score**: Harmonic mean of Precision and Recall.
    *   **Levenshtein Distance**: For almost correct matches (e.g., tolerate typos?).
*   **Automation**:
    *   Each generation is automatically checked against the Test Set.
    *   CI/CD pipeline that starts an evolution run on every commit or nightly.

## 5. Proposed Tech Stack
*   **Language**: **Python** (Excellent for ML/AI and text processing).
*   **Frameworks**:
    *   **DEAP** (Distributed Evolutionary Algorithms in Python) for GA logic.
    *   **PyTest** for Unit Tests.
*   **Database**:
    *   **SQLite** (sufficient for start) or **PostgreSQL** (JSONB Support).
    *   Storage of: Training Data (Raw Name -> Parsed JSON), Generation History, Best Individuals.
*   **Visualization**: Matplotlib/Streamlit to see fitness progress over generations.

## 6. Architecture Sketch
1.  **Data Ingest**: Import of name lists (CSV/DB).
2.  **Trainer (Evolution Engine)**:
    *   Initializes Population.
    *   Loop: Evaluate -> Select -> Mate -> Mutate.
    *   Saves Checkpoints.
3.  **Evaluator**: Compares Parser Output with Ground Truth.
4.  **Export**: The best parser (Champion) is exported as a Python module or Regex list.

## 7. Next Steps
1.  **Data Acquisition**: We need 1000+ labeled names.
2.  **Prototyping**: Set up a simple script with DEAP that tries to learn simple "Given Name Family Name" patterns.
