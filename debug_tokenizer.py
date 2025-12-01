from primitive_set import tokenize, RegexToken

def debug_tokens(text):
    print(f"\n--- Debugging: '{text}' ---")
    tokens = tokenize(text, locale="de") # Using 'de' as default for mixed data
    for i, t in enumerate(tokens):
        print(f"{i}: {t.value} -> {t.type.name}")

examples = [
    "Prof. Dr. Peter Meyer Sr.",
    "Mr. Dr. med. Thomas Hans",
    "Ms. Dr. Linda van Smith",
    "Mrs. Monika Becker Jr.",
    "Frau Dipl.-Ing. Elisabeth III"
]

for ex in examples:
    debug_tokens(ex)
