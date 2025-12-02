import pickle
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from primitive_set import create_pset, tokenize, NameObj, RegexToken

def main():
    # console = Console() # Removed
    
    # Load Champion
    model_path = "model/champion.pkl"
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}")
        return

    with open(model_path, "rb") as f:
        champion = pickle.load(f)
    
    pset = create_pset()
    func = pset.context["make_name_obj"]
    
    # Compile the individual
    from deap import gp
    compiled_ind = gp.compile(champion, pset)
    
    # Hall of Shame Examples to Debug
    examples = [
        "Frau Dipl.-Ing. Petra Schneider",
        "Mrs. Karin de Jones",
        "Mr. Robert Schneider",
        "Prof. Dr. Petra Brown",
        "Dr. med. Robert Brown",
        "James Brown PhD"
    ]
    
    print("=" * 60)
    print("CHAMPION DEBUG ANALYSIS")
    print("=" * 60)

    for raw in examples:
        print(f"\n[INPUT]: {raw}")
        
        # 1. Tokenize
        tokens = tokenize(raw)
        token_str = ", ".join([f"{t.value}({t.type.name})" for t in tokens])
        print(f"[TOKENS]: {token_str}")
        
        # 2. Predict
        try:
            pred: NameObj = compiled_ind(raw)
            
            print("[PREDICTION]:")
            print(f"  Salutation: '{pred.salutation}'")
            print(f"  Title:      {pred.title}")
            print(f"  Given:      '{pred.given}'")
            print(f"  Family:     '{pred.family}'")
            print(f"  Suffix:     {pred.suffix}")
            print(f"  Particles:  {pred.particles}")
            
            # Identify obvious issues (heuristics)
            issues = []
            if "Dipl.-Ing." in raw and "Dipl.-Ing." not in pred.title:
                issues.append("Missing Title: Dipl.-Ing.")
            if "de" in raw and "de" not in pred.particles and "de" not in pred.family:
                issues.append("Missing Particle: de")
            if "PhD" in raw and "PhD" not in pred.suffix and "PhD" not in pred.title:
                issues.append("Missing PhD")
            
            if issues:
                print(f"[ISSUES]: {', '.join(issues)}")
            else:
                print("[ISSUES]: None detected by heuristic")
            
        except Exception as e:
            print(f"[ERROR]: {e}")
        
        print("-" * 60)

    print(f"\n[TREE]: {str(champion)}")

if __name__ == "__main__":
    main()
