import random
import json
import urllib.request
from deap import gp, creator, base, tools
import operator
import sys
import os
import sys
import os
sys.path.append(os.getcwd())
from primitive_set import create_pset

# Mock Setup
creator.create("FitnessMax", base.Fitness, weights=(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, -1.0, -1.0))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

pset = create_pset()

def query_ollama(prompt, model="qwen2.5-coder:1.5b"):
    url = "http://localhost:11434/api/generate"
    data = {"model": model, "prompt": prompt, "stream": False}
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", "")
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_llm_repair():
    target_name = "Mrs Prof. Monika Hoffmann"
    
    # Dummy broken individual (just a placeholder string for the prompt)
    code_str = "make_name_obj(raw_input, EMPTY_STR, EMPTY_TOK_LIST, EMPTY_STR, EMPTY_STR, EMPTY_TOK_LIST, FEMALE, EMPTY_TOK_LIST, EMPTY_TOK_LIST)"
    
    print(f"🧪 Testing LLM Repair for: '{target_name}'")
    print(f"Original Code: {code_str}\n")

    prompt = f"""
You are an expert in Genetic Programming and Python.
The following expression is supposed to parse the name "{target_name}" into a structured object (NameObj), but it fails.

Current Expression:
{code_str}

Available Primitives:
- String Ops: trim, to_lower, split_on_comma, get_first_string, get_last_string
- Token Ops: tokenize, filter_by_type, count_type, get_first_token, get_last_token, slice_tokens, remove_type, index_of_type, get_remainder_tokens
- Feature Detectors: has_comma, is_title, is_salutation, is_all_caps, is_capitalized, is_short, is_common_given_name, is_common_family_name
- Boosters: extract_salutation_str, extract_title_list, extract_given_str, extract_family_str, extract_middle_str, extract_suffix_list, extract_particles_list
- Object Builder: make_name_obj(raw, salutation, title_list, given, family, middle_list, gender, suffix_list, particles_list)

Task:
Modify the expression to better handle the name "{target_name}".
CRITICAL: The expression MUST start with `make_name_obj(...)`. Do not return a list or string directly.
Return ONLY the new expression string. Do not use markdown code blocks.
"""

    print("🤖 Querying LLM...")
    response = query_ollama(prompt)
    
    if not response:
        print("❌ No response from LLM.")
        return

    cleaned_code = response.strip().replace("```python", "").replace("```", "").strip()
    print(f"\n📄 LLM Response:\n{cleaned_code}\n")

    try:
        new_ind = gp.PrimitiveTree.from_string(cleaned_code, pset)
        
        # ROOT NODE CHECK
        if not isinstance(new_ind[0], gp.Primitive) or new_ind[0].name != "make_name_obj":
            print(f"❌ REJECTED: Invalid Root Node '{new_ind[0].name}' (Expected 'make_name_obj')")
        else:
            print(f"✅ ACCEPTED: Valid Root Node '{new_ind[0].name}'")
            print("Structure looks good!")

    except Exception as e:
        print(f"❌ Compilation Failed: {e}")

if __name__ == "__main__":
    test_llm_repair()
