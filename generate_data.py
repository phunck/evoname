import json
import random
import os
from typing import List, Dict

def load_data(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

import json
import random
import os
from typing import List, Dict, Any

# --- Configuration ---
NUM_SAMPLES = 1000
TRAIN_SPLIT = 0.8
VAL_SPLIT = 0.1
TEST_SPLIT = 0.1
SEED = 42

# --- Vocabulary ---
MALE_NAMES = ["Hans", "Peter", "Michael", "Thomas", "Andreas", "Wolfgang", "Klaus", "Jürgen", "Stefan", "Christian", "James", "John", "Robert", "David", "William"]
FEMALE_NAMES = ["Maria", "Ursula", "Monika", "Petra", "Elisabeth", "Sabine", "Renate", "Helga", "Karin", "Brigitte", "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth"]
LAST_NAMES = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann", "Smith", "Johnson", "Williams", "Brown", "Jones"]
TITLES = ["Dr.", "Prof.", "Prof. Dr.", "Dr. med.", "Dipl.-Ing."]
SALUTATIONS_MALE = ["Herr", "Mr.", "Mr"]
SALUTATIONS_FEMALE = ["Frau", "Mrs.", "Ms.", "Mrs", "Ms"]
PARTICLES = ["von", "van", "de", "vom", "zu"]
SUFFIXES = ["Jr.", "Sr.", "III", "PhD"]

def generate_random_name() -> Dict[str, Any]:
    gender_key = random.choice(["m", "f"])
    
    # Components
    salutation = ""
    title = ""
    given = ""
    middle = []
    particle = ""
    family = ""
    suffix = ""
    
    # 1. Salutation (80% chance)
    if random.random() < 0.8:
        if gender_key == "m":
            salutation = random.choice(SALUTATIONS_MALE)
        else:
            salutation = random.choice(SALUTATIONS_FEMALE)
            
    # 2. Title (30% chance)
    if random.random() < 0.3:
        title = random.choice(TITLES)
        
    # 3. Given Name
    names_list = MALE_NAMES if gender_key == "m" else FEMALE_NAMES
    given = random.choice(names_list)
    
    # 4. Middle Name (20% chance)
    if random.random() < 0.2:
        middle_name = random.choice(names_list)
        if middle_name != given:
            middle = [middle_name]
            
    # 5. Particle (10% chance)
    if random.random() < 0.1:
        particle = random.choice(PARTICLES)
        
    # 6. Family Name
    family = random.choice(LAST_NAMES)
    
    # 7. Suffix (5% chance)
    if random.random() < 0.05:
        suffix = random.choice(SUFFIXES)
        
    # Construct Raw String
    parts = []
    if salutation: parts.append(salutation)
    if title: parts.append(title)
    parts.append(given)
    parts.extend(middle)
    if particle: parts.append(particle)
    parts.append(family)
    if suffix: parts.append(suffix)
    
    raw = " ".join(parts)
    
    # Construct Solution Object
    solution = {
        "given": given,
        "family": family,
        "middle": middle,
        "title": [title] if title else [],
        "salutation": salutation,
        "gender": gender_key,
        "suffix": [suffix] if suffix else [],
        "particles": [particle] if particle else []
    }
    
    return {
        "raw": raw,
        "solution": solution
    }

def main():
    random.seed(SEED)
    
    print(f"Generating {NUM_SAMPLES} synthetic names...")
    data = [generate_random_name() for _ in range(NUM_SAMPLES)]
    
    # Shuffle
    random.shuffle(data)
    
    # Split
    n_train = int(NUM_SAMPLES * TRAIN_SPLIT)
    n_val = int(NUM_SAMPLES * VAL_SPLIT)
    
    train_data = data[:n_train]
    val_data = data[n_train:n_train+n_val]
    test_data = data[n_train+n_val:]
    
    # Save
    os.makedirs("data", exist_ok=True)
    
    with open("data/train.json", "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=2, ensure_ascii=False)
        
    with open("data/val.json", "w", encoding="utf-8") as f:
        json.dump(val_data, f, indent=2, ensure_ascii=False)
        
    with open("data/test.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
        
    print(f"Saved {len(train_data)} train, {len(val_data)} val, {len(test_data)} test samples.")

if __name__ == "__main__":
    main()
