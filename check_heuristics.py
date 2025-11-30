import json
from primitive_set import tokenize, extract_given_str, extract_family_str, extract_salutation_str, extract_title_list, NameObj

def calculate_f1(pred, truth):
    # Simple string match F1
    if not pred and not truth: return 1.0
    if pred == truth: return 1.0
    return 0.0

def main():
    print("Loading data/train.json...")
    with open("data/train.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"Testing heuristics on {len(data)} samples...")
    
    correct_given = 0
    correct_family = 0
    correct_salutation = 0
    
    for entry in data:
        raw = entry["raw"]
        truth = entry["solution"]
        
        # 1. Tokenize
        tokens = tokenize(raw)
        
        # 2. Run Heuristics
        h_given = extract_given_str(tokens)
        h_family = extract_family_str(tokens)
        h_salutation = extract_salutation_str(tokens)
        
        # 3. Compare
        if h_given == truth.get("given", ""): correct_given += 1
        if h_family == truth.get("family", ""): correct_family += 1
        if h_salutation == truth.get("salutation", ""): correct_salutation += 1
        
    print("\n--- Heuristic Baseline Performance ---")
    print(f"Given Name Accuracy:  {correct_given/len(data):.2%}")
    print(f"Family Name Accuracy: {correct_family/len(data):.2%}")
    print(f"Salutation Accuracy:  {correct_salutation/len(data):.2%}")
    
    print("\nIf these numbers are high, the GP *should* be able to find a solution.")
    print("If they are low, our primitives are too weak.")

if __name__ == "__main__":
    main()
