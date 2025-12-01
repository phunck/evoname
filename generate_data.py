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

def generate_random_name(difficulty: str = "normal") -> Dict[str, Any]:
    gender_key = random.choice(["m", "f"])
    
    # Components
    salutation = ""
    title = ""
    given = ""
    middle = []
    particle = ""
    family = ""
    suffix = ""
    
    # Probabilities based on difficulty
    p_salutation = 0.8
    p_title = 0.3
    p_middle = 0.2
    p_particle = 0.1
    p_suffix = 0.05
    
    if difficulty == "hard":
        p_title = 0.8      # High chance of title
        p_suffix = 0.5     # High chance of suffix
        p_middle = 0.4     # More middle names
        p_particle = 0.3   # More particles
    
    # 1. Salutation
    if random.random() < p_salutation:
        if gender_key == "m":
            salutation = random.choice(SALUTATIONS_MALE)
        else:
            salutation = random.choice(SALUTATIONS_FEMALE)
            
    # 2. Title
    if random.random() < p_title:
        title = random.choice(TITLES)
        
    # 3. Given Name
    names_list = MALE_NAMES if gender_key == "m" else FEMALE_NAMES
    given = random.choice(names_list)
    
    # 4. Middle Name
    if random.random() < p_middle:
        middle_name = random.choice(names_list)
        if middle_name != given:
            middle = [middle_name]
            
    # 5. Particle
    if random.random() < p_particle:
        particle = random.choice(PARTICLES)
        
    # 6. Family Name
    family = random.choice(LAST_NAMES)
    
    # 7. Suffix
    if random.random() < p_suffix:
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
    
    # 70% Normal, 30% Hard (including Hall of Shame)
    n_hard = int(NUM_SAMPLES * 0.3)
    n_normal = NUM_SAMPLES - n_hard
    
    data = []
    
    # 1. Inject Hall of Shame (if available)
    try:
        with open("difficulty.json", "r", encoding="utf-8") as f:
            shame_export = json.load(f)
            
            # Handle both legacy (list/dict of counts) and new (dict with 'data') formats
            shame_data = {}
            if "data" in shame_export:
                shame_data = shame_export["data"]
            
            if shame_data:
                # Get the keys (raw strings) sorted by failure count if possible, 
                # but here we just take all available data entries.
                # If we have counts, we could prioritize.
                
                shame_entries = list(shame_data.values())
                # Oversample them? Let's add them 3 times each to force learning
                print(f"Injecting {len(shame_entries)} Hall of Shame examples (3x oversampling)...")
                for _ in range(3):
                    data.extend(shame_entries)
            else:
                print("Hall of Shame found but no data entries (legacy format). Skipping injection.")
                
    except FileNotFoundError:
        print("No Hall of Shame found (difficulty.json).")

    # 2. Generate Data
    data.extend([generate_random_name(difficulty="normal") for _ in range(n_normal)])
    data.extend([generate_random_name(difficulty="hard") for _ in range(n_hard)])
    
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
