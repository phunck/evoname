import random
import json
import pickle
import os
import argparse
import datetime
import operator
import multiprocessing
from typing import List, Dict, Any, Tuple

# Rich & TQDM
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich import box
from tqdm import tqdm
import time

from deap import base, creator, tools, gp, algorithms

# Import our custom primitive set and types
from primitive_set import (
    NameObj, Token, TokenList, StringList, Gender, RegexToken,
    tokenize, make_name_obj,
    # Primitives
    if_bool_string, if_bool_tokenlist,
    trim, to_lower, split_on_comma,
    get_first_string, get_last_string,
    get_first_token, get_last_token,
    slice_tokens, len_tokens, drop_first, drop_last,
    remove_type, index_of_type, get_remainder_tokens,
    filter_by_type, count_type, get_gender_from_salutation, get_gender_from_name,
    # Feature Detectors
    has_comma, is_title, is_salutation, identity_token_type,
    extract_salutation_str, extract_title_list, extract_given_str, extract_family_str,
    extract_middle_str, extract_suffix_list, extract_particles_list,
    set_confidence
)

# --- 1. Setup & Configuration ---

def load_dataset(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_f1(pred: List[str] | str, truth: List[str] | str) -> float:
    """
    Calculates F1 score for strings or lists of strings.
    Case-insensitive comparison.
    """
    # Normalize inputs to sets of lowercase strings
    if isinstance(pred, str):
        pred_set = {pred.lower().strip()} if pred.strip() else set()
    else:
        pred_set = {p.lower().strip() for p in pred if p.strip()}
        
    if isinstance(truth, str):
        truth_set = {truth.lower().strip()} if truth.strip() else set()
    else:
        truth_set = {t.lower().strip() for t in truth if t.strip()}

    if not pred_set and not truth_set:
        return 1.0 # Both empty = Match
    
    tp = len(pred_set.intersection(truth_set))
    fp = len(pred_set - truth_set)
    fn = len(truth_set - pred_set)
    
    if tp == 0:
        return 0.0
        
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    
    return 2 * (precision * recall) / (precision + recall)

def gen_rand_int():
    return random.randint(0, 5)

def gen_rand_float():
    return round(random.random(), 2)

def evaluate_individual(individual, pset, data: List[Dict], weights: Dict[str, float] = None) -> Tuple[float]:
    func = gp.compile(individual, pset)
    
    # Default Weights (Balanced)
    if weights is None:
        weights = {
            "core_family": 0.4,
            "core_given": 0.4,
            "core_title": 0.1,
            "core_gender": 0.1,
            "bonus_exact": 0.1,
            "bonus_coverage": 0.1,
            "bonus_uncertainty": 0.1,
            "penalty_hallucination": 0.2,
            "penalty_vital": 0.1, # Light penalty
            "penalty_lazy": 0.5
        }
    
    # --- METRICS ACCUMULATORS ---
    # Core F1 Sums
    sum_f1_given = 0.0
    sum_f1_family = 0.0
    sum_f1_title = 0.0
    sum_f1_gender = 0.0
    
    # Bonus Counters
    count_exact_match = 0
    sum_coverage_score = 0.0
    sum_unknown_handling = 0.0
    
    # Penalty Counters
    sum_hallucination_rate = 0.0
    sum_vital_penalty = 0.0
    
    n = len(data)
    if n == 0: return 0.0,

    valid_gender_count = 0
    
    for entry in data:
        raw = entry["raw"]
        solution = entry["solution"]
        
        try:
            pred_obj: NameObj = func(raw)
        except Exception:
            return 0.0, # Runtime error is still death

        # --- 1. CORE SCORE CALCULATION ---
        f1_given = calculate_f1(pred_obj.given, solution["given"])
        f1_family = calculate_f1(pred_obj.family, solution["family"])
        f1_title = calculate_f1(pred_obj.title, solution["title"])
        
        # Gender
        truth_gender = solution.get("gender")
        f1_gender = 0.0
        if truth_gender and truth_gender != "null":
            valid_gender_count += 1
            pred_gender_val = pred_obj.gender.value if pred_obj.gender else "null"
            if pred_gender_val == truth_gender:
                f1_gender = 1.0
        else:
            pass

        sum_f1_given += f1_given
        sum_f1_family += f1_family
        sum_f1_title += f1_title
        sum_f1_gender += f1_gender

        # --- 2. BONUS SCORE CALCULATION ---
        
        # 2.1 Exact Match Bonus
        is_exact = True
        if f1_given < 1.0 or f1_family < 1.0 or f1_title < 1.0: is_exact = False
        if calculate_f1(pred_obj.middle, solution["middle"]) < 1.0: is_exact = False
        if calculate_f1(pred_obj.suffix, solution["suffix"]) < 1.0: is_exact = False
        if calculate_f1(pred_obj.particles, solution["particles"]) < 1.0: is_exact = False
        if calculate_f1(pred_obj.salutation, solution["salutation"]) < 1.0: is_exact = False
        
        p_gen = pred_obj.gender.value if pred_obj.gender else "null"
        t_gen = solution.get("gender", "null")
        if p_gen != t_gen: is_exact = False
        
        if is_exact:
            count_exact_match += 1
            
        # 2.2 Coverage Bonus (Optional Fields)
        opt_fields = ["middle", "suffix", "particles"]
        opt_correct = 0
        opt_total_present = 0
        
        for field in opt_fields:
            truth_val = solution.get(field)
            has_content = False
            if isinstance(truth_val, list) and truth_val: has_content = True
            elif isinstance(truth_val, str) and truth_val.strip(): has_content = True
            
            if has_content:
                opt_total_present += 1
                if calculate_f1(getattr(pred_obj, field), truth_val) == 1.0:
                    opt_correct += 1
        
        if opt_total_present > 0:
            sum_coverage_score += (opt_correct / opt_total_present)
        else:
            sum_coverage_score += 1.0

        # 2.3 Uncertainty Bonus
        unc_fields = ["salutation", "title", "middle", "suffix", "particles"]
        unc_correct = 0
        unc_total_empty = 0
        
        for field in unc_fields:
            truth_val = solution.get(field)
            is_empty = False
            if not truth_val: is_empty = True
            elif isinstance(truth_val, list) and not truth_val: is_empty = True
            elif isinstance(truth_val, str) and not truth_val.strip(): is_empty = True
            
            if is_empty:
                unc_total_empty += 1
                pred_val = getattr(pred_obj, field)
                pred_empty = False
                if not pred_val: pred_empty = True
                elif isinstance(pred_val, list) and not pred_val: pred_empty = True
                elif isinstance(pred_val, str) and not pred_val.strip(): pred_empty = True
                
                if pred_empty:
                    unc_correct += 1
        
        if unc_total_empty > 0:
            sum_unknown_handling += (unc_correct / unc_total_empty)
        else:
            sum_unknown_handling += 1.0

        # --- 3. PENALTY CALCULATION ---
        
        # 3.1 Hallucination Penalty
        hallucinations = 0
        total_fields = 0
        all_fields = ["given", "family", "salutation", "title", "middle", "suffix", "particles"]
        
        for field in all_fields:
            truth_val = solution.get(field)
            is_truth_empty = not truth_val or (isinstance(truth_val, list) and not truth_val)
            
            if is_truth_empty:
                total_fields += 1
                pred_val = getattr(pred_obj, field)
                is_pred_empty = not pred_val or (isinstance(pred_val, list) and not pred_val)
                
                if not is_pred_empty:
                    hallucinations += 1
        
        if total_fields > 0:
            sum_hallucination_rate += (hallucinations / total_fields)

        # 3.2 Vital Penalty (Family & Given)
        if solution.get("family"):
            p_fam = pred_obj.family
            if not p_fam or (isinstance(p_fam, str) and not p_fam.strip()):
                 sum_vital_penalty += weights.get("penalty_vital", 0.1)
        
        if solution.get("given"):
            p_giv = pred_obj.given
            if not p_giv or (isinstance(p_giv, str) and not p_giv.strip()):
                sum_vital_penalty += weights.get("penalty_vital", 0.1)

        # 3.3 Lazy Penalty
        if pred_obj.given and pred_obj.given.strip() == raw.strip():
             sum_vital_penalty += weights.get("penalty_lazy", 0.5)
             
        if pred_obj.family and pred_obj.family.strip() == raw.strip():
             sum_vital_penalty += weights.get("penalty_lazy", 0.5)

    # --- AGGREGATION ---
    
    # Averages
    avg_given = sum_f1_given / n
    avg_family = sum_f1_family / n
    avg_title = sum_f1_title / n
    avg_gender = sum_f1_gender / valid_gender_count if valid_gender_count > 0 else 1.0
    
    exact_rate = count_exact_match / n
    avg_coverage = sum_coverage_score / n
    avg_uncertainty = sum_unknown_handling / n
    avg_hallucination = sum_hallucination_rate / n
    avg_vital_penalty = sum_vital_penalty / n
    
    # Weighted Score Calculation
    core_score = (weights["core_family"] * avg_family) + \
                 (weights["core_given"] * avg_given) + \
                 (weights["core_title"] * avg_title) + \
                 (weights["core_gender"] * avg_gender)
    
    bonus_score = (weights["bonus_exact"] * exact_rate) + \
                  (weights["bonus_coverage"] * avg_coverage) + \
                  (weights["bonus_uncertainty"] * avg_uncertainty)
    
    penalty_score = (weights["penalty_hallucination"] * avg_hallucination) + avg_vital_penalty
    
    final_score = core_score + bonus_score - penalty_score
    
    return max(0.0, final_score),

def setup_gp():
    # Define Types
    # Input: str (raw name)
    # Output: NameObj
    
    pset = gp.PrimitiveSetTyped("MAIN", [str], NameObj)
    
    # Register Terminals (Regex Patterns are handled inside tokenize, but we need types)
    # Actually, we don't pass tokens as arguments to MAIN.
    # MAIN takes 'raw' string.
    # The first step in the tree usually is 'tokenize(raw)'.
    
    # Register Primitives
    # -- Control Flow --
    pset.addPrimitive(if_bool_string, [bool, str, str], str)
    pset.addPrimitive(if_bool_tokenlist, [bool, TokenList, TokenList], TokenList)
    
    # -- String/List Ops --
    pset.addPrimitive(trim, [str], str)
    pset.addPrimitive(to_lower, [str], str)
    pset.addPrimitive(split_on_comma, [str], StringList)
    pset.addPrimitive(get_first_string, [StringList], str)
    pset.addPrimitive(get_last_string, [StringList], str)
    
    pset.addPrimitive(get_first_token, [TokenList], Token) # Returns Optional[Token], handled as Token for now
    pset.addPrimitive(get_last_token, [TokenList], Token)
    pset.addPrimitive(slice_tokens, [TokenList, int, int], TokenList)
    pset.addPrimitive(len_tokens, [TokenList], int)
    pset.addPrimitive(drop_first, [TokenList], TokenList)
    pset.addPrimitive(drop_last, [TokenList], TokenList)
    pset.addPrimitive(remove_type, [TokenList, RegexToken], TokenList)
    pset.addPrimitive(index_of_type, [TokenList, RegexToken], int)
    pset.addPrimitive(get_remainder_tokens, [TokenList, TokenList], TokenList)
    
    # -- Token Muscles --
    pset.addPrimitive(tokenize, [str], TokenList) # Uses default locale for now, or we inject it?
    # Note: tokenize signature is (str, locale). We might need to curry it or fix locale.
    # For now, let's assume default locale or fix it in the primitive wrapper if needed.
    # But wait, tokenize is the entry point.
    
    pset.addPrimitive(filter_by_type, [TokenList, RegexToken], TokenList)
    pset.addPrimitive(count_type, [TokenList, RegexToken], int)
    pset.addPrimitive(get_gender_from_salutation, [Token], Gender)
    pset.addPrimitive(get_gender_from_name, [str], Gender)
    
    # -- Feature Detectors --
    pset.addPrimitive(has_comma, [str], bool)
    pset.addPrimitive(is_title, [Token], bool)
    pset.addPrimitive(is_salutation, [Token], bool)
    pset.addPrimitive(identity_token_type, [RegexToken], RegexToken)

    # -- Macro-Primitives (Boosters) --
    pset.addPrimitive(extract_salutation_str, [TokenList], str)
    pset.addPrimitive(extract_title_list, [TokenList], StringList)
    pset.addPrimitive(extract_given_str, [TokenList], str)
    pset.addPrimitive(extract_family_str, [TokenList], str)
    pset.addPrimitive(extract_middle_str, [TokenList], StringList)
    pset.addPrimitive(extract_suffix_list, [TokenList], StringList)
    pset.addPrimitive(extract_particles_list, [TokenList], StringList)
    
    # -- Object Builder --
    pset.addPrimitive(make_name_obj, 
                      [str, str, str, StringList, StringList, str, Gender, StringList, StringList], 
                      NameObj)
    pset.addPrimitive(set_confidence, [NameObj, float], NameObj)
    
    # -- Float Math --
    pset.addPrimitive(operator.add, [float, float], float)
    pset.addPrimitive(operator.sub, [float, float], float)
    pset.addPrimitive(operator.mul, [float, float], float)
    
    # -- Ephemeral Constants --
    # Integers for slicing
    pset.addEphemeralConstant("rand_int", gen_rand_int, int)
    # Floats for confidence
    pset.addEphemeralConstant("rand_float", gen_rand_float, float)
    
    # -- Enums as Terminals --
    # We need to register the Enum values so the tree can use them (e.g. RegexToken.SALUTATION)
    # DEAP handles this by adding them as terminals of their type.
    for token_type in RegexToken:
        pset.addTerminal(token_type, RegexToken, name=token_type.name)
        
    # Gender Enums? Usually output of function, but maybe input to builder.
    # But builder takes Gender type.
    # We can add Gender.UNKNOWN etc as terminals if needed, but usually they come from extraction.
    # Let's add them just in case fallback is needed.
    for g in Gender:
        pset.addTerminal(g, Gender, name=g.name)

    # Empty Lists/Strings for fallbacks
    pset.addTerminal("", str, name="EMPTY_STR")
    pset.addTerminal(StringList([]), StringList, name="EMPTY_STR_LIST")
    pset.addTerminal(TokenList([]), TokenList, name="EMPTY_TOK_LIST")
    
    # Fallback Objects
    pset.addTerminal(NameObj(""), NameObj, name="EMPTY_NAME_OBJ")
    pset.addTerminal(Token("", RegexToken.PUNCT, (0,0), -1), Token, name="EMPTY_TOKEN")
    
    # Booleans
    pset.addTerminal(True, bool, name="TRUE")
    pset.addTerminal(False, bool, name="FALSE")

    # Rename arguments for clarity
    pset.renameArguments(ARG0="raw_input")
    
    return pset

def setup_toolbox(pset):
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=6) # Increased depth slightly
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("compile", gp.compile, pset=pset)

    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("mate", gp.cxOnePoint)
    toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
    toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

    # Bloat control
    toolbox.decorate("mate", gp.staticLimit(key=operator.attrgetter("height"), max_value=17))
    toolbox.decorate("mutate", gp.staticLimit(key=operator.attrgetter("height"), max_value=17))

    return toolbox

# --- 3. Main Trainer ---

# --- Rich UI Helpers ---
def generate_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="stats", size=10),
        Layout(name="best", ratio=1)
    )
    return layout

def create_stats_table(logbook):
    table = Table(title="Generation Statistics", box=box.ROUNDED)
    table.add_column("Gen", justify="right", style="cyan", no_wrap=True)
    table.add_column("N-Evals", justify="right", style="magenta")
    table.add_column("Avg Fitness", justify="right", style="green")
    table.add_column("Std Dev", justify="right", style="yellow")
    table.add_column("Max Fitness", justify="right", style="bold green")
    
    # Show last 5 generations
    for record in logbook[-5:]:
        table.add_row(
            str(record['gen']),
            str(record['nevals']),
            f"{record['avg']:.4f}",
            f"{record['std']:.4f}",
            f"{record['max']:.4f}"
        )
    return table

def main():
    console = Console()
    parser = argparse.ArgumentParser(description="EvoName Trainer")
    parser.add_argument("--generations", type=int, default=50)
    parser.add_argument("--pop-size", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--data-dir", type=str, default="data")
    parser.add_argument("--checkpoint", type=str, help="Path to checkpoint to resume")
    parser.add_argument("--run-id", type=str, help="Custom Run ID")
    parser.add_argument("--monitor", action="store_true", help="Enable live monitoring (writes monitor.json)")
    parser.add_argument("--seed-model", type=str, help="Path to a champion.pkl to seed the population with")
    
    args = parser.parse_args()
    
    # Reproducibility
    random.seed(args.seed)
    
    # Paths
    run_id = args.run_id or datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir = os.path.join("runs", run_id)
    cp_dir = os.path.join(run_dir, "checkpoints")
    art_dir = os.path.join(run_dir, "artifacts")
    
    os.makedirs(cp_dir, exist_ok=True)
    os.makedirs(art_dir, exist_ok=True)
    
    # Load Data
    train_path = os.path.join(args.data_dir, "train.json")
    val_path = os.path.join(args.data_dir, "val.json")
    
    if not os.path.exists(train_path):
        print(f"Error: Training data not found at {train_path}")
        return
        
    train_data = load_dataset(train_path)
    val_data = load_dataset(val_path) if os.path.exists(val_path) else []
    
    print(f"Loaded {len(train_data)} training samples.")
    
    # Setup GP
    pset = setup_gp()
    toolbox = setup_toolbox(pset)
    
    # --- ISLAND CONFIGURATION ---
    # 1. Main Island (Balanced)
    weights_main = {
        "core_family": 0.4, "core_given": 0.4, "core_title": 0.1, "core_gender": 0.1,
        "bonus_exact": 0.1, "bonus_coverage": 0.1, "bonus_uncertainty": 0.1,
        "penalty_hallucination": 0.2, "penalty_vital": 0.1, "penalty_lazy": 0.5
    }
    
    # 2. Detail Island (Focus on Middle, Suffix, Particles)
    weights_detail = {
        "core_family": 0.1, "core_given": 0.1, "core_title": 0.0, "core_gender": 0.0,
        "bonus_exact": 0.0, "bonus_coverage": 0.8, # HUGE bonus for optional fields
        "bonus_uncertainty": 0.0,
        "penalty_hallucination": 0.0, "penalty_vital": 0.0, "penalty_lazy": 0.0
    }
    
    # 3. Structure Island (Focus on Title, Salutation)
    weights_structure = {
        "core_family": 0.1, "core_given": 0.1, "core_title": 0.4, "core_gender": 0.4,
        "bonus_exact": 0.0, "bonus_coverage": 0.0,
        "bonus_uncertainty": 0.5, # Reward correct handling of empty/non-empty structure
        "penalty_hallucination": 0.1, "penalty_vital": 0.0, "penalty_lazy": 0.0
    }
    
    # Register Evaluations
    toolbox.register("evaluate_main", evaluate_individual, pset=pset, data=train_data, weights=weights_main)
    toolbox.register("evaluate_detail", evaluate_individual, pset=pset, data=train_data, weights=weights_detail)
    toolbox.register("evaluate_structure", evaluate_individual, pset=pset, data=train_data, weights=weights_structure)
    
    # Initialize Islands
    print("Initializing Islands...")
    pop_main = toolbox.population(n=args.pop_size)
    pop_detail = toolbox.population(n=args.pop_size)
    pop_structure = toolbox.population(n=args.pop_size)
    
    islands = [pop_main, pop_detail, pop_structure]
    island_names = ["Main", "Detail", "Structure"]
    eval_funcs = [toolbox.evaluate_main, toolbox.evaluate_detail, toolbox.evaluate_structure]
    
    start_gen = 0
    hof = tools.HallOfFame(1)
    logbook = tools.Logbook()
    
    # Stats
    stats = tools.Statistics(lambda ind: ind.fitness.values[0])
    stats.register("avg", lambda x: sum(x)/len(x) if x else 0)
    stats.register("max", max)
    
    # GA Parameters
    CXPB, MUTPB = 0.5, 0.5
    
    best_fitness_so_far = 0.0
    
    # GA Parameters
    CXPB, MUTPB = 0.5, 0.5
    
    best_fitness_so_far = 0.0
    
    # Clean Header (No Blue Bar)
    print("\n" + "="*60)
    print(" 🧬 EvoName Island Model Training 🧬")
    print("="*60 + "\n")
    
    # Header
    # Gen | Main Island | Detail Island | Structure Island
    header = f"{'Gen':<4} | {'Main Island':<20} | {'Detail Island':<20} | {'Structure Island':<20}"
    console.print(f"[bold]{header}[/bold]")
    console.print("-" * 75)

    def draw_bar(val, max_val=1.2, width=10):
        # Draw a progress bar like: ██████░░░░
        filled = int((val / max_val) * width)
        filled = min(filled, width) # Clamp
        bar = "█" * filled + "░" * (width - filled)
        return f"{val:.4f} {bar}"

    # Evolution Loop
    for gen in range(start_gen, args.generations):
        
        # 1. Migration (Every 5 gens)
        if gen > 0 and gen % 5 == 0:
            migrants = tools.migRing(islands, k=5, selection=tools.selBest, replacement=tools.selRandom)
            console.print(f"[italic grey]  🔄 Migration: Best individuals swapped islands![/italic grey]")
        
        island_stats = []
        
        # 2. Evolve Each Island
        for i, island in enumerate(islands):
            # Select
            offspring = toolbox.select(island, len(island))
            offspring = list(map(toolbox.clone, offspring))
            
            # Mate & Mutate
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:
                if random.random() < MUTPB:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values
            
            # Evaluate
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            
            # Evaluate with specific function
            for ind in invalid_ind:
                fit = eval_funcs[i](ind)
                ind.fitness.values = fit
            
            # Replace
            island[:] = offspring
            
            # Record Stats for this island
            record = stats.compile(island)
            island_stats.append(record)
            
            # Update Global HoF (Only from Main Island)
            if i == 0:
                hof.update(island)

        # 3. Report
        main_max = island_stats[0]["max"]
        detail_max = island_stats[1]["max"]
        struct_max = island_stats[2]["max"]
        
        # Format with bars
        # Main: Green, Detail: Cyan, Structure: Magenta
        main_str = f"[green]{draw_bar(main_max)}[/green]"
        detail_str = f"[cyan]{draw_bar(detail_max)}[/cyan]"
        struct_str = f"[magenta]{draw_bar(struct_max)}[/magenta]"
        
        row = f"{gen+1:<4} | {main_str:<20} | {detail_str:<20} | {struct_str:<20}"
        console.print(row)
        
        # Save Champion (Main Island)
        best_ind = hof[0]
        if best_ind.fitness.values[0] > best_fitness_so_far:
            best_fitness_so_far = best_ind.fitness.values[0]
            with open("model/champion.pkl", "wb") as f:
                pickle.dump(best_ind, f)
            # console.print(f"[bold green]New Main Champion! 🏆[/bold green] Fitness: {best_fitness_so_far:.4f}")

    console.print("\n[bold green]Training Completed![/bold green]")
    best_ind = hof[0]
    console.print(f"Final Best Fitness: {best_ind.fitness.values[0]}")
    
    # Save Artifacts
    with open(os.path.join(art_dir, "champion.pkl"), "wb") as f:
        pickle.dump(best_ind, f)
    with open(os.path.join(art_dir, "champion.txt"), "w") as f:
        f.write(str(best_ind))
    
    model_dir = "model"
    os.makedirs(model_dir, exist_ok=True)
    with open(os.path.join(model_dir, "champion.pkl"), "wb") as f:
        pickle.dump(best_ind, f)
    with open(os.path.join(model_dir, "champion.txt"), "w") as f:
        f.write(str(best_ind))

    # Validation
    if val_data:
        print("\nRunning Validation...")
        func = gp.compile(best_ind, pset)
        # Validate using Main weights
        val_score, = evaluate_individual(best_ind, pset, val_data, weights=weights_main)
        print(f"Validation Score: {val_score}")

if __name__ == "__main__":
    main()
