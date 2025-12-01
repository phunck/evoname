import json
import pickle
import os
from typing import List, Dict
from rich.console import Console
from rich.table import Table
from deap import gp

from primitive_set import create_pset, NameObj
from evaluator import calculate_f1
from oracle import OracleParser
from config import weights_main_strict

def load_dataset(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_model(model_func, data: List[Dict]) -> Dict[str, float]:
    """
    Evaluates a model (function or callable) on the data.
    Returns a dictionary of average F1 scores.
    """
    scores = {
        "given": 0.0, "family": 0.0, "title": 0.0, "gender": 0.0,
        "middle": 0.0, "suffix": 0.0, "particles": 0.0, "salutation": 0.0,
        "exact": 0.0
    }
    n = len(data)
    valid_gender = 0
    
    for entry in data:
        raw = entry["raw"]
        solution = entry["solution"]
        
        try:
            pred: NameObj = model_func(raw)
        except Exception:
            continue # Skip failures (shouldn't happen for Oracle/Champion)
            
        # Core
        f1_given = calculate_f1(pred.given, solution["given"])
        f1_family = calculate_f1(pred.family, solution["family"])
        f1_title = calculate_f1(pred.title, solution["title"])
        
        # Gender
        truth_gender = solution.get("gender")
        f1_gender = 0.0
        if truth_gender and truth_gender != "null":
            valid_gender += 1
            pred_gender = pred.gender.value if pred.gender else "null"
            if pred_gender == truth_gender:
                f1_gender = 1.0
                
        # Optional
        f1_middle = calculate_f1(pred.middle, solution["middle"])
        f1_suffix = calculate_f1(pred.suffix, solution["suffix"])
        f1_particles = calculate_f1(pred.particles, solution["particles"])
        f1_salutation = calculate_f1(pred.salutation, solution["salutation"])
        
        # Exact Match
        is_exact = (f1_given == 1.0 and f1_family == 1.0 and f1_title == 1.0 and
                    f1_middle == 1.0 and f1_suffix == 1.0 and f1_particles == 1.0 and
                    f1_salutation == 1.0)
        # Gender match for exact? Usually yes.
        if truth_gender and truth_gender != "null":
             pred_gender = pred.gender.value if pred.gender else "null"
             if pred_gender != truth_gender: is_exact = False

        scores["given"] += f1_given
        scores["family"] += f1_family
        scores["title"] += f1_title
        scores["gender"] += f1_gender
        scores["middle"] += f1_middle
        scores["suffix"] += f1_suffix
        scores["particles"] += f1_particles
        scores["salutation"] += f1_salutation
        if is_exact: scores["exact"] += 1.0

    # Average
    for key in scores:
        if key == "gender":
            scores[key] /= valid_gender if valid_gender > 0 else 1
        else:
            scores[key] /= n
            
    return scores

def main():
    console = Console()
    
    # 1. Load Data
    val_path = "data/val.json"
    if not os.path.exists(val_path):
        console.print(f"[red]Error: {val_path} not found.[/red]")
        return
    data = load_dataset(val_path)
    console.print(f"Loaded {len(data)} validation samples.")
    
    # 2. Load Champion
    model_path = "model/champion.pkl"
    if not os.path.exists(model_path):
        console.print(f"[red]Error: {model_path} not found. Train a model first![/red]")
        return
        
    with open(model_path, "rb") as f:
        champion = pickle.load(f)
    
    pset = create_pset()
    gp_func = gp.compile(champion, pset)
    
    # 3. Setup Oracle
    oracle = OracleParser()
    
    # 4. Evaluate
    console.print("Evaluating Oracle...")
    oracle_scores = evaluate_model(oracle.parse, data)
    
    console.print("Evaluating Champion...")
    gp_scores = evaluate_model(gp_func, data)
    
    # 5. Report
    table = Table(title="🏆 Baseline (Oracle) vs. Champion (GP) 🏆")
    table.add_column("Metric", style="cyan")
    table.add_column("Oracle (Baseline)", justify="right")
    table.add_column("Champion (GP)", justify="right", style="bold green")
    table.add_column("Lift", justify="right")
    
    metrics = ["exact", "given", "family", "title", "salutation", "gender", "middle", "suffix", "particles"]
    
    for m in metrics:
        base = oracle_scores[m]
        champ = gp_scores[m]
        diff = champ - base
        lift = (diff / base * 100) if base > 0 else 0.0
        
        color = "green" if diff >= 0 else "red"
        lift_str = f"[{color}]{lift:+.1f}%[/{color}]"
        
        table.add_row(
            m.capitalize(),
            f"{base:.4f}",
            f"{champ:.4f}",
            lift_str
        )
        
    console.print(table)

if __name__ == "__main__":
    main()
