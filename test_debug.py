import primitive_set
from primitive_set import tokenize, get_tokens_before_comma, extract_middle_str, TokenList, RegexToken

def test():
    raw_input = "Wolfgang Schmidt"
    print(f"Testing with '{raw_input}'")
    
    tokens = tokenize(raw_input)
    print(f"Tokens: {tokens}")
    
    try:
        before = get_tokens_before_comma(tokens)
        print(f"Before comma: {before}")
    except Exception as e:
        print(f"Crash in get_tokens_before_comma: {e}")
        
    try:
        middle = extract_middle_str(before)
        print(f"Middle: {middle}")
    except Exception as e:
        print(f"Crash in extract_middle_str: {e}")

    # Test with comma
    raw_input_comma = "Schmidt, Wolfgang"
    print(f"\nTesting with '{raw_input_comma}'")
    tokens_comma = tokenize(raw_input_comma)
    print(f"Tokens: {tokens_comma}")
    
    try:
        before_comma = get_tokens_before_comma(tokens_comma)
        print(f"Before comma: {before_comma}")
    except Exception as e:
        print(f"Crash in get_tokens_before_comma: {e}")

if __name__ == "__main__":
    test()
