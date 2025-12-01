from collections import Counter
from typing import List, Dict, Any
from deap import gp

class DifficultyTracker:
    def __init__(self):
        self.failures = Counter()
        self.total_attempts = 0

    def update(self, population, data: List[Dict], pset):
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
                    self.failures[raw] += 1
                    
            except Exception:
                self.failures[raw] += 1
        
        self.total_attempts += 1

    def get_hall_of_shame(self, n=20):
        """Returns the top N most frequent failures."""
        return self.failures.most_common(n)
