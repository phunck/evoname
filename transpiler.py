import pickle
import argparse
import os
import sys
import json
from deap import gp, creator, base
from primitive_set import *  # Import all to match trainer's namespace for unpickling
import primitive_set # Keep module reference for checks

# Recreate the types used in the pickle
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

def transpile_terminal(node):
    # Check for named terminals (Arguments and Constants)
    name = getattr(node, "name", "")
    val = node.value
    
    # 1. Arguments
    if name == "raw_input" or name == "ARG0":
        return "raw_input"
        
    # 2. Known Constants (Map name -> lib.NAME)
    known_constants = {
        "EMPTY_STR", "EMPTY_STR_LIST", "EMPTY_TOK_LIST", 
        "EMPTY_NAME_OBJ", "EMPTY_TOKEN", "TRUE", "FALSE"
    }
    if name in known_constants:
        return f"lib.{name}"
        
    # 3. Enums (RegexToken, Gender)
    if isinstance(val, primitive_set.RegexToken):
        return f"lib.RegexToken.{val.name}"
    if isinstance(val, primitive_set.Gender):
        return f"lib.Gender.{val.name}"
    
    # Fallback for Enums if they appear as strings
    if name in primitive_set.RegexToken.__members__:
        return f"lib.RegexToken.{name}"
    if name in primitive_set.Gender.__members__:
        return f"lib.Gender.{name}"

    # 4. Literals
    if isinstance(val, str):
        return '""' if val == "" else f'"{val}"'
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, list):
        return "[]"
        
    return str(val)

def transpile_primitive(node, args):
    func_name = node.name
    # Standard Primitives -> lib.funcName
    return f"lib.{func_name}({', '.join(args)})"

import re

def bundle_library():
    """Reads and sanitizes library.js and regex_definitions.json."""
    # 1. Load Regex Definitions
    with open("regex_definitions.json", "r", encoding="utf-8") as f:
        regex_defs = f.read()
    
    # 2. Load Library Source
    with open("library.js", "r", encoding="utf-8") as f:
        lib_src = f.read()
        
    # 3. Sanitize Library
    # Remove imports that are not needed in bundle or handled via injection
    lib_src = lib_src.replace("const fs = require('fs');", "// const fs = require('fs');")
    lib_src = lib_src.replace("const path = require('path');", "// const path = require('path');")
    
    # Replace module.exports with const lib
    # Use regex to handle potential whitespace differences
    # We match "module.exports = {" and replace with "const lib = {"
    lib_src, count = re.subn(r"module\.exports\s*=\s*\{", "const lib = {", lib_src)
    
    if count == 0:
        print("WARNING: Could not find 'module.exports = {' in library.js to replace with 'const lib = {'. Bundling might fail.")
    else:
        print(f"Successfully replaced module.exports (count: {count})")
    
    return regex_defs, lib_src

def generate_js(individual):
    """
    Wraps the transpiled expression in a self-contained JS module.
    """
    regex_defs, lib_src = bundle_library()
    
    # DEAP trees are flat lists in pre-order
    iterator = iter(individual)
    
    def walk():
        node = next(iterator)
        if isinstance(node, gp.Terminal):
            return transpile_terminal(node)
        elif isinstance(node, gp.Primitive):
            args = [walk() for _ in range(node.arity)]
            return transpile_primitive(node, args)
        else:
            raise ValueError(f"Unknown node type: {type(node)}")

    expr = walk()
    
    js_code = f"""/**
 * evoname - Generated Parser (Self-Contained)
 * Transpiled from Python GP Tree
 */

// --- 1. Injected Configuration ---
const REGEX_DEFINITIONS = {regex_defs};

// --- 2. Runtime Library ---
{lib_src}

// --- 3. Champion Logic ---
function champion(raw_input) {{
    return {expr};
}}

// --- 4. Public API ---
function parseName(input, options = {{}}) {{
    // Wrapper to call the champion
    return champion(input);
}}

// Export for CommonJS (Node.js)
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = {{ parseName }};
}}

// Export for Browser (Global Variable)
if (typeof window !== 'undefined') {{
    window.EvoName = {{ parseName }};
}}
"""
    return js_code

def main():
    parser = argparse.ArgumentParser(description="Transpile Python GP Tree to Self-Contained JavaScript")
    parser.add_argument("--input", required=True, help="Path to champion.pkl")
    parser.add_argument("--output", required=True, help="Path to output .js file")
    
    args = parser.parse_args()
    
    print(f"Loading champion from {args.input}...")
    with open(args.input, "rb") as f:
        champion = pickle.load(f)
        
    print("Transpiling and Bundling...")
    js_code = generate_js(champion)
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(js_code)
        
    print(f"Saved self-contained parser to {args.output}")

if __name__ == "__main__":
    main()
