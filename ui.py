from rich.console import Console

def draw_bar(val, max_val=1.2, width=8):
    filled = int((val / max_val) * width)
    filled = max(0, min(filled, width))
    bar = "█" * filled + "░" * (width - filled)
    return bar

def print_header(console: Console):
    # Clean Header (No Blue Bar)
    print("\n" + "="*60)
    print(" 🧬 EvoName Island Model Training 🧬")
    print("="*60 + "\n")
    
    # Header
    header = f"{'Gen':<4} | {'Main Island':<20} | {'Detail Island':<20} | {'Structure Island':<20} | Phase"
    console.print(f"[bold]{header}[/bold]")
    console.print("-" * 90)
