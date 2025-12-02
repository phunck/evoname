import pickle
import json
import argparse
from deap import gp, creator, base
from primitive_set import *
import primitive_set

import operator

# Recreate types
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

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
    
    # -- New Context Primitives --
    pset.addPrimitive(get_tokens_before_comma, [TokenList], TokenList)
    pset.addPrimitive(get_tokens_after_comma, [TokenList], TokenList)
    pset.addPrimitive(is_all_caps, [Token], bool)
    pset.addPrimitive(is_capitalized, [Token], bool)
    pset.addPrimitive(is_short, [Token], bool)
    pset.addPrimitive(is_common_given_name, [Token], bool)
    pset.addPrimitive(is_common_family_name, [Token], bool)

    # -- Statistical & Feature Primitives --
    pset.addPrimitive(token_length, [Token], int)
    pset.addPrimitive(is_initial, [Token], bool)
    pset.addPrimitive(has_hyphen, [Token], bool)
    pset.addPrimitive(has_period, [Token], bool)
    pset.addPrimitive(is_roman_numeral, [Token], bool)
    pset.addPrimitive(is_particle, [Token], bool)
    pset.addPrimitive(is_suffix, [Token], bool)
    
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
                      [str, str, StringList, str, str, StringList, Gender, StringList, StringList], 
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

def calculate_entry_f1(pred: NameObj, truth: Dict) -> float:
    """Calculates F1 score for a single entry across all fields."""
    # Fields to compare
    fields = ["given", "family", "salutation"]
    # List fields
    list_fields = ["title", "middle", "suffix", "particles"]
    
    total_f1 = 0.0
    count = 0
    
    # 1. String Fields
    for field in fields:
        p_val = getattr(pred, field, "").strip().lower()
        t_val = truth.get(field, "").strip().lower()
        
        if not p_val and not t_val:
            score = 1.0 # Both empty = match
        elif p_val == t_val:
            score = 1.0
        else:
            score = 0.0
        
        total_f1 += score
        count += 1
        
    # 2. List Fields
    for field in list_fields:
        p_list = [x.lower() for x in getattr(pred, field, [])]
        t_list = [x.lower() for x in truth.get(field, [])]
        
        # Simple set comparison for lists (ignoring order)
        p_set = set(p_list)
        t_set = set(t_list)
        
        if not p_set and not t_set:
            score = 1.0
        else:
            tp = len(p_set & t_set)
            fp = len(p_set - t_set)
            fn = len(t_set - p_set)
            
            if tp == 0:
                score = 0.0
            else:
                precision = tp / (tp + fp)
                recall = tp / (tp + fn)
                score = 2 * (precision * recall) / (precision + recall)
        
        total_f1 += score
        count += 1
        
    return total_f1 / count

def main():
    parser = argparse.ArgumentParser(description="Analyze Champion Performance")
    parser.add_argument("--model", default="model/champion.pkl", help="Path to champion model")
    parser.add_argument("--data", default="data/training_data.json", help="Path to dataset")
    args = parser.parse_args()
    
    print(f"Loading model from {args.model}...")
    with open(args.model, "rb") as f:
        champion = pickle.load(f)
    
    print(f"Champion Tree: {champion}")
        
    print(f"Loading data from {args.data}...")
    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Compile
    pset = setup_gp()
    func = gp.compile(champion, pset)
    
    print("Evaluating...")
    
    buckets = {
        "100% (Perfect)": [],
        "75% - 99% (Good)": [],
        "50% - 74% (Okay)": [],
        "0% - 49% (Bad)": []
    }
    
    print("Evaluating...")
    for entry in data:
        raw = entry["raw"]
        try:
            if raw is None: print("DEBUG: raw is None!")
            pred = func(raw)
            # Ensure we have a NameObj
            if not isinstance(pred, NameObj):
                # Fallback if tree returns something else (shouldn't happen with typed GP but possible)
                pred = NameObj(raw) 
            
            # Fix: Pass entry["solution"] as truth, not entry itself
            truth = entry["solution"]
            score = calculate_entry_f1(pred, truth)
            
            item = {
                "raw": raw,
                "score": score,
                "truth": truth,
                "pred": pred
            }
            
            if score >= 0.99:
                buckets["100% (Perfect)"].append(item)
            elif score >= 0.75:
                buckets["75% - 99% (Good)"].append(item)
            elif score >= 0.50:
                buckets["50% - 74% (Okay)"].append(item)
            else:
                buckets["0% - 49% (Bad)"].append(item)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error processing '{raw}': {e}")

    # Output Report
    print("\n" + "="*60)
    print("PERFORMANCE ANALYSIS REPORT")
    print("="*60)
    
    for bucket_name, items in buckets.items():
        print(f"\n[{bucket_name}] - Count: {len(items)}")
        if not items:
            print("  (No examples)")
            continue
            
        # Table Header
        # Columns: Score | Raw | Salutation | Title | Given | Middle | Family | Suffix | Particles
        header = (
            f"{'Score':<6} | {'Raw Input':<25} | {'Salutation':<12} | {'Title':<15} | "
            f"{'Given':<20} | {'Middle':<15} | {'Family':<20} | {'Suffix':<10} | {'Particles':<10}"
        )
        print("-" * len(header))
        print(header)
        print("-" * len(header))
        
        # ANSI Colors
        GREEN = "\033[92m"
        RED = "\033[91m"
        RESET = "\033[0m"
        
        # Show up to 10 examples for better visibility
        for item in items[:10]:
            p = item['pred']
            t = item['truth']
            
            def get_styled_cell(pred_val, truth_val, width):
                # Handle lists
                if isinstance(pred_val, list): pred_val = ", ".join(pred_val)
                if isinstance(truth_val, list): truth_val = ", ".join(truth_val)
                if not pred_val: pred_val = ""
                if not truth_val: truth_val = ""
                
                is_match = str(pred_val).lower().strip() == str(truth_val).lower().strip()
                
                if is_match:
                    text = f"{pred_val}"
                else:
                    text = f"{pred_val} / {truth_val}"
                
                # Truncate
                if len(text) > width:
                    text = text[:width-2] + ".."
                
                # Pad manually to ensure alignment before coloring
                padded = f"{text:<{width}}"
                
                # Apply Color
                if is_match:
                    return f"{GREEN}{padded}{RESET}"
                else:
                    return f"{RED}{padded}{RESET}"

            # Raw Input (No color, just truncate/pad)
            raw_val = item['raw']
            if len(raw_val) > 25: raw_val = raw_val[:23] + ".."
            raw_cell = f"{raw_val:<25}"

            salut_cell = get_styled_cell(p.salutation, t.get('salutation'), 12)
            title_cell = get_styled_cell(p.title, t.get('title'), 15)
            given_cell = get_styled_cell(p.given, t.get('given'), 20)
            middle_cell = get_styled_cell(p.middle, t.get('middle'), 15)
            family_cell = get_styled_cell(p.family, t.get('family'), 20)
            suffix_cell = get_styled_cell(p.suffix, t.get('suffix'), 10)
            part_cell = get_styled_cell(p.particles, t.get('particles'), 10)
            
            row = (
                f"{item['score']:<6.2f} | {raw_cell} | {salut_cell} | {title_cell} | "
                f"{given_cell} | {middle_cell} | {family_cell} | {suffix_cell} | {part_cell}"
            )
            print(row)
        print("-" * len(header))

if __name__ == "__main__":
    main()
