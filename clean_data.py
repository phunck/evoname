import json
import re

def clean_data(path):
    print(f"Cleaning {path}...")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    count = 0
    for entry in data:
        sol = entry["solution"]
        new_titles = []
        modified = False
        
        for t in sol.get("title", []):
            # Split on space if it's not just a single token
            if " " in t:
                parts = t.split(" ")
                # Filter empty
                parts = [p for p in parts if p]
                new_titles.extend(parts)
                modified = True
            else:
                new_titles.append(t)
        
        if modified:
            sol["title"] = new_titles
            count += 1
            
    print(f"Modified {count} entries.")
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Done.")

if __name__ == "__main__":
    clean_data("data/train.json")
    # Also clean val.json if it exists, but let's stick to train for now or check existence
    import os
    if os.path.exists("data/val.json"):
        clean_data("data/val.json")
