import subprocess
import sys
import time
import argparse

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
    
    args = parser.parse_args()
    
    print("==================================================")
    print(" 🧬 EvoName Active Learning Loop")
    print("==================================================")
    print(f"Cycles: {args.cycles}")
    print(f"Gens/Cycle: {args.gens_per_cycle}")
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
            
            cmd = f"python trainer.py --generations {args.gens_per_cycle} --pop-size {args.pop_size} --resume --jobs {args.jobs}"
            run_command(cmd)
            
            print(f"✅ Cycle {i+1} completed.")
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Active Learning Loop Interrupted by User.")
        print("Exiting gracefully...")
        sys.exit(0)

if __name__ == "__main__":
    main()
