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
        
    print(f"Loading data from {args.data}...")
    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Compile
    pset = setup_gp()
    func = gp.compile(champion, pset)
    
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
            pred = func(raw)
            # Ensure we have a NameObj
            if not isinstance(pred, NameObj):
                # Fallback if tree returns something else (shouldn't happen with typed GP but possible)
                pred = NameObj(raw) 
            
            score = calculate_entry_f1(pred, entry)
            
            item = {
                "raw": raw,
                "score": score,
                "truth": entry,
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
            
        # Show up to 5 examples
        print("  Examples:")
        for i, item in enumerate(items[:5]):
            print(f"  {i+1}. Input: '{item['raw']}'")
            print(f"     Score: {item['score']:.2f}")
            # Show discrepancies
            p = item['pred']
            t = item['truth']
            
            diffs = []
            if p.given != t.get('given', ''): diffs.append(f"Given: '{p.given}' vs '{t.get('given','')}'")
            if p.family != t.get('family', ''): diffs.append(f"Family: '{p.family}' vs '{t.get('family','')}'")
            if p.salutation != t.get('salutation', ''): diffs.append(f"Salutation: '{p.salutation}' vs '{t.get('salutation','')}'")
            # ... add more if needed
            
            if diffs:
                print(f"     Diffs: {', '.join(diffs)}")
            else:
                print(f"     (Perfect Match)")

if __name__ == "__main__":
    main()
