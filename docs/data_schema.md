# Data Schema & Labelling Guidelines

To ensure training (Evolution) and evaluation work correctly, we need a strict schema for the "Ground Truth".

## 1. JSON Data Structure (Training Entry)
Each entry in the dataset consists of the input string (`raw`) and the expected solution (`solution`).

```json
{
  "id": "unique_id_123",
  "raw": "Dr. med. Hans Peter Müller",
  "solution": {
    "title": ["Dr.", "med."],
    "given": "Hans",
    "middle": ["Peter"],
    "family": "Müller",
    "suffix": [],
    "particles": [],
    "salutation": "Herr",
    "gender": "m", // "m", "f", "d", "null" (unknown)
    "gender_source": "explicit", // "explicit" (salutation), "implicit" (name-lookup), "manual"
    "gender_confidence": 1.0, // 0.0 - 1.0
    "gender_candidates": [ // Optional for ambiguity
        { "gender": "m", "p": 0.62 },
        { "gender": "f", "p": 0.38 }
    ]
  },
  "meta": {
    "locale": "de-DE",
    "source": "manual_labeling_v1",
    "difficulty": "medium"
  }
}
```

## 2. Field Definitions
*   **raw**: The unchanged input string.
*   **title**: Academic titles and honorifics (e.g., "Dr.", "Prof.", "Mr.").
*   **given**: The first name (given name).
*   **middle**: Additional first names.
*   **family**: The surname (without particles).
*   **suffix**: Name suffixes (e.g., "Jr.", "III").
*   **particles**: Prefixes to the surname (e.g., "von", "de", "van").
*   **salutation**: The extracted salutation word (e.g., "Herr", "Mrs.").
*   **gender**: Normalized classification ("m", "f", "d", "null").
*   **gender_source**: Origin of the gender classification.

## 3. Labelling Guidelines (Edge Cases)
*   **Particles**: "von der Leyen" -> particles: ["von", "der"], family: "Leyen".
*   **Double Names**: "Müller-Lüdenscheidt" -> family: "Müller-Lüdenscheidt" (as one string, since hyphenated).
*   **Uncertainty**: If a part cannot be clearly assigned, it is added to `raw` or an `unparsed` field in doubt, or the entry is marked as a "Hard Case".

## 4. Data Governance
*   **Versioning**: Datasets are versioned (e.g., `data_v1.json`).
*   **Split**:
    *   **Train**: 70% (for Evolution).
    *   **Validation**: 15% (for Selection/Hyperparameter).
    *   **Test**: 15% (Hidden, only for Release Decision).
*   **Feedback Loop**: Failed parses from production are collected, manually corrected, and included in the next data version (`data_v2`) -> Warmstart Training.
