import json
import random
import pickle
import os
import datetime
import operator
import multiprocessing
import signal
import sys
import urllib.request
import time
from typing import List, Dict, Any, Tuple

from rich.console import Console


from deap import base, creator, tools, gp

# Import custom modules
from primitive_set import create_pset
from difficulty_tracker import DifficultyTracker
from usage_stats import PrimitiveUsageTracker
from evaluator import evaluate_individual, explain_fitness
from config import (
    get_main_weights, get_main_gates,
    weights_main_strict, weights_detail, weights_structure,
    GATES_DETAIL, GATES_STRUCTURE,
    DEFAULT_CXPB, DEFAULT_MUTPB, BLOAT_LIMIT
)
from ui import draw_bar, print_header

def init_worker():
    """Initializer for pool workers to ignore SIGINT."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def query_ollama(prompt, model="qwen2.5-coder:1.5b"):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", "")
    except Exception as e:
        # print(f"❌ Error connecting to Ollama: {e}")
        return None

class Trainer:
    def __init__(self, args, train_data, val_data):
        self.args = args
        self.train_data = train_data
        self.val_data = val_data
        
        self.console = Console()
        self.pset = create_pset()
        self.toolbox = self.setup_toolbox()
        
        self.tracker = DifficultyTracker()
        self.tracker.load() # Load existing difficulty data
        self.usage_tracker = PrimitiveUsageTracker(self.pset)
        
        self.hof = tools.HallOfFame(1)
        self.logbook = tools.Logbook()
        
        self.stats = tools.Statistics(lambda ind: ind.fitness.values[0])
        self.stats.register("avg", lambda x: sum(x)/len(x) if x else 0)
        self.stats.register("max", max)
        
        self.best_fitness_so_far = 0.0
        self.stagnation_counter = 0
        self.mutpb = DEFAULT_MUTPB

        # Paths
        self.run_id = args.run_id or datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.run_dir = os.path.join("runs", self.run_id)
        self.cp_dir = os.path.join(self.run_dir, "checkpoints")
        self.art_dir = os.path.join(self.run_dir, "artifacts")
        self.model_dir = "model"
        
        os.makedirs(self.cp_dir, exist_ok=True)
        os.makedirs(self.art_dir, exist_ok=True)
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Multiprocessing Pool
        self.pool = None
        if self.args.jobs > 1:
            self.console.print(f"[bold yellow]Initializing Multiprocessing Pool with {self.args.jobs} processes...[/bold yellow]")
            self.pool = multiprocessing.Pool(processes=self.args.jobs, initializer=init_worker)

    def __del__(self):
        if self.pool:
            self.pool.close()
            self.pool.join()

    def setup_toolbox(self):
        if not hasattr(creator, "FitnessMax"):
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        if not hasattr(creator, "Individual"):
            creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        toolbox.register("expr", gp.genHalfAndHalf, pset=self.pset, min_=1, max_=6)
        toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("compile", gp.compile, pset=self.pset)

        toolbox.register("select", tools.selTournament, tournsize=3)
        toolbox.register("mate", gp.cxOnePoint)
        toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
        toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=self.pset)

        # Bloat control
        toolbox.decorate("mate", gp.staticLimit(key=operator.attrgetter("height"), max_value=BLOAT_LIMIT))
        toolbox.decorate("mutate", gp.staticLimit(key=operator.attrgetter("height"), max_value=BLOAT_LIMIT))

        return toolbox

    def mutate_llm(self, individual):
        """
        Uses an LLM to try and repair/improve an individual based on a failure case.
        """
        # 1. Get a failure case from Hall of Shame
        shame_list = self.tracker.get_hall_of_shame(10)
        if not shame_list:
            return individual, False
            
        target_name, _ = random.choice(shame_list)
        
        # 2. Convert individual to code
        code_str = str(individual)
        
        # 3. Construct Prompt
        prompt = f"""
You are an expert in Genetic Programming and Python.
The following expression is supposed to parse the name "{target_name}" into a structured object (NameObj), but it fails or produces a suboptimal result.

Current Expression:
{code_str}

Available Primitives:
- String Ops: trim, to_lower, split_on_comma, get_first_string, get_last_string
- Token Ops: tokenize, filter_by_type, count_type, get_first_token, get_last_token, slice_tokens, remove_type, index_of_type, get_remainder_tokens
- Feature Detectors: has_comma, is_title, is_salutation, is_all_caps, is_capitalized, is_short, is_common_given_name, is_common_family_name
- Boosters: extract_salutation_str, extract_title_list, extract_given_str, extract_family_str, extract_middle_str, extract_suffix_list, extract_particles_list
- Object Builder: make_name_obj(raw, salutation, title_list, given, family, middle_list, gender, suffix_list, particles_list)

Task:
Modify the expression to better handle the name "{target_name}".
Keep the logic concise.
Return ONLY the new expression string. Do not use markdown code blocks.
"""

        # 4. Query LLM
        response = query_ollama(prompt)
        if not response:
            return individual, False
            
        # Clean response (remove markdown if present)
        cleaned_code = response.strip().replace("```python", "").replace("```", "").strip()
        
        # 5. Try to compile back to DEAP Individual
        try:
            # We need to use gp.PrimitiveTree.from_string but it requires a primitive set context
            # DEAP's from_string is a bit tricky, it expects a list of primitives.
            # A safer way is to use the compiler to check syntax, but to get a Tree object we need to parse it.
            
            new_ind = gp.PrimitiveTree.from_string(cleaned_code, self.pset)
            new_ind.fitness = self.toolbox.clone(individual.fitness) # Copy fitness type
            del new_ind.fitness.values # Invalidate fitness
            return new_ind, True
            
        except Exception as e:
            # print(f"⚠️ LLM produced invalid code: {e}")
            return individual, False

    def initialize_islands(self):
        print("Initializing Islands...")
        
        pop_main = None
        pop_detail = None
        pop_structure = None
        
        if self.args.resume:
            print("Attempting to resume from saved islands...")
            try:
                with open("model/island_main.pkl", "rb") as f: pop_main = pickle.load(f)
                with open("model/island_detail.pkl", "rb") as f: pop_detail = pickle.load(f)
                with open("model/island_structure.pkl", "rb") as f: pop_structure = pickle.load(f)
                print("Successfully loaded all 3 islands!")
            except FileNotFoundError:
                print("Warning: Could not find one or more island files. Starting fresh.")
                pop_main = None
        
        if pop_main is None:
            pop_main = self.toolbox.population(n=self.args.pop_size)
            pop_detail = self.toolbox.population(n=self.args.pop_size)
            pop_structure = self.toolbox.population(n=self.args.pop_size)
        
        self.islands = [pop_main, pop_detail, pop_structure]
        self.island_names = ["Main", "Detail", "Structure"]
        
        # Register fixed evaluators
        self.toolbox.register("evaluate_detail", evaluate_individual, pset=self.pset, data=self.train_data, weights=weights_detail, gates=GATES_DETAIL)
        self.toolbox.register("evaluate_structure", evaluate_individual, pset=self.pset, data=self.train_data, weights=weights_structure, gates=GATES_STRUCTURE)

    def train(self):
        self.initialize_islands()
        print_header(self.console)
        
        # Graceful Shutdown Handler
        self.stop_requested = False
        original_sigint_handler = signal.getsignal(signal.SIGINT)
        
        def signal_handler(sig, frame):
            self.console.print("\n[bold yellow]🛑 Stop requested! Finishing current generation...[/bold yellow]")
            self.stop_requested = True
            
        signal.signal(signal.SIGINT, signal_handler)
        
        # Parse Swap Rates
        try:
            if "," in self.args.swap:
                swap_rates = [int(x.strip()) for x in self.args.swap.split(",")]
            else:
                val = int(self.args.swap)
                swap_rates = [val, val, val]
        except ValueError:
            print("Error: --swap must be an integer or comma-separated integers.")
            return

        if len(swap_rates) < 3:
            swap_rates.extend([swap_rates[-1]] * (3 - len(swap_rates)))
            
        start_gen = 0
        if self.args.resume and os.path.exists("model/state.json"):
            try:
                with open("model/state.json", "r") as f:
                    state = json.load(f)
                    start_gen = state.get("gen", 0)
                self.console.print(f"[bold blue]Resuming from Generation {start_gen}[/bold blue]")
            except Exception as e:
                self.console.print(f"[bold red]Warning: Could not load state.json: {e}[/bold red]")
        
        try:
            # Run for specified number of generations *from current point*
            end_gen = start_gen + self.args.generations
            current_gen = start_gen
            
            for gen in range(start_gen, end_gen):
                if self.stop_requested:
                    break
            
                # --- CURRICULUM UPDATE (Main Island) ---
                cur_weights_main = get_main_weights(gen)
                cur_gates_main = get_main_gates(gen)
                self.toolbox.register("evaluate_main", evaluate_individual, pset=self.pset, data=self.train_data, weights=cur_weights_main, gates=cur_gates_main)
                
                phase = "Strict"
                if gen <= 20: phase = "Bootstrap"
                elif gen <= 70: phase = "Ramp"
                
                # 1. Migration (Hub-and-Spoke)
                mig_occurred = []
                
                # Define routes: (Source Index, Destination Index)
                # 0=Main, 1=Detail, 2=Structure
                # Hub-and-Spoke: Satellites <-> Hub
                routes = [
                    (1, 0), # Detail -> Main
                    (2, 0), # Structure -> Main
                    (0, 1), # Main -> Detail
                    (0, 2)  # Main -> Structure
                ]

                for source_idx, dest_idx in routes:
                    rate = swap_rates[source_idx]
                    
                    if gen > 0 and gen % rate == 0:
                        k = 5
                        migrants = tools.selBest(self.islands[source_idx], k)
                        migrants = [self.toolbox.clone(ind) for ind in migrants]
                        
                        for migrant in migrants:
                            # Tournament selection for replacement (crowding)
                            indexed_pop = list(enumerate(self.islands[dest_idx]))
                            # Sort by fitness (worst first for replacement candidates?)
                            # Actually we want to replace bad ones.
                            # The original code sorted by fitness.
                            sorted_indexed = sorted(indexed_pop, key=lambda x: x[1].fitness.values[0] if x[1].fitness.valid else -999.0)
                            
                            # Select from the lower half (worst individuals)
                            cutoff = max(1, len(sorted_indexed) // 2)
                            candidates = sorted_indexed[:cutoff]
                            
                            victim_entry = random.choice(candidates)
                            victim_idx = victim_entry[0]
                            
                            self.islands[dest_idx][victim_idx] = migrant
                            del self.islands[dest_idx][victim_idx].fitness.values
                        
                        mig_occurred.append(f"{self.island_names[source_idx]}->{self.island_names[dest_idx]}")
    
                if mig_occurred:
                    self.console.print(f"[italic grey]  🔄 Swap: {', '.join(mig_occurred)}[/italic grey]")
                
                island_stats = []
                
                # 2. Evolve Each Island
                for i, island in enumerate(self.islands):
                    offspring = self.toolbox.select(island, len(island))
                    offspring = list(map(self.toolbox.clone, offspring))
                    
                    for child1, child2 in zip(offspring[::2], offspring[1::2]):
                        if random.random() < DEFAULT_CXPB:
                            self.toolbox.mate(child1, child2)
                            del child1.fitness.values
                            del child2.fitness.values
    
                    for mutant in offspring:
                        # LLM Mutation (Experimental) - 5% chance, only on Main Island
                        if i == 0 and random.random() < 0.05:
                            new_ind, success = self.mutate_llm(mutant)
                            if success:
                                # Replace mutant with new_ind (trick: copy content)
                                mutant[:] = new_ind
                                mutant.fitness = new_ind.fitness
                                del mutant.fitness.values
                                # print("🤖 LLM Mutation triggered!")
                                continue

                        if random.random() < self.mutpb:
                            self.toolbox.mutate(mutant)
                            del mutant.fitness.values
                    
                    invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
                    
                    if i == 0: eval_func = self.toolbox.evaluate_main
                    elif i == 1: eval_func = self.toolbox.evaluate_detail
                    else: eval_func = self.toolbox.evaluate_structure
                    
                    if len(invalid_ind) > 0:
                        iterator = invalid_ind
                        
                        # Parallel Evaluation
                        if self.pool:
                            fitnesses = self.pool.map(eval_func, invalid_ind)
                        else:
                            fitnesses = map(eval_func, iterator)
                            
                        for ind, fit in zip(invalid_ind, fitnesses):
                            ind.fitness.values = fit
                    
                    island[:] = offspring
                    
                    record = self.stats.compile(island)
                    self.logbook.record(gen=gen, island=i, **record)
                    
                    fits = [ind.fitness.values[0] for ind in island]
                    mean = sum(fits) / len(fits)
                    variance = sum([((x - mean) ** 2) for x in fits]) / len(fits)
                    std_dev = variance ** 0.5
                    
                    island_stats.append((record['max'], std_dev))
                    
                    # Update Global HoF (Main Island)
                    if i == 0:
                        self.hof.update(island)
                        
                        if gen % 5 == 0:
                            self.tracker.update(island, self.train_data, self.pset)
                            self.tracker.save() # Persist Hall of Shame
                            
                            # Save State
                            with open("model/state.json", "w") as f:
                                json.dump({"gen": gen + 1}, f)
                        if gen % 10 == 0:
                            self.usage_tracker.update(island)
                        
                        current_best = record['max']
                        if current_best > self.best_fitness_so_far + 0.0001:
                            self.best_fitness_so_far = current_best
                            self.stagnation_counter = 0
                            if self.mutpb > DEFAULT_MUTPB:
                                self.mutpb = DEFAULT_MUTPB
                                self.console.print("[bold green]  🚀 Breakthrough! Mutation reset.[/bold green]")
                        else:
                            self.stagnation_counter += 1
                            
                        if self.stagnation_counter >= 10 and self.mutpb < 0.8:
                            self.mutpb = min(0.8, self.mutpb + 0.1)
                            self.stagnation_counter = 0
                            self.console.print(f"[bold red]  🌋 Cataclysm! Stagnation detected. Boosting Mutation to {self.mutpb:.1f}[/bold red]")
    
                # 3. Report
                row = f"{gen+1:<4} | "
                for max_val, std_val in island_stats:
                    bar = draw_bar(max_val)
                    color = "green" if max_val > 0 else "red"
                    row += f"[{color}]{max_val:6.4f}[/{color}] (σ{std_val:4.2f}) {bar} | "
                row += f"[cyan]{phase}[/cyan]"
                self.console.print(row)
                
                # Save Champion
                best_ind = self.hof[0]
                if best_ind.fitness.values[0] >= self.best_fitness_so_far: # Use >= to ensure save
                     with open("model/champion.pkl", "wb") as f:
                        pickle.dump(best_ind, f)
    
                current_gen = gen + 1
            
            # Always export stats for adaptive weighting (at end of cycle)
            if len(self.hof) > 0:
                explain_fitness(self.hof[0], self.pset, self.train_data, weights=cur_weights_main, gates=cur_gates_main, export_path="cycle_stats.json")
                
                # --- DIVERSITY CHECK ---
                # Calculate Phenotypic Diversity (Unique outputs on validation set)
                print("Calculating Diversity...")
                check_data = self.val_data if self.val_data else self.train_data[:100]
                unique_outputs = set()
                
                # Check top 50 individuals from Main Island (or HoF)
                # Using Main Island population gives better sense of population health than just HoF
                sample_pop = self.islands[0][:50] 
                
                for ind in sample_pop:
                    try:
                        func = gp.compile(ind, self.pset)
                        # Hash the outputs for a few examples
                        outputs = []
                        for entry in check_data[:5]: # Check first 5 examples
                            res = func(entry["raw"])
                            # Simple string representation for uniqueness
                            outputs.append(str(res))
                        unique_outputs.add(tuple(outputs))
                    except:
                        pass
                
                diversity_score = len(unique_outputs) / len(sample_pop) if len(sample_pop) > 0 else 0.0
                print(f"🧬 Phenotypic Diversity: {diversity_score:.2f}")
                
                with open("diversity_stats.json", "w") as f:
                    json.dump({"diversity": diversity_score}, f)

            # Save Final State

            # Save Final State
            with open("model/state.json", "w") as f:
                json.dump({"gen": current_gen}, f)

        except KeyboardInterrupt:
            self.console.print("\n[bold red]🛑 Training Interrupted by User![/bold red]")
            self.console.print("[yellow]Saving current progress before exiting...[/yellow]")
        
        finally:
            # Cleanup Pool
            if self.pool:
                self.pool.terminate()
                self.pool.join()
            
            # Restore signal handler
            signal.signal(signal.SIGINT, original_sigint_handler)

            self.console.print("\n[bold green]Training Completed/Stopped![/bold green]")
            if len(self.hof) > 0:
                best_ind = self.hof[0]
                self.console.print(f"Final Best Fitness: {best_ind.fitness.values[0]}")
                self.console.print(f"\n[bold green]🏆 HALL OF FAME (Champion) 🏆[/bold green]")
                self.console.print(f"{best_ind}\n")
                
                # Save Artifacts
                with open(os.path.join(self.art_dir, "champion.pkl"), "wb") as f: pickle.dump(best_ind, f)
                with open(os.path.join(self.art_dir, "champion.txt"), "w") as f: f.write(str(best_ind))
                
                with open(os.path.join(self.model_dir, "champion.pkl"), "wb") as f: pickle.dump(best_ind, f)
                with open(os.path.join(self.model_dir, "champion.txt"), "w") as f: f.write(str(best_ind))

                print("Saving Island Populations...")
                with open(os.path.join(self.model_dir, "island_main.pkl"), "wb") as f: pickle.dump(self.islands[0], f)
                with open(os.path.join(self.model_dir, "island_detail.pkl"), "wb") as f: pickle.dump(self.islands[1], f)
                with open(os.path.join(self.model_dir, "island_structure.pkl"), "wb") as f: pickle.dump(self.islands[2], f)

                # Validation
                if self.val_data:
                    print("\nRunning Validation...")
                    val_score, = evaluate_individual(best_ind, self.pset, self.val_data, weights=weights_main_strict)
                    print(f"Validation Score: {val_score}")
                    
                # Hall of Shame
                print("\n" + "="*60)
                print(" 🏆 HALL OF SHAME (Top 20 Hardest Examples) 🏆")
                print("="*60)
                shame_list = self.tracker.get_hall_of_shame(20)
                if not shame_list:
                    print("No failures recorded.")
                else:
                    print(f"{'Count':<6} | {'Example'}")
                    print("-" * 60)
                    for raw_name, count in shame_list:
                        print(f"{count:<6} | {raw_name}")
                print("="*60 + "\n")
                
                # Usage Stats
                print("\n" + "="*60)
                print(self.usage_tracker.get_stats())
                print("="*60 + "\n")
            else:
                print("No individuals in Hall of Fame.")
