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
### Training & Building
1. **Generate Data** (Optional, creates fresh synthetic names):
   ```bash
   python generate_data.py
   ```

2. **Train Model**:
   ```bash
   python trainer.py --generations 300 --pop-size 1000
   ```
   The best model is saved to `runs/LATEST/artifacts/champion.pkl`.

3. **Save Champion (Best Practice)**:
   To share your best model or use it on other machines, copy it to the `model/` directory and commit it:
   ```bash
   cp runs/LATEST/artifacts/champion.pkl model/champion.pkl
   git add model/champion.pkl
   git commit -m "Update champion model"
   ```

4. **Transpile to JavaScript**:
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

## 👥 Credits
Created by **Paul Hunck**.

## 📄 License
MIT
