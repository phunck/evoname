import yaml
import os
from typing import Dict

# Load Configuration
CONFIG_PATH = "config.yaml"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

# --- EXPORTED CONFIGURATIONS ---

# GA Parameters
DEFAULT_CXPB = config["ga_parameters"]["cxpb"]
DEFAULT_MUTPB = config["ga_parameters"]["mutpb"]
BLOAT_LIMIT = config["ga_parameters"].get("bloat_limit", 17)

# Curriculum
WARMUP_GENS = config["curriculum"]["warmup"]
RAMP_SPAN = config["curriculum"]["ramp_span"]

# Island Configs
weights_main_easy = config["weights_main_easy"]
gates_main_easy = config["gates_main_easy"]

weights_main_strict = config["weights_main_strict"]
gates_main_strict = config["gates_main_strict"]

weights_detail = config["weights_detail"]
GATES_DETAIL = config["gates_detail"]

weights_structure = config["weights_structure"]
GATES_STRUCTURE = config["gates_structure"]

# --- HELPER FUNCTIONS ---
def lerp(a: float, b: float, t: float) -> float:
    return a * (1.0 - t) + b * t

def get_main_weights(gen: int, warmup: int = WARMUP_GENS, ramp_span: int = RAMP_SPAN) -> Dict[str, float]:
    if gen <= warmup: return weights_main_easy
    t = (gen - warmup) / float(ramp_span)
    if t >= 1.0: return weights_main_strict
    
    w = {}
    for key in weights_main_easy.keys():
        w[key] = lerp(weights_main_easy[key], weights_main_strict[key], t)
    return w

def get_main_gates(gen: int, warmup: int = WARMUP_GENS, ramp_span: int = RAMP_SPAN) -> Dict[str, float]:
    if gen <= warmup: return gates_main_easy
    t = (gen - warmup) / float(ramp_span)
    if t >= 1.0: return gates_main_strict
    
    g = {}
    for key in ["min_family", "min_given", "max_penalty"]:
        g[key] = lerp(gates_main_easy[key], gates_main_strict[key], t)
    return g
