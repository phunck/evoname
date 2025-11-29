import pickle
import argparse
import os
import sys
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
    # Sometimes val is the Enum object, sometimes it might be the name if pickled weirdly
    if isinstance(val, primitive_set.RegexToken):
        return f"lib.RegexToken.{val.name}"
    if isinstance(val, primitive_set.Gender):
        return f"lib.Gender.{val.name}"
    
    # Fallback for Enums if they appear as strings (e.g. "SALUTATION")
    # We check if the name matches a RegexToken member
    if name in primitive_set.RegexToken.__members__:
        return f"lib.RegexToken.{name}"
    if name in primitive_set.Gender.__members__:
        return f"lib.Gender.{name}"

    # 4. Literals
    # Strings
    if isinstance(val, str):
        if val == "":
            return '""' 
        return f'"{val}"'
        
    # Booleans
    if isinstance(val, bool):
        return "true" if val else "false"
        
    # Numbers
    if isinstance(val, (int, float)):
        return str(val)
        
    # Lists (Empty constants fallback)
    if isinstance(val, list):
        return "[]"
        
    # Fallback
    return str(val)

def transpile_primitive(node, args):
    func_name = node.name
    
    # Map operator module functions if used
    if func_name == "add": return f"({args[0]} + {args[1]})"
    if func_name == "sub": return f"({args[0]} - {args[1]})"
    if func_name == "mul": return f"({args[0]} * {args[1]})"
    
    # Standard Primitives -> lib.funcName
    return f"lib.{func_name}({', '.join(args)})"

def generate_js(individual):
    """
    Wraps the transpiled expression in a JS module structure.
    """
    # DEAP trees are flat lists in pre-order (Polish notation)
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
 * evoname - Generated Parser
 * Transpiled from Python GP Tree
 */
const lib = require('../library');

function parse(raw_input) {{
    // The evolved tree expects 'raw_input' as argument
    return {expr};
}}

module.exports = parse;
"""
    return js_code

def main():
    parser = argparse.ArgumentParser(description="Transpile Python GP Tree to JavaScript")
    parser.add_argument("--input", required=True, help="Path to champion.pkl")
    parser.add_argument("--output", required=True, help="Path to output .js file")
    
    args = parser.parse_args()
    
    print(f"Loading champion from {args.input}...")
    with open(args.input, "rb") as f:
        champion = pickle.load(f)
        
    print("Transpiling...")
    js_code = generate_js(champion)
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(js_code)
        
    print(f"Saved transpiled parser to {args.output}")

if __name__ == "__main__":
    main()
