import random
import pickle
import os
import datetime
import operator
import multiprocessing
from typing import List, Dict, Any, Tuple

from rich.console import Console
from tqdm import tqdm

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

class Trainer:
    def __init__(self, args, train_data, val_data):
        self.args = args
        self.train_data = train_data
        self.val_data = val_data
        
        self.console = Console()
        self.pset = create_pset()
        self.toolbox = self.setup_toolbox()
        
        self.tracker = DifficultyTracker()
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
            self.pool = multiprocessing.Pool(processes=self.args.jobs)

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
        
        for gen in range(start_gen, self.args.generations):
            
            # --- CURRICULUM UPDATE (Main Island) ---
            cur_weights_main = get_main_weights(gen)
            cur_gates_main = get_main_gates(gen)
            self.toolbox.register("evaluate_main", evaluate_individual, pset=self.pset, data=self.train_data, weights=cur_weights_main, gates=cur_gates_main)
            
            phase = "Strict"
            if gen <= 20: phase = "Bootstrap"
            elif gen <= 70: phase = "Ramp"
            
            # 1. Migration
            mig_occurred = []
            for i in range(len(self.islands)):
                source_idx = i
                dest_idx = (i - 1) % len(self.islands)
                rate = swap_rates[source_idx]
                
                if gen > 0 and gen % rate == 0:
                    k = 5
                    migrants = tools.selBest(self.islands[source_idx], k)
                    migrants = [self.toolbox.clone(ind) for ind in migrants]
                    
                    for migrant in migrants:
                        indexed_pop = list(enumerate(self.islands[dest_idx]))
                        sorted_indexed = sorted(indexed_pop, key=lambda x: x[1].fitness.values[0] if x[1].fitness.valid else -999.0)
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
                    if random.random() < self.mutpb:
                        self.toolbox.mutate(mutant)
                        del mutant.fitness.values
                
                invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
                
                if i == 0: eval_func = self.toolbox.evaluate_main
                elif i == 1: eval_func = self.toolbox.evaluate_detail
                else: eval_func = self.toolbox.evaluate_structure
                
                if len(invalid_ind) > 0:
                    iterator = tqdm(invalid_ind, desc=f"Eval {self.island_names[i]}", leave=False) if len(invalid_ind) > 10 else invalid_ind
                    
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

            if self.args.info:
                explain_fitness(self.hof[0], self.pset, self.train_data, weights=cur_weights_main, gates=cur_gates_main)

        self.console.print("\n[bold green]Training Completed![/bold green]")
        best_ind = self.hof[0]
        self.console.print(f"Final Best Fitness: {best_ind.fitness.values[0]}")
        
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
