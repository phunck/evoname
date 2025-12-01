/**
 * evoname - library.js
 * JavaScript Runtime for Evolutionary Name Parser
 * 
 * Mirrors primitive_set.py for 1:1 execution of evolved trees.
 */

const fs = require('fs');
const path = require('path');

// --- 1. Types & Enums ---

const Gender = {
    MALE: "m",
    FEMALE: "f",
    DIVERSE: "d",
    UNKNOWN: "null"
};

const RegexToken = {
    SALUTATION: "TOKEN_SALUTATION",
    TITLE: "TOKEN_TITLE",
    DEGREE: "TOKEN_DEGREE",
    INITIAL: "TOKEN_INITIAL",
    PARTICLE: "TOKEN_PARTICLE",
    SUFFIX: "TOKEN_SUFFIX",
    WORD: "TOKEN_WORD",
    PUNCT: "TOKEN_PUNCT"
};

class Token {
    constructor(value, type, span, index = -1) {
        this.value = value;
        this.type = type;
        this.span = span; // [start, end]
        this.index = index;
    }
}

class NameObj {
    constructor(raw, given = "", family = "", middle = [], title = [], salutation = "", gender = Gender.UNKNOWN, suffix = [], particles = [], confidence = 1.0) {
        this.raw = raw;
        this.given = given;
        this.family = family;
        this.middle = middle; // Array of strings
        this.title = title;   // Array of strings
        this.salutation = salutation;
        this.gender = gender;
        this.suffix = suffix; // Array of strings
        this.particles = particles; // Array of strings
        this.confidence = confidence;
    }
}

// --- 2. Regex Loader ---

let REGEX_CACHE = {};

function loadRegexDefinitions(locale = "de", injectedDefinitions = null) {
    const cacheKey = locale;
    if (REGEX_CACHE[cacheKey]) {
        return REGEX_CACHE[cacheKey];
    }

    let defs;
    if (injectedDefinitions) {
        defs = injectedDefinitions;
    } else if (typeof REGEX_DEFINITIONS !== 'undefined') {
        // Check for global injection (Bundled mode)
        defs = REGEX_DEFINITIONS;
    } else {
        // Node.js mode (Development)
        try {
            const defsPath = path.join(__dirname, 'regex_definitions.json');
            defs = JSON.parse(fs.readFileSync(defsPath, 'utf8'));
        } catch (e) {
            console.warn("Could not load regex_definitions.json from disk. Ensure it is injected or present.");
            defs = {};
        }
    }

    const patterns = {};

    const keyMap = {
        "TOKEN_SALUTATION": RegexToken.SALUTATION,
        "TOKEN_TITLE": RegexToken.TITLE,
        "TOKEN_DEGREE": RegexToken.DEGREE,
        "TOKEN_INITIAL": RegexToken.INITIAL,
        "TOKEN_PARTICLE": RegexToken.PARTICLE,
        "TOKEN_SUFFIX": RegexToken.SUFFIX,
        "TOKEN_WORD": RegexToken.WORD,
        "TOKEN_PUNCT": RegexToken.PUNCT
    };

    for (const [jsonKey, tokenEnum] of Object.entries(keyMap)) {
        if (!defs[jsonKey]) continue;

        const entry = defs[jsonKey];
        let target = entry[locale];

        if (!target) {
            if (entry["en"]) target = entry["en"];
            else if (entry["default"]) target = entry["default"];
            else target = Object.values(entry)[0];
        }

        let patternStr = "";
        let flagsStr = "";

        if (typeof target === 'object') {
            patternStr = target.pattern;
            flagsStr = target.flags || "";
        } else {
            patternStr = target;
        }

        let flags = "g";
        if (flagsStr.includes("i")) flags += "i";

        patterns[tokenEnum] = new RegExp(patternStr, flags);
    }

    REGEX_CACHE[cacheKey] = patterns;
    return patterns;
}

// --- 3. Primitives ---

// 3.1 Control Flow
function if_bool_string(cond, a, b) {
    return cond ? a : b;
}

function if_bool_tokenlist(cond, a, b) {
    return cond ? a : b;
}

// 3.2 String & List Ops
function trim(s) {
    return s.trim();
}

function to_lower(s) {
    return s.toLowerCase();
}

function split_on_comma(s) {
    return s.split(",").map(p => p.trim()).filter(p => p.length > 0);
}

function get_first_string(l) {
    return l.length > 0 ? l[0] : "";
}

function get_last_string(l) {
    return l.length > 0 ? l[l.length - 1] : "";
}

function get_first_token(l) {
    return l.length > 0 ? l[0] : null; // Return null for Optional
}

function get_last_token(l) {
    return l.length > 0 ? l[l.length - 1] : null;
}

function slice_tokens(l, start, end) {
    if (start < 0) start = 0;
    if (end > l.length) end = l.length;
    if (start > end) return [];
    return l.slice(start, end);
}

function len_tokens(l) {
    return l.length;
}

function drop_first(l) {
    return l.length > 0 ? l.slice(1) : [];
}

function drop_last(l) {
    return l.length > 0 ? l.slice(0, -1) : [];
}

function remove_type(tokens, type_) {
    return tokens.filter(t => t.type !== type_);
}

function index_of_type(tokens, type_) {
    return tokens.findIndex(t => t.type === type_);
}

function get_remainder_tokens(original, used) {
    // JS Set doesn't work on objects by value/content, only reference.
    // We use span as unique ID: "start-end"
    const usedSpans = new Set(used.map(t => `${t.span[0]}-${t.span[1]}`));
    return original.filter(t => !usedSpans.has(`${t.span[0]}-${t.span[1]}`));
}

// 3.3 Token Muscles
function tokenize(s, locale = "de") {
    const patterns = loadRegexDefinitions(locale);

    const priority = [
        RegexToken.SALUTATION,
        RegexToken.TITLE,
        RegexToken.DEGREE,
        RegexToken.SUFFIX,
        RegexToken.PARTICLE,
        RegexToken.INITIAL,
        RegexToken.WORD,
        RegexToken.PUNCT
    ];

    const tokens = [];
    let pos = 0;

    while (pos < s.length) {
        let matchFound = false;

        // Skip whitespace
        if (/\s/.test(s[pos])) {
            pos++;
            continue;
        }

        const remaining = s.substring(pos);

        for (const tokenType of priority) {
            if (!patterns[tokenType]) continue;

            const regex = patterns[tokenType];
            // Reset state for global regex
            regex.lastIndex = 0;

            // We need to match at the BEGINNING of 'remaining'
            // JS RegExp doesn't have a direct 'matchAt' equivalent to Python's match()
            // We can use ^ anchor if not present, or just check index.
            // But we can't modify the regex source easily to add ^.
            // Alternative: regex.exec(remaining) and check if index === 0.

            const match = regex.exec(remaining);

            if (match && match.index === 0) {
                const value = match[0];
                tokens.push(new Token(value, tokenType, [pos, pos + value.length], tokens.length));
                pos += value.length;
                matchFound = true;
                break;
            }
        }

        if (!matchFound) {
            pos++;
        }
    }
    return tokens;
}

function filter_by_type(tokens, type_) {
    return tokens.filter(t => t.type === type_);
}

function count_type(tokens, type_) {
    return tokens.filter(t => t.type === type_).length;
}

function get_gender_from_salutation(token) {
    if (!token || token.type !== RegexToken.SALUTATION) {
        return Gender.UNKNOWN;
    }

    const val = token.value.toLowerCase().replace(".", "");
    const maleTerms = new Set(["herr", "herrn", "hr", "mr", "mister", "monsieur", "m", "sir", "lord"]);
    const femaleTerms = new Set(["frau", "fr", "mrs", "ms", "miss", "madame", "mme", "mlle", "dame", "lady"]);

    if (maleTerms.has(val)) return Gender.MALE;
    if (femaleTerms.has(val)) return Gender.FEMALE;
    return Gender.UNKNOWN;
}

// 3.4 Feature Detectors
function has_comma(s) {
    return s.includes(",");
}

function is_title(t) {
    return t ? t.type === RegexToken.TITLE : false;
}

function is_salutation(t) {
    return t ? t.type === RegexToken.SALUTATION : false;
}

function identity_token_type(t) {
    return t;
}

// 3.4.1 New Context Primitives
function get_tokens_before_comma(tokens) {
    for (let i = 0; i < tokens.length; i++) {
        if (tokens[i].type === RegexToken.PUNCT && tokens[i].value.includes(",")) {
            return tokens.slice(0, i);
        }
    }
    return tokens;
}

function get_tokens_after_comma(tokens) {
    for (let i = 0; i < tokens.length; i++) {
        if (tokens[i].type === RegexToken.PUNCT && tokens[i].value.includes(",")) {
            return tokens.slice(i + 1);
        }
    }
    return [];
}

function is_all_caps(t) {
    if (!t) return false;
    return t.value === t.value.toUpperCase() && t.value.length > 1;
}

function is_capitalized(t) {
    if (!t) return false;
    return t.value.charAt(0) === t.value.charAt(0).toUpperCase();
}

function is_short(t) {
    if (!t) return false;
    return t.value.length <= 3;
}

const COMMON_FAMILY_NAMES = new Set([
    "müller", "schmidt", "schneider", "fischer", "weber", "meyer", "wagner", "becker", "schulz", "hoffmann",
    "schäfer", "koch", "bauer", "richter", "klein", "wolf", "schröder", "neumann", "schwarz", "zimmermann",
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis", "rodriguez", "martinez",
    "hernandez", "lopez", "gonzalez", "wilson", "anderson", "thomas", "taylor", "moore", "jackson", "martin",
    "lee", "perez", "thompson", "white", "harris", "sanchez", "clark", "ramirez", "lewis", "robinson",
    "walker", "young", "allen", "king", "wright", "scott", "torres", "nguyen", "hill", "flores",
    "green", "adams", "nelson", "baker", "hall", "rivera", "campbell", "mitchell", "carter", "roberts"
]);

// Reuse GENDER_DB logic for given names (simplified)
const COMMON_GIVEN_NAMES = new Set([
    "james", "john", "robert", "michael", "william", "david", "richard", "joseph", "thomas", "charles",
    "mary", "patricia", "linda", "barbara", "elizabeth", "jennifer", "maria", "susan", "margaret", "dorothy",
    "klaus", "hans", "jürgen", "stefan", "wolfgang", "andreas", "michael", "werner", "gerhard", "dieter",
    "sabine", "renate", "ursula", "monika", "helga", "elisabeth", "ingrid", "gisela", "birgit", "petra"
]);

function is_common_family_name(t) {
    if (!t) return false;
    return COMMON_FAMILY_NAMES.has(t.value.toLowerCase());
}

function is_common_given_name(t) {
    if (!t) return false;
    return COMMON_GIVEN_NAMES.has(t.value.toLowerCase());
}

// 3.6 Macro-Primitives (Boosters)
function extract_salutation_str(tokens) {
    for (const t of tokens) {
        if (t.type === RegexToken.SALUTATION) {
            return t.value;
        }
    }
    return "";
}

function extract_title_list(tokens) {
    return tokens.filter(t => t.type === RegexToken.TITLE).map(t => t.value);
}

function extract_given_str(tokens) {
    for (const t of tokens) {
        if (t.type === RegexToken.WORD) {
            return t.value;
        }
    }
    return "";
}

function extract_family_str(tokens) {
    let lastWord = "";
    for (const t of tokens) {
        if (t.type === RegexToken.WORD) {
            lastWord = t.value;
        }
    }
    return lastWord;
}

function extract_middle_str(tokens) {
    const words = tokens.filter(t => t.type === RegexToken.WORD).map(t => t.value);
    if (words.length <= 2) return [];
    return words.slice(1, -1);
}

function extract_suffix_list(tokens) {
    return tokens.filter(t => t.type === RegexToken.SUFFIX).map(t => t.value);
}

function extract_particles_list(tokens) {
    return tokens.filter(t => t.type === RegexToken.PARTICLE).map(t => t.value);
}

// 3.5 Object Builder
function make_name_obj(raw, given, family, middle, title, salutation, gender, suffix, particles) {
    return new NameObj(raw, given, family, middle, title, salutation, gender, suffix, particles);
}

function set_confidence(obj, c) {
    obj.confidence = c;
    return obj;
}

function get_gender_from_name(name) {
    if (!name) return Gender.UNKNOWN;
    const parts = name.trim().split(/\s+/);
    if (parts.length === 0) return Gender.UNKNOWN;
    const firstName = parts[0].toLowerCase();
    if (COMMON_GIVEN_NAMES.has(firstName)) {
        // Simple heuristic for JS lib
        return Gender.UNKNOWN;
    }
    return Gender.UNKNOWN;
}

// --- Terminals ---
const EMPTY_STR = "";
const EMPTY_STR_LIST = [];
const EMPTY_TOK_LIST = [];
const EMPTY_NAME_OBJ = new NameObj("");
const EMPTY_TOKEN = new Token("", RegexToken.PUNCT, [0, 0], -1);
const TRUE = true;
const FALSE = false;

// --- Exports ---
module.exports = {
    Gender, RegexToken, Token, NameObj,
    loadRegexDefinitions,
    if_bool_string, if_bool_tokenlist,
    trim, to_lower, split_on_comma,
    get_first_string, get_last_string,
    get_first_token, get_last_token,
    slice_tokens, len_tokens, drop_first, drop_last,
    remove_type, index_of_type, get_remainder_tokens,
    tokenize, filter_by_type, count_type, get_gender_from_salutation, get_gender_from_name,
    has_comma, is_title, is_salutation, identity_token_type,
    get_tokens_before_comma, get_tokens_after_comma, is_all_caps, is_capitalized, is_short, is_common_given_name, is_common_family_name,
    extract_salutation_str, extract_title_list, extract_given_str, extract_family_str, extract_middle_str, extract_suffix_list, extract_particles_list,
    make_name_obj, set_confidence,
    EMPTY_STR, EMPTY_STR_LIST, EMPTY_TOK_LIST, EMPTY_NAME_OBJ, EMPTY_TOKEN, TRUE, FALSE
};
