from primitive_set import create_pset

def check_primitives():
    pset = create_pset()
    
    new_primitives = [
        "get_tokens_before_comma",
        "get_tokens_after_comma",
        "is_all_caps",
        "is_capitalized",
        "is_short",
        "is_common_given_name",
        "is_common_family_name"
    ]
    
    print("Checking for new primitives in pset...")
    found_count = 0
    for p_name in new_primitives:
        if p_name in pset.mapping:
            print(f"✅ Found: {p_name}")
            found_count += 1
        else:
            print(f"❌ MISSING: {p_name}")
            
    if found_count == len(new_primitives):
        print("\nAll new primitives are correctly registered!")
    else:
        print(f"\nOnly {found_count}/{len(new_primitives)} found.")

if __name__ == "__main__":
    check_primitives()
