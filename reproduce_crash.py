from primitive_set import *
import re

# Mocking the DEAP terminals/constants
EMPTY_TOKEN = Token("", RegexToken.PUNCT, (0,0), -1)
EMPTY_TOK_LIST = TokenList([])
PARTICLE = RegexToken.PARTICLE
TITLE = RegexToken.TITLE
SUFFIX = RegexToken.SUFFIX
MALE = Gender.MALE
FALSE = False

def run_tree(raw_input):
    print(f"Processing: {raw_input}")
    
    # Argument 1: raw_input
    arg1 = raw_input
    
    # Argument 2: extract_salutation_str(tokenize(raw_input))
    t2 = tokenize(raw_input)
    arg2 = extract_salutation_str(t2)
    
    # Argument 3: extract_particles_list(drop_first(filter_by_type(if_bool_tokenlist(has_period(EMPTY_TOKEN), get_remainder_tokens(get_remainder_tokens(tokenize(raw_input), EMPTY_TOK_LIST), EMPTY_TOK_LIST), EMPTY_TOK_LIST), PARTICLE)))
    # has_period(EMPTY_TOKEN) -> False
    # if_bool_tokenlist(False, ..., EMPTY_TOK_LIST) -> EMPTY_TOK_LIST
    # filter_by_type(EMPTY_TOK_LIST, PARTICLE) -> []
    # drop_first([]) -> []
    # extract_particles_list([]) -> []
    arg3 = extract_particles_list(drop_first(filter_by_type(if_bool_tokenlist(has_period(EMPTY_TOKEN), get_remainder_tokens(get_remainder_tokens(tokenize(raw_input), EMPTY_TOK_LIST), EMPTY_TOK_LIST), EMPTY_TOK_LIST), PARTICLE)))
    
    # Argument 4: extract_given_str(get_remainder_tokens(tokenize(raw_input), EMPTY_TOK_LIST))
    t4 = tokenize(raw_input)
    r4 = get_remainder_tokens(t4, EMPTY_TOK_LIST)
    arg4 = extract_given_str(r4)
    
    # Argument 5: extract_family_str(tokenize(raw_input))
    t5 = tokenize(raw_input)
    arg5 = extract_family_str(t5)
    
    # Argument 6: extract_middle_str(...)
    # identity_token_type(TITLE) -> TITLE
    # remove_type(EMPTY_TOK_LIST, TITLE) -> []
    # get_remainder_tokens(tokenize(raw_input), []) -> tokenize(raw_input)
    # get_tokens_before_comma(...)
    t6 = tokenize(raw_input)
    r6 = get_remainder_tokens(t6, remove_type(EMPTY_TOK_LIST, identity_token_type(identity_token_type(identity_token_type(identity_token_type(identity_token_type(TITLE)))))))
    b6 = get_tokens_before_comma(r6)
    arg6 = extract_middle_str(b6)
    
    # Argument 7: MALE
    arg7 = MALE
    
    # Argument 8: extract_particles_list(...)
    # get_tokens_after_comma(EMPTY_TOK_LIST) -> []
    # get_tokens_before_comma([]) -> []
    # get_remainder_tokens([], EMPTY_TOK_LIST) -> []
    # if_bool_tokenlist(FALSE, ..., EMPTY_TOK_LIST) -> EMPTY_TOK_LIST
    # filter_by_type(EMPTY_TOK_LIST, SUFFIX) -> []
    # drop_first([]) -> []
    # extract_particles_list([]) -> []
    arg8 = extract_particles_list(drop_first(filter_by_type(if_bool_tokenlist(FALSE, get_remainder_tokens(get_tokens_before_comma(get_tokens_after_comma(EMPTY_TOK_LIST)), EMPTY_TOK_LIST), EMPTY_TOK_LIST), identity_token_type(SUFFIX))))
    
    # Argument 9: extract_particles_list(drop_first(drop_first(tokenize(raw_input))))
    t9 = tokenize(raw_input)
    d9_1 = drop_first(t9)
    d9_2 = drop_first(d9_1)
    arg9 = extract_particles_list(d9_2)
    
    print("Constructing NameObj...")
    res = make_name_obj(arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9)
    print("Result:", res)
    return res

if __name__ == "__main__":
    try:
        run_tree("Wolfgang Schmidt")
        run_tree("Mrs. Dipl.-Ing. Linda Elisabeth vom Meyer PhD")
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()
