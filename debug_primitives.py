from primitive_set import tokenize, extract_given_str, extract_family_str, RegexToken

raw = "Ms. Mary Meyer"
tokens = tokenize(raw)
print(f"Tokens: {[t.value for t in tokens]}")

given = extract_given_str(tokens)
print(f"Extracted Given: '{given}'")

family = extract_family_str(tokens)
print(f"Extracted Family: '{family}'")
