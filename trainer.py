import random
import json
import pickle
import os
import argparse
import datetime
import operator
import multiprocessing
from typing import List, Dict, Any, Tuple

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
    filter_by_type, count_type, get_gender_from_salutation,
    has_comma, is_title, is_salutation, identity_token_type,
    extract_salutation_str, extract_title_list, extract_given_str, extract_family_str,
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

def evaluate_individual(individual, pset, data: List[Dict]) -> Tuple[float]:
    # Compile the tree into a function
    func = gp.compile(individual, pset)
    
    f1_given_sum = 0.0
    f1_family_sum = 0.0
    f1_title_sum = 0.0
    f1_gender_sum = 0.0
    
    valid_gender_count = 0
    
    for entry in data:
        raw = entry["raw"]
        solution = entry["solution"]
        
        try:
            # Execute the generated function
            # Note: The primitive set expects 'raw' string as input
            # But wait, our primitives need to start somewhere.
            # The tree input is defined in pset.
            # We need to pass the raw string to the function.
            pred_obj: NameObj = func(raw)
        except Exception:
            # If execution fails (e.g. index out of bounds), return penalty
            return 0.0,

        # Hard Constraint: Family name must not be empty (unless truth is empty, which is rare)
        if not pred_obj.family and solution["family"]:
             return 0.0,

        # Calculate Metrics
        f1_given_sum += calculate_f1(pred_obj.given, solution["given"])
        f1_family_sum += calculate_f1(pred_obj.family, solution["family"])
        f1_title_sum += calculate_f1(pred_obj.title, solution["title"])
        
        # Gender Metric (only if truth has gender)
        truth_gender = solution.get("gender")
        if truth_gender and truth_gender != "null":
            valid_gender_count += 1
            # Simple match for now
            pred_gender_val = pred_obj.gender.value if pred_obj.gender else "null"
            if pred_gender_val == truth_gender:
                f1_gender_sum += 1.0
    
    n = len(data)
    if n == 0: return 0.0,
    
    avg_given = f1_given_sum / n
    avg_family = f1_family_sum / n
    avg_title = f1_title_sum / n
    avg_gender = f1_gender_sum / valid_gender_count if valid_gender_count > 0 else 1.0
    
    # Weighted Score
    # Weights: Given 0.4, Family 0.4, Title 0.1, Gender 0.1
    score = (0.4 * avg_given) + (0.4 * avg_family) + (0.1 * avg_title) + (0.1 * avg_gender)
    
    # Parsimony Pressure (Penalty for tree size)
    # Small penalty to encourage smaller trees
    penalty = 0.001 * len(individual)
    
    final_fitness = max(0.0, score - penalty)
    
    return final_fitness,

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

def main():
    parser = argparse.ArgumentParser(description="EvoName Trainer")
    parser.add_argument("--generations", type=int, default=50)
    parser.add_argument("--pop-size", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--data-dir", type=str, default="data")
    parser.add_argument("--checkpoint", type=str, help="Path to checkpoint to resume")
    parser.add_argument("--run-id", type=str, help="Custom Run ID")
    parser.add_argument("--monitor", action="store_true", help="Enable live monitoring (writes monitor.json)")
    
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
    
    # Register Evaluate with data
    toolbox.register("evaluate", evaluate_individual, pset=pset, data=train_data)
    
    # Initialization
    if args.checkpoint:
        print(f"Resuming from {args.checkpoint}...")
        with open(args.checkpoint, "rb") as f:
            cp = pickle.load(f)
        pop = cp["population"]
        start_gen = cp["generation"] + 1
        hof = cp["halloffame"]
        logbook = cp["logbook"]
        random.setstate(cp["rndstate"])
    else:
        print("Initializing new population...")
        pop = toolbox.population(n=args.pop_size)
        start_gen = 0
        hof = tools.HallOfFame(1)
        logbook = tools.Logbook()
        logbook.header = ['gen', 'nevals'] + (tools.Statistics(lambda ind: ind.fitness.values).fields if False else ['avg', 'std', 'min', 'max'])

    # Stats
    stats = tools.Statistics(lambda ind: ind.fitness.values[0])
    stats.register("avg", lambda x: sum(x)/len(x) if x else 0)
    stats.register("std", lambda x: 0) # Simplify for now
    stats.register("min", min)
    stats.register("max", max)
    
    # Monitor Setup
    monitor_samples = []
    if args.monitor:
        # Select 5 random samples for consistent tracking
        monitor_samples = random.sample(train_data, min(5, len(train_data)))
        print(f"Monitoring enabled. Tracking {len(monitor_samples)} samples.")

    # Evolution Loop
    print(f"Starting evolution for {args.generations} generations...")
    
    for gen in range(start_gen, args.generations):
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))

        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < 0.5: # CXPB
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:
            if random.random() < 0.2: # MUTPB
                toolbox.mutate(mutant)
                del mutant.fitness.values

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # The population is entirely replaced by the offspring
        pop[:] = offspring
        
        # Update HallOfFame
        hof.update(pop)

        # Record statistics
        record = stats.compile(pop)
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)
        print(logbook.stream)
        
        # Monitor Update
        if args.monitor:
            try:
                best_ind = hof[0]
                func = gp.compile(best_ind, pset)
                
                sample_results = []
                for sample in monitor_samples:
                    try:
                        pred = func(sample["raw"])
                        # Convert NameObj to simple dict for JSON
                        pred_json = pred.to_json() if hasattr(pred, "to_json") else str(pred)
                    except Exception as e:
                        pred_json = {"error": str(e)}
                        
                    sample_results.append({
                        "raw": sample["raw"],
                        "truth": sample["solution"],
                        "pred": pred_json
                    })
                
                monitor_data = {
                    "generation": gen,
                    "best_fitness": best_ind.fitness.values[0],
                    "avg_fitness": record["avg"],
                    "samples": sample_results
                }
                
                with open("monitor.json", "w", encoding="utf-8") as f:
                    json.dump(monitor_data, f, indent=2)
            except Exception as e:
                print(f"Monitor Error: {e}")
        
        # Checkpointing (every 10 gens or last)
        if gen % 10 == 0 or gen == args.generations - 1:
            cp_path = os.path.join(cp_dir, f"gen_{gen:03d}.pkl")
            with open(cp_path, "wb") as f:
                pickle.dump(dict(population=pop, generation=gen, halloffame=hof, logbook=logbook, rndstate=random.getstate()), f)
    
    # Final Report
    best_ind = hof[0]
    print("\nBest Individual found:")
    print(best_ind)
    print(f"Fitness: {best_ind.fitness.values[0]}")
    
    # Save Artifacts
    with open(os.path.join(art_dir, "champion.pkl"), "wb") as f:
        pickle.dump(best_ind, f)
        
    with open(os.path.join(art_dir, "champion.txt"), "w") as f:
        f.write(str(best_ind))

    # Validation
    if val_data:
        print("\nRunning Validation...")
        # We need to re-compile and run on val data manually to get details
        func = gp.compile(best_ind, pset)
        # Reuse evaluate logic but maybe print details?
        # For now just score
        val_score, = evaluate_individual(best_ind, pset, val_data)
        print(f"Validation Score: {val_score}")

if __name__ == "__main__":
    main()
