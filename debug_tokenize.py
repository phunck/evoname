from primitive_set import tokenize, RegexToken, drop_first, extract_given_str

def debug(raw):
    print(f"Input: '{raw}'")
    tokens = tokenize(raw)
    print(f"Tokens: {[t.value for t in tokens]}")
    print(f"Types: {[t.type.name for t in tokens]}")
    
    dropped = drop_first(tokens)
    print(f"Dropped: {[t.value for t in dropped]}")
    
    given = extract_given_str(dropped)
    print(f"Given (from dropped): '{given}'")
    
    given_full = extract_given_str(tokens)
    print(f"Given (from full): '{given_full}'")

if __name__ == "__main__":
    debug("Dr. Paul Boris Hunck")
