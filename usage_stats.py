from collections import Counter
from typing import List, Dict, Any
from deap import gp

class PrimitiveUsageTracker:
    def __init__(self, pset: gp.PrimitiveSetTyped):
        self.pset = pset
        self.primitive_counts = Counter()
        self.terminal_counts = Counter()
        self.total_nodes = 0
        self.total_individuals = 0

    def update(self, population: List[Any]):
        """
        Analyzes the population to count primitive usage.
        Resets counts before analysis to provide a snapshot of the current generation.
        """
        self.primitive_counts.clear()
        self.terminal_counts.clear()
        self.total_nodes = 0
        self.total_individuals = len(population)

        for ind in population:
            for node in ind:
                if isinstance(node, gp.Primitive):
                    self.primitive_counts[node.name] += 1
                elif isinstance(node, gp.Terminal):
                    # For terminals, we might want the value or the name
                    name = str(node.value)
                    # If it's an ephemeral constant or named terminal
                    if hasattr(node, 'name'):
                        name = node.name
                    self.terminal_counts[name] += 1
                
                self.total_nodes += 1

    def get_stats(self, top_n=20) -> str:
        """Returns a formatted string of usage statistics."""
        if self.total_individuals == 0:
            return "No data."

        output = []
        output.append(f"Primitive Usage Stats (Snapshot of {self.total_individuals} individuals)")
        output.append("-" * 60)
        output.append(f"{'Name':<30} | {'Count':<8} | {'% of Nodes':<10}")
        output.append("-" * 60)

        # Combine and sort
        all_counts = self.primitive_counts + self.terminal_counts
        
        for name, count in all_counts.most_common(top_n):
            perc = (count / self.total_nodes) * 100
            output.append(f"{name:<30} | {count:<8} | {perc:<6.2f}%")
            
        return "\n".join(output)
