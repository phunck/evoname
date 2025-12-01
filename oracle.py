from primitive_set import (
    tokenize, RegexToken, NameObj, StringList, Gender,
    get_gender_from_salutation, get_gender_from_name,
    clean_str_val
)

class OracleParser:
    """
    A rule-based 'Oracle' parser to serve as a baseline.
    It uses the same tokenizer as the GP model but applies fixed heuristics.
    """
    
    def parse(self, raw_name: str) -> NameObj:
        tokens = tokenize(raw_name)
        
        # 1. Extract Known Components
        salutation = ""
        titles = []
        suffixes = []
        particles = []
        words = []
        
        salutation_token = None
        
        for t in tokens:
            if t.type == RegexToken.SALUTATION:
                if not salutation: # Take first
                    salutation = t.value
                    salutation_token = t
            elif t.type == RegexToken.TITLE:
                titles.append(t.value)
            elif t.type == RegexToken.SUFFIX:
                suffixes.append(t.value)
            elif t.type == RegexToken.PARTICLE:
                particles.append(t.value)
            elif t.type == RegexToken.WORD:
                words.append(t.value)
            # Ignore Punctuation for now (except comma handling below)
            
        # 2. Handle Comma (Family, Given)
        # Check raw string for comma
        if "," in raw_name:
            # Split words by comma position? 
            # Simpler: If comma exists, assume "Family, Given Middle"
            # But we need to know WHICH word is before the comma.
            # Let's stick to a simpler heuristic for the baseline:
            # If comma, first word is Family, rest Given.
            if len(words) >= 2:
                family = words[0]
                given = " ".join(words[1:])
                middle = [] # Oracle is lazy with middle names in comma case
            else:
                family = words[0] if words else ""
                given = ""
                middle = []
        else:
            # Standard "Given Middle Family"
            if not words:
                family = ""
                given = ""
                middle = []
            elif len(words) == 1:
                # Ambiguous. Usually Family if only one name? Or Given?
                # Let's say Given for single word (e.g. "Madonna"), unless it's clearly a list of names.
                # Actually, standard datasets often have "Family" as required.
                # Let's assign to Family to be safe (Vital Penalty).
                family = words[0]
                given = ""
                middle = []
            else:
                # Last word is Family
                family = words[-1]
                # First word is Given
                given = words[0]
                # Everything in between is Middle
                middle = words[1:-1]

        # 3. Gender Guessing
        gender = Gender.UNKNOWN
        
        # Try Salutation
        if salutation_token:
            gender = get_gender_from_salutation(salutation_token)
            
        # Try Name if unknown
        if gender == Gender.UNKNOWN and given:
            gender = get_gender_from_name(given)

        # 4. Construct Object
        return NameObj(
            raw=raw_name,
            salutation=clean_str_val(salutation),
            title=StringList([clean_str_val(x) for x in titles]),
            given=clean_str_val(given),
            family=clean_str_val(family),
            middle=StringList([clean_str_val(x) for x in middle]),
            suffix=StringList([clean_str_val(x) for x in suffixes]),
            particles=StringList([clean_str_val(x) for x in particles]),
            gender=gender,
            confidence=1.0
        )
