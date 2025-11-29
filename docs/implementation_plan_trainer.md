# Implementation Plan: trainer.py

## Goal
Implement the evolutionary training loop using DEAP.

## Components

### 1. Setup & Configuration
*   **Libraries**: `deap`, `random`, `json`, `pickle`, `argparse`, `datetime`.
*   **Arguments**:
    *   `--generations`: Number of generations (default: 50).
    *   `--pop-size`: Population size (default: 300).
    *   `--checkpoint`: Path to checkpoint to resume from (optional).
    *   `--seed`: Random seed (default: 42).
    *   `--data-dir`: Directory containing train/val/test.json (default: "data").

### 2. DEAP Initialization
*   **Creator**:
    *   `FitnessMax`: Weights = (1.0,) -> We maximize the score.
    *   `Individual`: List (Tree), with `fitness` attribute.
*   **Toolbox**:
    *   `register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=2)`
    *   `register("individual", tools.initIterate, creator.Individual, toolbox.expr)`
    *   `register("population", tools.initRepeat, list, toolbox.individual)`
    *   `register("compile", gp.compile, pset=pset)`
    *   `register("evaluate", evaluate_individual)`
    *   `register("select", tools.selTournament, tournsize=3)`
    *   `register("mate", gp.cxOnePoint)`
    *   `register("expr_mut", gp.genFull, min_=0, max_=2)`
    *   `register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)`
    *   **Constraints**: Decorate mate/mutate with `gp.staticLimit(key=operator.attrgetter("height"), max_value=17)` to prevent bloat.

### 3. Fitness Function (`evaluate_individual`)
*   **Input**: Individual (Tree).
*   **Logic**:
    *   Compile tree to Python function.
    *   Iterate over **Training Data**.
    *   Run function on `raw` string -> `NameObj`.
    *   Compare `NameObj` with `solution` (Ground Truth).
    *   Calculate F1 scores for: `given`, `family`, `title`, `gender`.
    *   **Weighted Sum**: `0.4*F1_given + 0.4*F1_family + 0.1*F1_title + 0.1*F1_gender`.
    *   **Parsimony Pressure**: `Score - (0.001 * len(individual))`.
    *   **Hard Constraints**: If `family` is empty -> Fitness = 0.
*   **Optimization**: Use `multiprocessing` if possible, or simple loop for V1.

### 4. Training Loop
*   **Algorithm**: `eaSimple` or custom loop (better for checkpointing).
*   **Stats**: Track Avg, Max, Min fitness.
*   **HallOfFame**: Keep best 1-5 individuals.
*   **Checkpointing**:
    *   Save `cp = dict(population=pop, generation=gen, halloffame=hof, logbook=logbook, rndstate=random.getstate())` to `runs/{id}/checkpoints/gen_{gen}.pkl` every N generations.

### 5. Output
*   Save the best individual (Champion) to `runs/{id}/artifacts/champion.pkl` (and text representation).
*   Evaluate Champion on **Validation Set** and print report.

## Step-by-Step Implementation
1.  **Helper Functions**: `calculate_f1`, `evaluate_dataset`.
2.  **Main Class**: `Trainer` class to encapsulate state.
3.  **CLI**: `main()` function.
