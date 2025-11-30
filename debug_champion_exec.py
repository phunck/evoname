import pickle
import sys
import os
from deap import gp, creator, base
from primitive_set import *

# Mock classes to allow unpickling
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

def setup_gp():
    pset = gp.PrimitiveSetTyped("MAIN", [str], NameObj)
    pset.addPrimitive(if_bool_string, [bool, str, str], str)
    pset.addPrimitive(if_bool_tokenlist, [bool, TokenList, TokenList], TokenList)
    pset.addPrimitive(trim, [str], str)
    pset.addPrimitive(to_lower, [str], str)
    pset.addPrimitive(split_on_comma, [str], StringList)
    pset.addPrimitive(get_first_string, [StringList], str)
    pset.addPrimitive(get_last_string, [StringList], str)
    pset.addPrimitive(get_first_token, [TokenList], Token)
    pset.addPrimitive(get_last_token, [TokenList], Token)
    pset.addPrimitive(slice_tokens, [TokenList, int, int], TokenList)
    pset.addPrimitive(len_tokens, [TokenList], int)
    pset.addPrimitive(drop_first, [TokenList], TokenList)
    pset.addPrimitive(drop_last, [TokenList], TokenList)
    pset.addPrimitive(remove_type, [TokenList, RegexToken], TokenList)
    pset.addPrimitive(index_of_type, [TokenList, RegexToken], int)
    pset.addPrimitive(get_remainder_tokens, [TokenList, TokenList], TokenList)
    pset.addPrimitive(tokenize, [str], TokenList)
    pset.addPrimitive(filter_by_type, [TokenList, RegexToken], TokenList)
    pset.addPrimitive(count_type, [TokenList, RegexToken], int)
    pset.addPrimitive(get_gender_from_salutation, [Token], Gender)
    pset.addPrimitive(has_comma, [str], bool)
    pset.addPrimitive(is_title, [Token], bool)
    pset.addPrimitive(is_salutation, [Token], bool)
    pset.addPrimitive(identity_token_type, [RegexToken], RegexToken)
    pset.addPrimitive(extract_salutation_str, [TokenList], str)
    pset.addPrimitive(extract_title_list, [TokenList], StringList)
    pset.addPrimitive(extract_given_str, [TokenList], str)
    pset.addPrimitive(extract_family_str, [TokenList], str)
    pset.addPrimitive(make_name_obj, [str, str, str, StringList, StringList, str, Gender, StringList, StringList], NameObj)
    pset.addPrimitive(set_confidence, [NameObj, float], NameObj)
    pset.addPrimitive(operator.add, [float, float], float)
    pset.addPrimitive(operator.sub, [float, float], float)
    pset.addPrimitive(operator.mul, [float, float], float)
    
    def gen_rand_int(): return random.randint(0, 5)
    def gen_rand_float(): return round(random.random(), 2)
    
    pset.addEphemeralConstant("rand_int", gen_rand_int, int)
    pset.addEphemeralConstant("rand_float", gen_rand_float, float)
    
    for token_type in RegexToken:
        pset.addTerminal(token_type, RegexToken, name=token_type.name)
    for g in Gender:
        pset.addTerminal(g, Gender, name=g.name)
        
    pset.addTerminal("", str, name="EMPTY_STR")
    pset.addTerminal(StringList([]), StringList, name="EMPTY_STR_LIST")
    pset.addTerminal(TokenList([]), TokenList, name="EMPTY_TOK_LIST")
    pset.addTerminal(NameObj(""), NameObj, name="EMPTY_NAME_OBJ")
    pset.addTerminal(Token("", RegexToken.PUNCT, (0,0), -1), Token, name="EMPTY_TOKEN")
    pset.addTerminal(True, bool, name="TRUE")
    pset.addTerminal(False, bool, name="FALSE")
    
    pset.renameArguments(ARG0="raw_input")
    return pset

def main():
    path = "runs/2025-11-29_213417/artifacts/champion.pkl"
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    try:
        with open(path, "rb") as f:
            ind = pickle.load(f)
        
        pset = setup_gp()
        func = gp.compile(ind, pset)
        
        raw = "Dr. Paul Boris Hunck"
        print(f"Running champion on '{raw}'...")
        res = func(raw)
        print(f"Result raw: '{res.raw}'")
        print(f"Result given: '{res.given}'")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
