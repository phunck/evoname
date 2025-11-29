import json
import random
import os
from typing import List, Dict

def load_data(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def split_data(data: List[Dict], train_ratio=0.6, val_ratio=0.2):
    # Shuffle consistently
    random.seed(42)
    random.shuffle(data)
    
    n = len(data)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    
    train = data[:n_train]
    val = data[n_train:n_train+n_val]
    test = data[n_train+n_val:]
    
    return train, val, test

def save_split(data: List[Dict], filename: str, output_dir="data"):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} entries to {path}")

def main():
    input_file = "data_dummy.json"
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Loading data from {input_file}...")
    data = load_data(input_file)
    
    # For very small datasets (like smoke test), ensure at least 1 item in each if possible
    if len(data) < 5:
        print("Warning: Dataset very small. Splitting might be trivial.")
        train, val, test = data, data, data # Overlap for smoke test
    else:
        train, val, test = split_data(data)

    save_split(train, "train.json")
    save_split(val, "val.json")
    save_split(test, "test.json")
    
    print("Data generation complete.")

if __name__ == "__main__":
    main()
