# Implementation Plan: Evolution Dashboard

## Goal
Create a local Web UI (`dashboard.py`) to control the training process, visualize progress, and interactively test the evolving model.

## Architecture

### 1. Backend (`dashboard.py` - Flask)
*   **Role**: Orchestrator.
*   **Features**:
    *   `POST /start`: Starts `trainer.py` as a subprocess with given parameters (pop size, generations, etc.).
    *   `POST /stop`: Kills the training subprocess.
    *   `GET /stats`: Returns the latest training statistics (Generation, Fitness, Sample Results).
    *   `POST /transpile`: Triggers `transpiler.py` on the current best model.
    *   `GET /champion.js`: Serves the transpiled JS for the frontend.

### 2. Trainer Integration (`trainer.py`)
*   **Modification**: Add a `--monitor` flag.
*   **Behavior**: When enabled, the trainer writes a `monitor.json` file every generation.
*   **Content of `monitor.json`**:
    *   `generation`: Current generation number.
    *   `best_fitness`: Score of the champion.
    *   `avg_fitness`: Average population score.
    *   `samples`: A list of 5 sample inputs and the champion's output for them (to visualize "Versuchskaninchen").

### 3. Frontend (`dashboard/templates/index.html`)
*   **Tech**: HTML, Vanilla JS, Chart.js (via CDN or local), Bootstrap/Tailwind (optional, stick to simple CSS).
*   **Sections**:
    *   **Controls**: Inputs for Pop Size, Generations. Start/Stop buttons.
    *   **Live Monitor**:
        *   Line Chart: Fitness over time.
        *   "Guinea Pigs": Table showing 5 random names and how the current champion parses them.
    *   **Playground**:
        *   Input field for custom name.
        *   "Test Champion" button (loads generated JS and runs it).
        *   Output display.

## Step-by-Step Implementation

1.  **Modify `trainer.py`**:
    *   Add `--monitor` argument.
    *   Implement `write_monitor_stats(gen, population)` function.
    *   Select 5 fixed sample names at startup to track consistently.

2.  **Create `dashboard.py`**:
    *   Setup Flask app.
    *   Implement subprocess management for `trainer.py`.
    *   Implement file reading for `monitor.json`.

3.  **Create Frontend**:
    *   Build the HTML structure.
    *   Implement polling loop (fetch `/stats` every 1s).
    *   Implement Chart.js update logic.
    *   Implement Playground logic (dynamic script loading).

## Dependencies
*   `flask` (Need to install).
