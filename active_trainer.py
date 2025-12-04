import subprocess
import sys
import time
import argparse
import json
import os

def run_command(cmd):
    print(f"🚀 Running: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {cmd}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="🔄 EvoName Active Learning Loop")
    parser.add_argument("--cycles", type=int, default=10, help="Number of active learning cycles.")
    parser.add_argument("--gens-per-cycle", type=int, default=30, help="Generations per cycle.")
    parser.add_argument("--pop-size", type=int, default=300, help="Population size.")
    parser.add_argument("--jobs", type=int, default=8, help="Number of parallel jobs.")
    parser.add_argument("--swap", type=str, default="5", help="Migration interval(s). Single int or comma-separated.")
    
    args = parser.parse_args()
    
    print("==================================================")
    print(" 🧬 EvoName Active Learning Loop")
    print("==================================================")
    print(f"Cycles: {args.cycles}")
    print(f"Gens/Cycle: {args.gens_per_cycle}")
    print("💡 Tip: Press Ctrl+C once to stop gracefully after the current generation.")
    print("==================================================\n")
    
    try:
        for i in range(args.cycles):
            print(f"\n>>> CYCLE {i+1}/{args.cycles} <<<\n")
            
            # 1. Generate Data (will read difficulty.json if exists)
            print("--- Step 1: Generating Data (Targeted) ---")
            run_command("python generate_data.py")
            
            # 2. Train (Resume if not first cycle, or if user wants to resume previous run)
            # We always use --resume to keep the population evolving.
            # If it's a fresh start, ensure model/ directory is empty or ignore resume warning.
            print(f"--- Step 2: Training ({args.gens_per_cycle} generations) ---")
            
            # We need to pass the TOTAL generations target to trainer.py if it resumes?
            # No, trainer.py loop is `range(start_gen, args.generations)`.
            # If we resume, we need to know where we left off, OR trainer.py needs to handle incremental generations.
            # Currently trainer.py starts from 0 unless we modify it to load generation count.
            # BUT: DEAP's logbook or the population file doesn't explicitly store "current generation" in a way trainer.py reads to set start_gen.
            # trainer.py just loads the population and runs for `args.generations`.
            # So if we say --generations 30, it runs 30 *more* generations?
            # Let's check trainer.py loop: `for gen in range(start_gen, self.args.generations):`
            # `start_gen` is hardcoded to 0.
            # So it will run 0..30.
            # If we resume, we load the population, but the generation counter resets to 0 in the logs.
            # That's fine for now, effectively we run 30 more generations each time.
            
            cmd = f"python trainer.py --generations {args.gens_per_cycle} --pop-size {args.pop_size} --resume --jobs {args.jobs} --swap {args.swap}"
            run_command(cmd)
            
            # 3. Adaptive Weighting
            print("--- Step 3: Adaptive Weighting ---")
            update_weights("cycle_stats.json", "config.yaml")
            
            # 4. Fresh Blood Injection (Diversity Check)
            check_diversity("diversity_stats.json")
            
            print(f"✅ Cycle {i+1} completed.")
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Active Learning Loop Interrupted by User.")
        print("Exiting gracefully...")
        sys.exit(0)

def update_weights(stats_path, config_path):
    if not os.path.exists(stats_path):
        print(f"⚠️ Stats file {stats_path} not found. Skipping adaptation.")
        return
        
    try:
        import yaml
        
        with open(stats_path, "r") as f:
            stats = json.load(f)
            
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        print(f"📊 Current Stats: Title={stats['title']:.2f}, Suffix={stats['suffix']:.2f}, Family={stats['family']:.2f}")
        
        # Heuristic: Weight = (1.0 - F1) * Scaling Factor
        # We want weights to sum to roughly the same total for core components (~0.8)
        
        target_components = ["title", "suffix", "family", "given"]
        raw_weights = {}
        
        for comp in target_components:
            f1 = stats.get(comp, 0.5)
            # Base weight is inverse of performance
            # Min weight 0.20 to prevent forgetting (Catastrophic Forgetting)
            w = max(0.20, (1.0 - f1)) 
            raw_weights[comp] = w
            
        # Normalize to keep total core weight around 0.8 (leaving 0.2 for gender/bonuses)
        total_raw = sum(raw_weights.values())
        target_total = 0.8
        
        new_weights = {}
        for comp, w in raw_weights.items():
            normalized = (w / total_raw) * target_total
            new_weights[f"core_{comp}"] = round(normalized, 3)
            
        # Update config (weights_main_strict)
        # We only update strict weights because easy weights are for warmup
        old_weights = config["weights_main_strict"]
        
        print("⚖️  Adjusting Weights (Main Strict):")
        for key, val in new_weights.items():
            old_val = old_weights.get(key, 0.0)
            print(f"   - {key}: {old_val} -> {val}")
            config["weights_main_strict"][key] = val
            
        # Also update Structure Island to follow suit? 
        # Maybe keep Structure specialized (high title), but let Main adapt.
        # Let's just update Main Strict for now.
            
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, sort_keys=False)
            
        print("✅ Config updated.")
        
    except Exception as e:
        print(f"❌ Failed to update weights: {e}")

def check_diversity(stats_path):
    if not os.path.exists(stats_path):
        return
        
    try:
        with open(stats_path, "r") as f:
            stats = json.load(f)
            
        diversity = stats.get("diversity", 1.0)
        print(f"🧬 Diversity: {diversity:.2f}")
        
        if diversity < 0.20:
            print("\n⚠️  CRITICAL: Low Diversity Detected! (< 0.20)")
            print("💉 INJECTING FRESH BLOOD...")
            
            # Delete Satellite Islands to force restart
            # Main Island is kept (Champion survives)
            # Satellites will be re-initialized randomly by trainer.py
            
            files_to_delete = [
                "model/island_detail.pkl",
                "model/island_structure.pkl"
            ]
            
            for p in files_to_delete:
                if os.path.exists(p):
                    os.remove(p)
                    print(f"   - Deleted {p} (will be re-seeded)")
            
            print("✅ Fresh Blood Injection prepared for next cycle.\n")
            
    except Exception as e:
        print(f"❌ Failed to check diversity: {e}")

if __name__ == "__main__":
    main()
