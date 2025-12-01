from collections import Counter
from typing import List, Dict, Any
from deap import gp

class DifficultyTracker:
    def __init__(self):
        self.failures = Counter()
        self.failure_data = {} # Map raw -> full entry
        self.total_attempts = 0

    def update(self, population, data: List[Dict], pset):
        # ... (rest of update method is fine, we patched the loop above)
        pass 

    # We need to patch the update method properly in the previous step or here. 
    # The previous step patched the loop inside update. 
    # Here we just fix __init__ and save/load.

    def get_hall_of_shame(self, n=20):
        """Returns the top N most frequent failures."""
        return self.failures.most_common(n)

    def save(self, path="difficulty.json"):
        import json
        # Save both counts and the data
        export = {
            "counts": dict(self.failures),
            "data": self.failure_data
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(export, f, indent=2)

    def load(self, path="difficulty.json"):
        import json
        import os
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                export = json.load(f)
                if "counts" in export:
                    self.failures.update(export["counts"])
                    self.failure_data.update(export.get("data", {}))
                else:
                    # Legacy format support (just counts)
                    self.failures.update(export)
        """
        Updates failure counts based on the best individual's performance.
        We only track failures of the BEST individual to see what is 'hard' for the current state of the art.
        """
        # Find best individual
        best_ind = max(population, key=lambda ind: ind.fitness.values[0])
        func = gp.compile(best_ind, pset)
        
        for entry in data:
            raw = entry['raw']
            expected = entry['solution']
            
            try:
                result = func(raw)
                # Simple check: if fitness < 1.0 (imperfect), count as failure
                # Or stricter: if fitness < 0.8
                # Let's use a simple heuristic: if family name is wrong
                
                # We don't have the fitness function here easily available without re-calculating.
                # So let's just check exact match of family name as a proxy for "hard"
                
                res_fam = result.family.lower().strip()
                exp_fam = expected['family'].lower().strip()
                
                if res_fam != exp_fam:
                    # Store full entry as JSON string to be hashable, or use a tuple key
                    # We use raw string as key, but store the full entry in a separate dict
                    self.failures[raw] += 1
                    self.failure_data[raw] = entry
                    
            except Exception:
                self.failures[raw] += 1
                self.failure_data[raw] = entry
        
        self.total_attempts += 1

    def get_hall_of_shame(self, n=20):
        """Returns the top N most frequent failures."""
        return self.failures.most_common(n)

    def save(self, path="difficulty.json"):
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dict(self.failures), f, indent=2)

    def load(self, path="difficulty.json"):
        import json
        import os
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.failures.update(data)
