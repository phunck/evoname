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

# 3.4.1 New Context Primitives
def get_tokens_before_comma(tokens: TokenList) -> TokenList:
    for i, t in enumerate(tokens):
        if t.type == RegexToken.PUNCT and "," in t.value:
            return TokenList(tokens[:i])
    return TokenList(tokens)

def get_tokens_after_comma(tokens: TokenList) -> TokenList:
    for i, t in enumerate(tokens):
        if t.type == RegexToken.PUNCT and "," in t.value:
            return TokenList(tokens[i+1:])
    return TokenList([])

def is_all_caps(t: Optional[Token]) -> bool:
    if not t: return False
    return t.value.isupper() and len(t.value) > 1

def is_capitalized(t: Optional[Token]) -> bool:
    if not t: return False
    return t.value[0].isupper()

def is_short(t: Optional[Token]) -> bool:
    if not t: return False
    return len(t.value) <= 3

# Common Name Lists (Top ~50-100 for DE/EN)
COMMON_FAMILY_NAMES = {
    "müller", "schmidt", "schneider", "fischer", "weber", "meyer", "wagner", "becker", "schulz", "hoffmann",
    "schäfer", "koch", "bauer", "richter", "klein", "wolf", "schröder", "neumann", "schwarz", "zimmermann",
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis", "rodriguez", "martinez",
    "hernandez", "lopez", "gonzalez", "wilson", "anderson", "thomas", "taylor", "moore", "jackson", "martin",
    "lee", "perez", "thompson", "white", "harris", "sanchez", "clark", "ramirez", "lewis", "robinson",
    "walker", "young", "allen", "king", "wright", "scott", "torres", "nguyen", "hill", "flores",
    "green", "adams", "nelson", "baker", "hall", "rivera", "campbell", "mitchell", "carter", "roberts"
}

def is_common_family_name(t: Optional[Token]) -> bool:
    if not t: return False
    return t.value.lower() in COMMON_FAMILY_NAMES

def is_common_given_name(t: Optional[Token]) -> bool:
    if not t: return False
    # Reuse GENDER_DB keys as they are common given names
    return t.value.lower() in GENDER_DB

# 3.4.2 Statistical & Feature Primitives
def token_length(t: Optional[Token]) -> int:
    if not t: return 0
    return len(t.value)

def is_initial(t: Optional[Token]) -> bool:
    if not t: return False
    # Check regex type OR pattern (single letter + dot)
    return t.type == RegexToken.INITIAL or (len(t.value) == 2 and t.value[1] == '.' and t.value[0].isalpha())

def has_hyphen(t: Optional[Token]) -> bool:
    if not t: return False
    return "-" in t.value

def has_period(t: Optional[Token]) -> bool:
    if not t: return False
    return "." in t.value

def is_roman_numeral(t: Optional[Token]) -> bool:
    if not t: return False
    # Simple check for common roman numerals used in names
    val = t.value.upper().strip(".,")
    return val in {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"}

def is_particle(t: Optional[Token]) -> bool:
    if not t: return False
    return t.type == RegexToken.PARTICLE

def is_suffix(t: Optional[Token]) -> bool:
    if not t: return False
    return t.type == RegexToken.SUFFIX

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
    s = s.replace("/", "")
    return s.strip(" ,.-")

# 3.5 Object Builder
def make_name_obj(
    raw: str,
    salutation: str,
    title_list: StringList, 
    given: str,
    family: str, 
    middle_list: StringList, 
    gender: Gender,
    suffix_list: StringList,
    particles_list: StringList
) -> NameObj:
    
    # Helper to clean list items
    def clean_list(l):
        if not l: return StringList([])
        return StringList([clean_str_val(x) for x in l if clean_str_val(x)])

    return NameObj(
        raw=raw,
        salutation=clean_str_val(salutation),
        title=clean_list(title_list),
        given=clean_str_val(given),
        family=clean_str_val(family),
        middle=clean_list(middle_list),
        suffix=clean_list(suffix_list),
        particles=clean_list(particles_list),
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

# --- 4. Primitive Set Creation ---
from deap import gp

def create_pset() -> gp.PrimitiveSetTyped:
    pset = gp.PrimitiveSetTyped("MAIN", [str], NameObj)
    
    # Register Primitives
    # -- Control Flow --
    pset.addPrimitive(if_bool_string, [bool, str, str], str)
    pset.addPrimitive(if_bool_tokenlist, [bool, TokenList, TokenList], TokenList)
    
    # -- String/List Ops --
    pset.addPrimitive(trim, [str], str)
    pset.addPrimitive(to_lower, [str], str)
    pset.addPrimitive(split_on_comma, [str], StringList)
    pset.addPrimitive(get_first_string, [StringList], str)
    pset.addPrimitive(get_last_string, [StringList], str)
    
    pset.addPrimitive(get_first_token, [TokenList], Token) 
    pset.addPrimitive(get_last_token, [TokenList], Token)
    pset.addPrimitive(slice_tokens, [TokenList, int, int], TokenList)
    pset.addPrimitive(len_tokens, [TokenList], int)
    pset.addPrimitive(drop_first, [TokenList], TokenList)
    pset.addPrimitive(drop_last, [TokenList], TokenList)
    pset.addPrimitive(remove_type, [TokenList, RegexToken], TokenList)
    pset.addPrimitive(index_of_type, [TokenList, RegexToken], int)
    pset.addPrimitive(get_remainder_tokens, [TokenList, TokenList], TokenList)
    
    # -- Token Muscles --
    pset.addPrimitive(tokenize, [str], TokenList)
    pset.addPrimitive(filter_by_type, [TokenList, RegexToken], TokenList)
    pset.addPrimitive(count_type, [TokenList, RegexToken], int)
    pset.addPrimitive(get_gender_from_salutation, [Token], Gender)
    pset.addPrimitive(get_gender_from_name, [str], Gender)
    
    # -- Feature Detectors --
    pset.addPrimitive(has_comma, [str], bool)
    pset.addPrimitive(is_title, [Token], bool)
    pset.addPrimitive(is_salutation, [Token], bool)
    pset.addPrimitive(identity_token_type, [RegexToken], RegexToken)
    
    # -- New Context Primitives --
    pset.addPrimitive(get_tokens_before_comma, [TokenList], TokenList)
    pset.addPrimitive(get_tokens_after_comma, [TokenList], TokenList)
    pset.addPrimitive(is_all_caps, [Token], bool)
    pset.addPrimitive(is_capitalized, [Token], bool)
    pset.addPrimitive(is_short, [Token], bool)
    pset.addPrimitive(is_common_given_name, [Token], bool)
    pset.addPrimitive(is_common_given_name, [Token], bool)
    pset.addPrimitive(is_common_family_name, [Token], bool)

    # -- Statistical & Feature Primitives --
    pset.addPrimitive(token_length, [Token], int)
    pset.addPrimitive(is_initial, [Token], bool)
    pset.addPrimitive(has_hyphen, [Token], bool)
    pset.addPrimitive(has_period, [Token], bool)
    pset.addPrimitive(is_roman_numeral, [Token], bool)
    pset.addPrimitive(is_particle, [Token], bool)
    pset.addPrimitive(is_suffix, [Token], bool)

    # -- Macro-Primitives (Boosters) --
    pset.addPrimitive(extract_salutation_str, [TokenList], str)
    pset.addPrimitive(extract_title_list, [TokenList], StringList)
    pset.addPrimitive(extract_given_str, [TokenList], str)
    pset.addPrimitive(extract_family_str, [TokenList], str)
    pset.addPrimitive(extract_middle_str, [TokenList], StringList)
    pset.addPrimitive(extract_suffix_list, [TokenList], StringList)
    pset.addPrimitive(extract_particles_list, [TokenList], StringList)
    
    # -- Object Builder --
    pset.addPrimitive(make_name_obj, 
                      [str, str, StringList, str, str, StringList, Gender, StringList, StringList], 
                      NameObj)
    pset.addPrimitive(set_confidence, [NameObj, float], NameObj)
    
    # -- Float Math --
    pset.addPrimitive(operator.add, [float, float], float)
    pset.addPrimitive(operator.sub, [float, float], float)
    pset.addPrimitive(operator.mul, [float, float], float)
    
    # -- Ephemeral Constants --
    pset.addEphemeralConstant("rand_int", gen_rand_int, int)
    pset.addEphemeralConstant("rand_float", gen_rand_float, float)
    
    # -- Enums as Terminals --
    for token_type in RegexToken:
        pset.addTerminal(token_type, RegexToken, name=token_type.name)
        
    for g in Gender:
        pset.addTerminal(g, Gender, name=g.name)

    # Empty Lists/Strings for fallbacks
    pset.addTerminal("", str, name="EMPTY_STR")
    pset.addTerminal(StringList([]), StringList, name="EMPTY_STR_LIST")
    pset.addTerminal(TokenList([]), TokenList, name="EMPTY_TOK_LIST")
    
    # Fallback Objects
    pset.addTerminal(NameObj(""), NameObj, name="EMPTY_NAME_OBJ")
    pset.addTerminal(Token("", RegexToken.PUNCT, (0,0), -1), Token, name="EMPTY_TOKEN")
    
    # Booleans
    pset.addTerminal(True, bool, name="TRUE")
    pset.addTerminal(False, bool, name="FALSE")

    # Rename arguments for clarity
    pset.renameArguments(ARG0="raw_input")
    
    return pset
