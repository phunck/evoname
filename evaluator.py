import json
from typing import List, Dict, Tuple
from deap import gp
from primitive_set import NameObj
from post_processor import repair_name_object

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

def evaluate_individual(individual, pset, data: List[Dict], weights: Dict[str, float] = None, gates: Dict[str, float] = None) -> Tuple[float]:
    func = gp.compile(individual, pset)
    
    # Default Weights (Balanced)
    if weights is None:
        weights = {
            "core_family": 0.4, "core_given": 0.4, "core_title": 0.1, "core_gender": 0.1,
            "bonus_exact": 0.1, "bonus_coverage": 0.1, "bonus_uncertainty": 0.1,
            "penalty_hallucination": 0.2, "penalty_vital": 0.1, "penalty_lazy": 0.5
        }
    
    # Core F1 Sums
    sum_f1_given = 0.0
    sum_f1_family = 0.0
    sum_f1_title = 0.0
    sum_f1_suffix = 0.0
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
            pred_obj = func(raw)
            # Check if it's actually a NameObj (LLM might return StringList etc.)
            if not isinstance(pred_obj, NameObj):
                return 0.0,
                
            # --- POST-PROCESSING ---
            pred_obj = repair_name_object(pred_obj)
        except Exception:
            return 0.0, # Runtime error is still death

        # --- 1. CORE SCORE CALCULATION ---
        f1_given = calculate_f1(pred_obj.given, solution["given"])
        f1_family = calculate_f1(pred_obj.family, solution["family"])
        f1_title = calculate_f1(pred_obj.title, solution["title"])
        f1_suffix = calculate_f1(pred_obj.suffix, solution["suffix"])
        
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
        sum_f1_suffix += f1_suffix
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
    
    # --- GATE LOGIC (Soft Gates) ---
    if gates:
        min_fam = gates.get("min_family", 0.0)
        min_giv = gates.get("min_given", 0.0)
        max_pen = gates.get("max_penalty", 0.0)
        
        gap_fam = max(0.0, min_fam - avg_family)
        gap_giv = max(0.0, min_giv - avg_given)
        
        gap = max(gap_fam, gap_giv)
        if gap > 0:
            # Soft Gate: factor = 1.0 - (gap * max_pen)
            # Ensure we don't go below 0.1 (never kill completely)
            factor = max(0.1, 1.0 - (gap * max_pen))
            final_score *= factor
    
    # Allow negative fitness (important for curriculum learning)
    return final_score,

def explain_fitness(individual, pset, data: List[Dict], weights: Dict[str, float] = None, gates: Dict[str, float] = None, export_path: str = None):
    """
    Runs evaluation but prints detailed breakdown instead of returning score.
    Optionally exports stats to a JSON file.
    """
    func = gp.compile(individual, pset)
    
    # Default Weights (Balanced)
    if weights is None:
        weights = {
            "core_family": 0.4, "core_given": 0.4, "core_title": 0.1, "core_gender": 0.1,
            "bonus_exact": 0.1, "bonus_coverage": 0.1, "bonus_uncertainty": 0.1,
            "penalty_hallucination": 0.2, "penalty_vital": 0.1, "penalty_lazy": 0.5
        }
    
    # Core F1 Sums
    sum_f1_given = 0.0
    sum_f1_family = 0.0
    sum_f1_title = 0.0
    sum_f1_suffix = 0.0
    sum_f1_gender = 0.0
    
    # Bonus Counters
    count_exact_match = 0
    sum_coverage_score = 0.0
    sum_unknown_handling = 0.0
    
    # Penalty Counters
    sum_hallucination_rate = 0.0
    sum_vital_penalty = 0.0
    
    n = len(data)
    valid_gender_count = 0
    
    for entry in data:
        raw = entry["raw"]
        solution = entry["solution"]
        try:
            pred_obj: NameObj = func(raw)
            # --- POST-PROCESSING ---
            pred_obj = repair_name_object(pred_obj)
        except Exception:
            continue

        # --- 1. CORE SCORE CALCULATION ---
        f1_given = calculate_f1(pred_obj.given, solution["given"])
        f1_family = calculate_f1(pred_obj.family, solution["family"])
        f1_title = calculate_f1(pred_obj.title, solution["title"])
        f1_suffix = calculate_f1(pred_obj.suffix, solution["suffix"])
        
        # Gender
        truth_gender = solution.get("gender")
        f1_gender = 0.0
        if truth_gender and truth_gender != "null":
            valid_gender_count += 1
            pred_gender_val = pred_obj.gender.value if pred_obj.gender else "null"
            if pred_gender_val == truth_gender:
                f1_gender = 1.0

        sum_f1_given += f1_given
        sum_f1_family += f1_family
        sum_f1_title += f1_title
        sum_f1_suffix += f1_suffix
        sum_f1_gender += f1_gender

        # --- 2. BONUS SCORE CALCULATION ---
        is_exact = True
        if f1_given < 1.0 or f1_family < 1.0 or f1_title < 1.0: is_exact = False
        if calculate_f1(pred_obj.middle, solution["middle"]) < 1.0: is_exact = False
        if calculate_f1(pred_obj.suffix, solution["suffix"]) < 1.0: is_exact = False
        if calculate_f1(pred_obj.particles, solution["particles"]) < 1.0: is_exact = False
        if calculate_f1(pred_obj.salutation, solution["salutation"]) < 1.0: is_exact = False
        p_gen = pred_obj.gender.value if pred_obj.gender else "null"
        t_gen = solution.get("gender", "null")
        if p_gen != t_gen: is_exact = False
        
        if is_exact: count_exact_match += 1
            
        # Coverage
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
        if opt_total_present > 0: sum_coverage_score += (opt_correct / opt_total_present)
        else: sum_coverage_score += 1.0

        # Uncertainty
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
    avg_suffix = sum_f1_suffix / n
    avg_gender = sum_f1_gender / valid_gender_count if valid_gender_count > 0 else 1.0
    
    exact_rate = count_exact_match / n
    avg_coverage = sum_coverage_score / n
    avg_uncertainty = sum_unknown_handling / n
    avg_hallucination = sum_hallucination_rate / n
    avg_vital_penalty = sum_vital_penalty / n
    
    # Weighted Score Calculation
    # Weighted Score Calculation
    core_score = (weights["core_family"] * avg_family) + \
                 (weights["core_given"] * avg_given) + \
                 (weights["core_title"] * avg_title) + \
                 (weights.get("core_suffix", 0.0) * avg_suffix) + \
                 (weights["core_gender"] * avg_gender)
    
    bonus_score = (weights["bonus_exact"] * exact_rate) + \
                  (weights["bonus_coverage"] * avg_coverage) + \
                  (weights["bonus_uncertainty"] * avg_uncertainty)
    
    penalty_score = (weights["penalty_hallucination"] * avg_hallucination) + avg_vital_penalty
    
    final_score = core_score + bonus_score - penalty_score
    
    print("\n" + "-"*40)
    print(" 📊 FITNESS BREAKDOWN (Champion)")
    print("-"*40)
    print(f" CORE SCORE:    {core_score:.4f}")
    print(f"   - Family:    {avg_family:.4f} (w={weights['core_family']})")
    print(f"   - Given:     {avg_given:.4f} (w={weights['core_given']})")
    print(f"   - Title:     {avg_title:.4f} (w={weights['core_title']})")
    print(f"   - Suffix:    {avg_suffix:.4f} (w={weights.get('core_suffix', 0.0)})")
    print(f"   - Gender:    {avg_gender:.4f} (w={weights['core_gender']})")
    print(f" BONUS SCORE:   {bonus_score:.4f}")
    print(f"   - Exact:     {exact_rate:.4f} (w={weights['bonus_exact']})")
    print(f"   - Coverage:  {avg_coverage:.4f} (w={weights['bonus_coverage']})")
    print(f"   - Uncert.:   {avg_uncertainty:.4f} (w={weights['bonus_uncertainty']})")
    print(f" PENALTY SCORE: {penalty_score:.4f}")
    print(f"   - Halluc.:   {avg_hallucination:.4f} (w={weights['penalty_hallucination']})")
    print(f"   - Vital/Lazy:{avg_vital_penalty:.4f}")
    print("-"*40)
    
    if gates:
        min_fam = gates.get("min_family", 0.0)
        min_giv = gates.get("min_given", 0.0)
        max_pen = gates.get("max_penalty", 0.0)
        gap_fam = max(0.0, min_fam - avg_family)
        gap_giv = max(0.0, min_giv - avg_given)
        gap = max(gap_fam, gap_giv)
        if gap > 0:
            factor = max(0.1, 1.0 - (gap * max_pen))
            print(f" 🚪 GATE PENALTY APPLIED!")
            print(f"   - Gap: {gap:.4f} (Min Fam: {min_fam}, Min Giv: {min_giv})")
            print(f"   - Factor: {factor:.4f}")
            final_score *= factor
            
    print(f" 🏁 FINAL SCORE: {final_score:.4f}")
    print("-"*40 + "\n")

    if export_path:
        stats = {
            "family": avg_family,
            "given": avg_given,
            "title": avg_title,
            "suffix": avg_suffix,
            "gender": avg_gender,
            "exact": exact_rate,
            "coverage": avg_coverage,
            "uncertainty": avg_uncertainty,
            "hallucination": avg_hallucination,
            "vital_penalty": avg_vital_penalty,
            "final_score": final_score
        }
        try:
            with open(export_path, "w") as f:
                json.dump(stats, f, indent=4)
            print(f"✅ Stats exported to {export_path}")
        except Exception as e:
            print(f"❌ Failed to export stats: {e}")
