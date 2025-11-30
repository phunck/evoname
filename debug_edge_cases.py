from primitive_set import tokenize, extract_given_str, extract_family_str, RegexToken

test_cases = [
    "Mrs Dipl.-Ing. Sabine Maria Hoffmann", # "Mrs" -> "s"?
    "Dr. med. Thomas Hans Wagner",          # "Dr. med." -> "med"?
    "Prof. Dr. Peter Meyer Sr.",            # "Sr." -> Family?
    "Ms Sabine Williams Sr."                # "Sr." -> Family?
]

print("--- Debugging Edge Cases ---")
for raw in test_cases:
    print(f"\nInput: '{raw}'")
    tokens = tokenize(raw)
    print(f"Tokens: {[t.value for t in tokens]}")
    print(f"Types:  {[t.type.name for t in tokens]}")
    
    given = extract_given_str(tokens)
    family = extract_family_str(tokens)
    
    print(f"Extracted Given: '{given}'")
    print(f"Extracted Family: '{family}'")
