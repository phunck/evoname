from primitive_set import NameObj, StringList

def repair_name_object(obj: NameObj) -> NameObj:
    """
    Applies deterministic repair heuristics to the NameObj.
    
    Heuristic 1: If raw input has exactly 2 words and no title is detected,
    assume structure is "Given Family".
    """
    if not obj or not obj.raw:
        return obj

    # --- Heuristic 1: 2 Words, No Title -> Given Family ---
    # Check if we have exactly 2 words
    parts = obj.raw.strip().split()
    if len(parts) == 2:
        # Check if title is empty
        # Note: obj.title is a StringList, so we check if it's empty
        if not obj.title:
            # Apply repair
            # We trust the raw split more than the model's internal tokenization for this heuristic
            obj.given = parts[0]
            obj.family = parts[1]
            
            # Clear conflicting fields that might have been hallucinated
            # If we force Given/Family, we probably shouldn't have a middle name or suffix 
            # from just 2 words (unless one word is "Jr." etc, but we assume "Given Family")
            obj.middle = StringList([])
            obj.suffix = StringList([])
            obj.particles = StringList([])
            # We keep salutation/gender as they might be inferred correctly or irrelevant
            
    return obj
