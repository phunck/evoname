from deap import gp, creator, base
from primitive_set import *
import primitive_set

# Recreate types
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

def setup_gp():
    pset = gp.PrimitiveSetTyped("MAIN", [str], NameObj)
    
    # Register Primitives
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
    pset.addPrimitive(get_tokens_before_comma, [TokenList], TokenList)
    pset.addPrimitive(get_tokens_after_comma, [TokenList], TokenList)
    
    pset.addPrimitive(tokenize, [str], TokenList)
    pset.addPrimitive(filter_by_type, [TokenList, RegexToken], TokenList)
    pset.addPrimitive(count_type, [TokenList, RegexToken], int)
    pset.addPrimitive(get_gender_from_salutation, [Token], Gender)
    pset.addPrimitive(get_gender_from_name, [str], Gender)
    
    pset.addPrimitive(has_comma, [str], bool)
    pset.addPrimitive(is_title, [Token], bool)
    pset.addPrimitive(is_salutation, [Token], bool)
    pset.addPrimitive(identity_token_type, [RegexToken], RegexToken)

    pset.addPrimitive(extract_salutation_str, [TokenList], str)
    pset.addPrimitive(extract_title_list, [TokenList], StringList)
    pset.addPrimitive(extract_given_str, [TokenList], str)
    pset.addPrimitive(extract_family_str, [TokenList], str)
    pset.addPrimitive(extract_middle_str, [TokenList], StringList)
    pset.addPrimitive(extract_suffix_list, [TokenList], StringList)
    pset.addPrimitive(extract_particles_list, [TokenList], StringList)
    
    pset.addPrimitive(make_name_obj, 
                      [str, str, StringList, str, str, StringList, Gender, StringList, StringList], 
                      NameObj)
    pset.addPrimitive(set_confidence, [NameObj, float], NameObj)
    
    pset.addPrimitive(operator.add, [float, float], float)
    pset.addPrimitive(operator.sub, [float, float], float)
    pset.addPrimitive(operator.mul, [float, float], float)
    
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
    pset = setup_gp()
    raw = "Wolfgang Schmidt"
    
    # Inspect pset.context
    print(f"has_period in context: {pset.context.get('has_period')}")
    print(f"Type of has_period: {type(pset.context.get('has_period'))}")
    
    # Atomic Test 3a: has_period(EMPTY_TOKEN)
    expr_3a = "has_period(EMPTY_TOKEN)"
    print(f"Compiling 3a: {expr_3a}")
    func_3a = gp.compile(expr_3a, pset)
    try:
        print(f"Result 3a: {func_3a(raw)}")
    except Exception as e:
        print(f"3a Failed: {e}")

    # Atomic Test 3b: tokenize(raw_input)
    expr_3b = "tokenize(raw_input)"
    print(f"Compiling 3b: {expr_3b}")
    func_3b = gp.compile(expr_3b, pset)
    try:
        print(f"Result 3b: {func_3b(raw)}")
    except Exception as e:
        print(f"3b Failed: {e}")

    # Atomic Test 3c: if_bool_tokenlist
    # if_bool_tokenlist(has_period(EMPTY_TOKEN), EMPTY_TOK_LIST, EMPTY_TOK_LIST)
    expr_3c = "if_bool_tokenlist(has_period(EMPTY_TOKEN), EMPTY_TOK_LIST, EMPTY_TOK_LIST)"
    print(f"Compiling 3c: {expr_3c}")
    func_3c = gp.compile(expr_3c, pset)
    try:
        print(f"Result 3c: {func_3c(raw)}")
    except Exception as e:
        print(f"3c Failed: {e}")

    # Atomic Test 3d: filter_by_type(EMPTY_TOK_LIST, PARTICLE)
    expr_3d = "filter_by_type(EMPTY_TOK_LIST, PARTICLE)"
    print(f"Compiling 3d: {expr_3d}")
    func_3d = gp.compile(expr_3d, pset)
    try:
        print(f"Result 3d: {func_3d(raw)}")
    except Exception as e:
        print(f"3d Failed: {e}")

    # Subtree 3: Title Extraction (Arg 3)
    expr_str_3 = "extract_particles_list(drop_first(filter_by_type(if_bool_tokenlist(has_period(EMPTY_TOKEN), get_remainder_tokens(get_remainder_tokens(tokenize(raw_input), EMPTY_TOK_LIST), EMPTY_TOK_LIST), EMPTY_TOK_LIST), PARTICLE)))"
    
    print(f"Compiling Subtree 3: {expr_str_3}")
    func_3 = gp.compile(expr_str_3, pset)
    
    import dis
    print("Disassembly of func_3:")
    dis.dis(func_3)
    
    print(f"Running Subtree 3 with: {raw}")
    
    try:
        res = func_3(raw)
        print("Subtree 3 Success!")
        print(res)
    except Exception as e:
        print(f"Subtree 3 Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
