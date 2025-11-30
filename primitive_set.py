import json
import re
import enum
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import operator

# --- 1. Types & Enums ---

class Gender(enum.Enum):
    MALE = "m"
    FEMALE = "f"
    DIVERSE = "d"
    UNKNOWN = "null"

class RegexToken(enum.Enum):
    SALUTATION = "TOKEN_SALUTATION"
    TITLE = "TOKEN_TITLE"
    DEGREE = "TOKEN_DEGREE"
    INITIAL = "TOKEN_INITIAL"
    PARTICLE = "TOKEN_PARTICLE"
    SUFFIX = "TOKEN_SUFFIX"
    WORD = "TOKEN_WORD"
    PUNCT = "TOKEN_PUNCT"

@dataclass
class Token:
    value: str
    type: RegexToken
    span: Tuple[int, int]
    index: int = -1  # Position in the token list

    def __repr__(self):
        return f"Token({self.value}, {self.type.name}, {self.span}, {self.index})"

# Define Strong Types for DEAP
class TokenList(list):
    pass

class StringList(list):
    pass

@dataclass
class NameObj:
    raw: str
    given: str = ""
    family: str = ""
    middle: StringList = field(default_factory=StringList)
    title: StringList = field(default_factory=StringList)
    salutation: str = ""
    gender: Gender = Gender.UNKNOWN
    suffix: StringList = field(default_factory=StringList)
    particles: StringList = field(default_factory=StringList)
    confidence: float = 1.0
    
    def to_json(self):
        return {
            "raw": self.raw,
            "solution": {
                "title": self.title,
                "given": self.given,
                "middle": self.middle,
                "family": self.family,
                "suffix": self.suffix,
                "particles": self.particles,
                "salutation": self.salutation,
                "gender": self.gender.value
            },
            "confidence": self.confidence
        }

# --- 2. Regex Loader ---

REGEX_CACHE = {}

def load_regex_definitions(path: str = "regex_definitions.json", locale: str = "de") -> Dict[RegexToken, re.Pattern]:
    """
    Loads regex patterns for the specified locale.
    Falls back to 'en' if locale not found, or fails if critical.
    """
    cache_key = f"{path}_{locale}"
    if cache_key in REGEX_CACHE:
        return REGEX_CACHE[cache_key]

    with open(path, "r", encoding="utf-8") as f:
        defs = json.load(f)

    patterns = {}
    
    # Mapping from JSON keys to Enum
    key_map = {
        "TOKEN_SALUTATION": RegexToken.SALUTATION,
        "TOKEN_TITLE": RegexToken.TITLE,
        "TOKEN_DEGREE": RegexToken.DEGREE,
        "TOKEN_INITIAL": RegexToken.INITIAL,
        "TOKEN_PARTICLE": RegexToken.PARTICLE,
        "TOKEN_SUFFIX": RegexToken.SUFFIX,
        "TOKEN_WORD": RegexToken.WORD,
        "TOKEN_PUNCT": RegexToken.PUNCT
    }

    for json_key, token_enum in key_map.items():
        if json_key not in defs:
            continue
            
        entry = defs[json_key]
        
        # Locale selection logic
        target = entry.get(locale)
        if not target:
            # Fallback to 'en' or 'default' if exists, or first available
            if "en" in entry:
                target = entry["en"]
            elif "default" in entry: # Legacy support if structure mixed
                target = entry["default"]
            else:
                # Take the first one found
                target = list(entry.values())[0]
        
        # Parse pattern and flags
        if isinstance(target, dict):
            pattern_str = target["pattern"]
            flags_str = target.get("flags", "")
        else:
            # Legacy string support if any
            pattern_str = target
            flags_str = ""

        flags = 0
        if "i" in flags_str:
            flags |= re.IGNORECASE
        
        patterns[token_enum] = re.compile(pattern_str, flags)

    REGEX_CACHE[cache_key] = patterns
    return patterns

# --- 3. Primitives ---

# 3.1 Control Flow
def if_bool_string(cond: bool, a: str, b: str) -> str:
    return a if cond else b

def if_bool_tokenlist(cond: bool, a: TokenList, b: TokenList) -> TokenList:
    return TokenList(a if cond else b)

# 3.2 String & List Ops
def trim(s: str) -> str:
    return s.strip()

def to_lower(s: str) -> str:
    return s.lower()

def split_on_comma(s: str) -> StringList:
    return StringList([p.strip() for p in s.split(",") if p.strip()])

def get_first_string(l: StringList) -> str:
    return l[0] if l else ""

def get_last_string(l: StringList) -> str:
    return l[-1] if l else ""

def get_first_token(l: TokenList) -> Optional[Token]:
    return l[0] if l else None

def get_last_token(l: TokenList) -> Optional[Token]:
    return l[-1] if l else None

def slice_tokens(l: TokenList, start: int, end: int) -> TokenList:
    # Safe slicing
    if start < 0: start = 0
    if end > len(l): end = len(l)
    if start > end: return TokenList([])
    return TokenList(l[start:end])

def len_tokens(l: TokenList) -> int:
    return len(l)

def drop_first(l: TokenList) -> TokenList:
    return TokenList(l[1:]) if l else TokenList([])

def drop_last(l: TokenList) -> TokenList:
    return TokenList(l[:-1]) if l else TokenList([])

def remove_type(tokens: TokenList, type_: RegexToken) -> TokenList:
    return TokenList([t for t in tokens if t.type != type_])

def index_of_type(tokens: TokenList, type_: RegexToken) -> int:
    for i, t in enumerate(tokens):
        if t.type == type_:
            return i
    return -1

def get_remainder_tokens(original: TokenList, used: TokenList) -> TokenList:
    # Set subtraction based on object identity or span
    used_spans = {t.span for t in used}
    return TokenList([t for t in original if t.span not in used_spans])

# 3.3 Token Muscles
def tokenize(s: str, locale: str = "de") -> TokenList:
    patterns = load_regex_definitions(locale=locale)
    
    # Priority Order for Matching
    priority = [
        RegexToken.SALUTATION,
        RegexToken.TITLE,
        RegexToken.DEGREE,
        RegexToken.SUFFIX,
        RegexToken.PARTICLE,
        RegexToken.INITIAL,
        RegexToken.WORD,
        RegexToken.PUNCT
    ]
    
    tokens = []
    pos = 0
    while pos < len(s):
        match_found = False
        # Skip whitespace
        if s[pos].isspace():
            pos += 1
            continue
            
        for token_type in priority:
            if token_type not in patterns:
                continue
            regex = patterns[token_type]
            match = regex.match(s, pos)
            if match:
                tokens.append(Token(match.group(0), token_type, match.span(), len(tokens)))
                pos = match.end()
                match_found = True
                break
        
        if not match_found:
            # Safety: skip one char if nothing matches (should rarely happen with WORD/PUNCT)
            pos += 1
            
    return TokenList(tokens)

def filter_by_type(tokens: TokenList, type_: RegexToken) -> TokenList:
    return TokenList([t for t in tokens if t.type == type_])

def count_type(tokens: TokenList, type_: RegexToken) -> int:
    return sum(1 for t in tokens if t.type == type_)

def get_gender_from_salutation(token: Optional[Token]) -> Gender:
    if not token or token.type != RegexToken.SALUTATION:
        return Gender.UNKNOWN
    
    val = token.value.lower().strip(".")
    # Phase 1: Hardcoded Mapping
    male_terms = {"herr", "herrn", "hr", "mr", "mister", "monsieur", "m", "sir", "lord"}
    female_terms = {"frau", "fr", "mrs", "ms", "miss", "madame", "mme", "mlle", "dame", "lady"}
    
    if val in male_terms:
        return Gender.MALE
    if val in female_terms:
        return Gender.FEMALE
    return Gender.UNKNOWN

# Simple Name Database for Gender Guessing
GENDER_DB = {
    # Male
    "james": "m", "john": "m", "robert": "m", "michael": "m", "william": "m", "david": "m",
    "richard": "m", "joseph": "m", "thomas": "m", "charles": "m", "christopher": "m",
    "daniel": "m", "matthew": "m", "anthony": "m", "donald": "m", "mark": "m", "paul": "m",
    "steven": "m", "andrew": "m", "kenneth": "m", "george": "m", "joshua": "m", "kevin": "m",
    "brian": "m", "edward": "m", "ronald": "m", "timothy": "m", "jason": "m", "jeffrey": "m",
    "ryan": "m", "jacob": "m", "gary": "m", "nicholas": "m", "eric": "m", "stephen": "m",
    "jonathan": "m", "larry": "m", "justin": "m", "scott": "m", "brandon": "m", "frank": "m",
    "benjamin": "m", "gregory": "m", "samuel": "m", "raymond": "m", "patrick": "m", "alexander": "m",
    "jack": "m", "dennis": "m", "jerry": "m", "tyler": "m", "aaron": "m", "jose": "m", "henry": "m",
    "douglas": "m", "peter": "m", "adam": "m", "nathan": "m", "zachary": "m", "walter": "m",
    "kyle": "m", "harold": "m", "carl": "m", "jeremy": "m", "keith": "m", "roger": "m", "gerald": "m",
    "ethan": "m", "arthur": "m", "terry": "m", "christian": "m", "sean": "m", "lawrence": "m",
    "austin": "m", "joe": "m", "noah": "m", "jesse": "m", "albert": "m", "bryan": "m", "billy": "m",
    "bruce": "m", "willie": "m", "jordan": "m", "dylan": "m", "alan": "m", "ralph": "m", "gabriel": "m",
    "roy": "m", "juan": "m", "wayne": "m", "eugene": "m", "logan": "m", "randy": "m", "louis": "m",
    "russell": "m", "vincent": "m", "philip": "m", "bobby": "m", "johnny": "m", "bradley": "m",
    "klaus": "m", "hans": "m", "jürgen": "m", "stefan": "m", "wolfgang": "m", "andreas": "m",
    "michael": "m", "werner": "m", "klaus-peter": "m", "gerhard": "m", "dieter": "m", "horst": "m",
    "manfred": "m", "uwe": "m", "günter": "m", "helmut": "m", "rolf": "m", "bernd": "m", "reiner": "m",
    "rainer": "m", "joachim": "m", "torsten": "m", "frank": "m", "jörg": "m", "ralf": "m", "oliver": "m",
    "sven": "m", "dirk": "m", "kai": "m", "holger": "m", "matthias": "m", "markus": "m", "martin": "m",
    "jens": "m", "lars": "m", "alexander": "m", "jan": "m", "tobias": "m", "sebastian": "m", "patrick": "m",
    "marcel": "m", "tim": "m", "tom": "m", "lukas": "m", "felix": "m", "maximilian": "m", "julian": "m",
    "philipp": "m", "jonas": "m", "leon": "m", "elias": "m", "paul": "m", "ben": "m", "noah": "m", "finn": "m",
    
    # Female
    "mary": "f", "patricia": "f", "linda": "f", "barbara": "f", "elizabeth": "f", "jennifer": "f",
    "maria": "f", "susan": "f", "margaret": "f", "dorothy": "f", "lisa": "f", "nancy": "f",
    "karen": "f", "betty": "f", "helen": "f", "sandra": "f", "donna": "f", "carol": "f",
    "ruth": "f", "sharon": "f", "michelle": "f", "laura": "f", "sarah": "f", "kimberly": "f",
    "deborah": "f", "jessica": "f", "shirley": "f", "cynthia": "f", "angela": "f", "melissa": "f",
    "brenda": "f", "amy": "f", "anna": "f", "rebecca": "f", "virginia": "f", "kathleen": "f",
    "pamela": "f", "martha": "f", "debra": "f", "amanda": "f", "stephanie": "f", "carolyn": "f",
    "christine": "f", "marie": "f", "janet": "f", "catherine": "f", "frances": "f", "ann": "f",
    "joyce": "f", "diane": "f", "alice": "f", "julie": "f", "heather": "f", "teresa": "f",
    "doris": "f", "gloria": "f", "evelyn": "f", "jean": "f", "cheryl": "f", "mildred": "f",
    "katherine": "f", "joan": "f", "ashley": "f", "judith": "f", "rose": "f", "janice": "f",
    "kelly": "f", "nicole": "f", "judy": "f", "christina": "f", "kathy": "f", "theresa": "f",
    "beverly": "f", "denise": "f", "tammy": "f", "irene": "f", "jane": "f", "lori": "f",
    "rachel": "f", "marilyn": "f", "andrea": "f", "kathryn": "f", "louise": "f", "sara": "f",
    "anne": "f", "jacqueline": "f", "wanda": "f", "bonnie": "f", "julia": "f", "ruby": "f",
    "lois": "f", "tina": "f", "phyllis": "f", "norma": "f", "paula": "f", "diana": "f",
    "annie": "f", "lillian": "f", "emily": "f", "robin": "f",
    "sabine": "f", "renate": "f", "ursula": "f", "monika": "f", "helga": "f", "elisabeth": "f",
    "ingrid": "f", "gisela": "f", "birgit": "f", "petra": "f", "gabriele": "f", "karin": "f",
    "brigitte": "f", "angelika": "f", "barbara": "f", "ute": "f", "christa": "f", "elke": "f",
    "heike": "f", "kerstin": "f", "susanne": "f", "tanja": "f", "katja": "f", "anja": "f",
    "silke": "f", "nicole": "f", "julia": "f", "sarah": "f", "jessica": "f", "katharina": "f",
    "anna": "f", "laura": "f", "lena": "f", "sophie": "f", "marie": "f", "lea": "f", "emma": "f",
    "mia": "f", "hannah": "f", "emilia": "f", "sofia": "f", "lina": "f", "mila": "f"
}

def get_gender_from_name(name: str) -> Gender:
    if not name:
        return Gender.UNKNOWN
    
    # Check first word if multiple
    parts = name.strip().split()
    if not parts:
        return Gender.UNKNOWN
        
    first_name = parts[0].lower()
    
    if first_name in GENDER_DB:
        g = GENDER_DB[first_name]
        if g == "m": return Gender.MALE
        if g == "f": return Gender.FEMALE
        
    return Gender.UNKNOWN

# 3.4 Feature Detectors
def has_comma(s: str) -> bool:
    return "," in s

def is_title(t: Optional[Token]) -> bool:
    return t.type == RegexToken.TITLE if t else False

def is_salutation(t: Optional[Token]) -> bool:
    return t.type == RegexToken.SALUTATION if t else False

def identity_token_type(t: RegexToken) -> RegexToken:
    return t

# 3.6 Macro-Primitives (Boosters)
def extract_salutation_str(tokens: TokenList) -> str:
    # Finds the first salutation token and returns its value
    for t in tokens:
        if t.type == RegexToken.SALUTATION:
            return t.value
    return ""

def extract_title_list(tokens: TokenList) -> StringList:
    # Returns all title values as StringList
    return StringList([t.value for t in tokens if t.type == RegexToken.TITLE])

def extract_given_str(tokens: TokenList) -> str:
    # Heuristic: First WORD that is not a Salutation/Title
    # This is a simple heuristic to help the EA start
    for t in tokens:
        if t.type == RegexToken.WORD:
            return t.value
    return ""

def extract_family_str(tokens: TokenList) -> str:
    # Heuristic: Last WORD
    last_word = ""
    for t in tokens:
        if t.type == RegexToken.WORD:
            last_word = t.value
    return last_word

def extract_middle_str(tokens: TokenList) -> StringList:
    # Heuristic: Everything between first and last word
    # Returns a StringList of middle names
    words = [t.value for t in tokens if t.type == RegexToken.WORD]
    if len(words) <= 2:
        return StringList([])
    
    # Return everything between first and last
    return StringList(words[1:-1])

def extract_suffix_list(tokens: TokenList) -> StringList:
    # Returns all suffix values
    return StringList([t.value for t in tokens if t.type == RegexToken.SUFFIX])

def extract_particles_list(tokens: TokenList) -> StringList:
    # Returns all particle values
    return StringList([t.value for t in tokens if t.type == RegexToken.PARTICLE])

# Helper to clean strings
def clean_str_val(s: str) -> str:
    if not s: return ""
    # Remove leading/trailing non-alphanumeric chars (except some)
    # Specifically target the issue: "/ Jones" -> "Jones"
    return s.strip(" /,.-")

# 3.5 Object Builder
def make_name_obj(
    raw: str,
    salutation: str,
    title: str, 
    given_list: StringList,
    family_list: StringList, 
    middle_str: str, 
    gender: Gender,
    suffix_list: StringList,
    particles_list: StringList
) -> NameObj:
    
    # Convert Lists to Strings
    given = " ".join(given_list) if isinstance(given_list, list) else str(given_list)
    family = " ".join(family_list) if isinstance(family_list, list) else str(family_list)
    middle = " ".join(middle_str) if isinstance(middle_str, list) else str(middle_str)
    suffix = " ".join(suffix_list) if isinstance(suffix_list, list) else str(suffix_list)
    particles = " ".join(particles_list) if isinstance(particles_list, list) else str(particles_list)
    
    # CLEANUP
    return NameObj(
        raw=raw,
        salutation=clean_str_val(salutation),
        title=clean_str_val(title),
        given=clean_str_val(given),
        family=clean_str_val(family),
        middle=clean_str_val(middle),
        suffix=clean_str_val(suffix),
        particles=clean_str_val(particles),
        gender=gender
    )

def set_confidence(obj: NameObj, c: float) -> NameObj:
    obj.confidence = c
    return obj

# --- Ephemeral Generators ---
import random
def gen_rand_int():
    return random.randint(0, 5)

def gen_rand_float():
    return round(random.random(), 2)

# Aliases for potential pickle compatibility
rand_int = gen_rand_int
rand_float = gen_rand_float
