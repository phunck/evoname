import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from primitive_set import tokenize, extract_family_str, RegexToken

def test_fixes():
    print("=" * 60)
    print("VERIFYING FIXES")
    print("=" * 60)

    # Test 1: Particle Extraction
    raw1 = "Mrs. Karin de Jones"
    print(f"\n[TEST 1] Input: '{raw1}'")
    tokens1 = tokenize(raw1)
    print(f"Tokens: {', '.join([f'{t.value}({t.type.name})' for t in tokens1])}")
    
    family_str = extract_family_str(tokens1)
    print(f"Extracted Family: '{family_str}'")
    
    if family_str == "de Jones":
        print("[PASS] Family name correctly includes particle.")
    else:
        print(f"[FAIL] Expected 'de Jones', got '{family_str}'")

    # Test 2: Title Regex
    raw2 = "Frau Dipl. Ing. Petra"
    print(f"\n[TEST 2] Input: '{raw2}'")
    tokens2 = tokenize(raw2)
    print(f"Tokens: {', '.join([f'{t.value}({t.type.name})' for t in tokens2])}")
    
    # Check for Title token
    titles = [t.value for t in tokens2 if t.type == RegexToken.TITLE]
    print(f"Found Titles: {titles}")
    
    if "Dipl. Ing." in titles:
        print("[PASS] 'Dipl. Ing.' recognized as single TITLE.")
    else:
        print("[FAIL] 'Dipl. Ing.' NOT recognized as single TITLE.")

    print("-" * 60)

if __name__ == "__main__":
    test_fixes()
