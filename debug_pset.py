from primitive_set import create_pset

try:
    print("Creating pset...")
    pset = create_pset()
    print("Pset created successfully!")
    print(f"Primitives: {len(pset.primitives)}")
    print(f"Terminals: {len(pset.terminals)}")
except Exception as e:
    print(f"Error creating pset: {e}")
    import traceback
    traceback.print_exc()
