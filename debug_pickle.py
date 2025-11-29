import pickle
import sys
import os
from deap import gp, creator, base

# Ensure current dir is in path
sys.path.append(os.getcwd())

import primitive_set

print("primitive_set file:", primitive_set.__file__)
print("Has StringList?", hasattr(primitive_set, "StringList"))
if hasattr(primitive_set, "StringList"):
    print("StringList:", primitive_set.StringList)

# Recreate DEAP classes
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

path = "runs/2025-11-29_023945/artifacts/champion.pkl"
print(f"Loading {path}...")

with open(path, "rb") as f:
    try:
        champion = pickle.load(f)
        print("Success!")
        print(champion)
    except Exception as e:
        print("Failed:", e)
        import traceback
        traceback.print_exc()
