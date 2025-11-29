# evoname

**Evolutionary Name Parser**

`evoname` is an experimental project to build a robust name parser (splitting strings like "Dr. Hans Müller" into structured JSON) using **Genetic Programming (GP)** and **Regular Expressions**.

Instead of manually writing thousands of rules, we "breed" the parser logic using an evolutionary algorithm (DEAP).

## 🏗 Architecture
*   **Hybrid Approach**: GP handles the control flow (logic tree), while Regex handles the pattern matching (tokens).
*   **Strictly Typed DSL**: Prevents invalid trees and ensures robustness.
*   **GitOps Factory**: The training pipeline automatically commits and publishes high-scoring models to npm.

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
pip install deap pytest
```

### Running Tests
```bash
python -m pytest tests/
```

### Data Generation
Generate synthetic training data:
```bash
python generate_data.py
```

### Training
Start the evolutionary training loop:
```bash
python trainer.py --generations 50 --pop-size 300
```
Checkpoints are saved in `runs/`.

### JavaScript Runtime
To use the parser in your project:

1.  Go to the **Actions** tab on GitHub.
2.  Click on the latest successful run.
3.  Scroll down to **Artifacts** and download `evoname-dist`.
4.  Extract `evoname.js` and use it with `library.js`.

Verify the JS library implementation locally:
```bash
node test_library.js
```

## 📅 Roadmap
- [x] Concept & Specs
- [x] Primitive Set & Regex Loader
- [x] Data Generation (Synthetic)
- [x] Trainer Implementation
- [x] JavaScript Runtime (`library.js`)
- [x] Transpiler (Python -> JS)
- [x] Automated CI/CD Pipeline

## 👥 Credits
Created by **Paul Hunck**.

## 📄 License
MIT
