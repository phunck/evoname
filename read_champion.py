import pickle
import sys
import os
from deap import gp, creator, base

# Mock classes to allow unpickling
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

def main():
    path = "runs/2025-11-29_213417/artifacts/champion.pkl"
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    try:
        with open(path, "rb") as f:
            ind = pickle.load(f)
        with open("champion_structure.txt", "w") as out:
            out.write(str(ind))
        print("Wrote champion structure to champion_structure.txt")
    except Exception as e:
        print(f"Error loading pickle: {e}")

if __name__ == "__main__":
    main()
