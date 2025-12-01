import random
import json
import os
import argparse
import datetime
from typing import List, Dict

from rich.console import Console
from evolution import Trainer

def load_dataset(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    console = Console()
    parser = argparse.ArgumentParser(
        description="🧬 EvoName Trainer - Genetic Programming for Name Parsing",
        epilog="Example: python trainer.py --generations 50 --pop-size 300 --swap 5 --resume --info",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--generations", type=int, default=50, help="Number of generations to evolve.")
    parser.add_argument("--pop-size", type=int, default=300, help="Population size per island.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--data-dir", type=str, default="data", help="Directory containing train.json/val.json.")
    parser.add_argument("--checkpoint", type=str, help="Path to checkpoint file to resume from.")
    parser.add_argument("--run-id", type=str, help="Custom Run ID for logging.")
    parser.add_argument("--monitor", action="store_true", help="Enable live monitoring (writes monitor.json).")
    parser.add_argument("--seed-model", type=str, help="Path to a champion.pkl to seed the population with.")
    parser.add_argument("--swap", type=str, default="5", help="Migration interval(s). Single int (e.g. '5') or comma-separated (e.g. '3,5,7').")
    parser.add_argument("--resume", action="store_true", help="Resume training from saved island populations (model/island_*.pkl).")
    parser.add_argument("--info", action="store_true", help="Show detailed fitness breakdown and stats per generation.")
    parser.add_argument("--jobs", "-j", type=int, default=os.cpu_count(), help="Number of parallel jobs for evaluation (default: all cores).")
    
    args = parser.parse_args()
    
    # Reproducibility
    random.seed(args.seed)
    
    # Load Data
    train_path = os.path.join(args.data_dir, "train.json")
    val_path = os.path.join(args.data_dir, "val.json")
    
    if not os.path.exists(train_path):
        print(f"Error: Training data not found at {train_path}")
        return
        
    train_data = load_dataset(train_path)
    val_data = load_dataset(val_path) if os.path.exists(val_path) else []
    
    print(f"Loaded {len(train_data)} training samples.")
    
    # Initialize and Run Trainer
    trainer = Trainer(args, train_data, val_data)
    trainer.train()

if __name__ == "__main__":
    main()
