import json

def verify():
    with open('data/train.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    total = len(data)
    with_suffix = len([d for d in data if d['solution']['suffix']])
    with_title = len([d for d in data if d['solution']['title']])
    
    print(f"Total Samples: {total}")
    print(f"With Suffix: {with_suffix} ({with_suffix/total*100:.1f}%)")
    print(f"With Title: {with_title} ({with_title/total*100:.1f}%)")
    
    # Check if we have enough "hard" examples
    # Expected: ~30% hard * 50% suffix = ~15% total suffix (plus normal 5% * 70% = 3.5%) -> ~18.5%
    # Expected: ~30% hard * 80% title = ~24% total title (plus normal 30% * 70% = 21%) -> ~45%
    
    if with_suffix < total * 0.10:
        print("WARNING: Suffix count seems low!")
    else:
        print("✅ Suffix distribution looks boosted.")
        
    if with_title < total * 0.35:
        print("WARNING: Title count seems low!")
    else:
        print("✅ Title distribution looks boosted.")

if __name__ == "__main__":
    verify()
