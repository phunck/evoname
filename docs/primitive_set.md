# Primitive Set Draft for evoname (Refined)

The "Primitive Set" defines the building blocks from which the evolutionary algorithm (DEAP) is allowed to assemble solution programs.
Based on user feedback, this is structured into 5 categories.

## 1. Types (Strongly Typed GP)
*   `String`: A text fragment.
*   `Token`: A recognized Regex Match Object.
*   `TokenList`: List of Tokens.
*   `StringList`: List of Strings.
*   `Boolean`: Truth value.
*   `Int`: Integer (Index, Count).
*   `NameObj`: The target object.
*   `Gender`: Enum Type ("m", "f", "d", "null").
*   `RegexToken`: A Regex Pattern Type (Enum).

## 2. Primitives by Category

### 2.1 Control-Flow & Composition (Strictly Typed)
*   `IF_BOOL_STRING(cond: Bool, a: String, b: String) -> String`
*   `IF_BOOL_TOKENLIST(cond: Bool, a: TokenList, b: TokenList) -> TokenList`
*   `SEQ(step1: Any, step2: Any) -> Any`: (Optional, only if necessary).

### 2.2 String & List Operations
*   `TRIM(s: String) -> String`
*   `TO_LOWER(s: String) -> String`
*   `SPLIT_ON_COMMA(s: String) -> StringList`
*   `SPLIT_ON_SPACE(s: String) -> StringList`
*   `GET_FIRST_STRING(list: StringList) -> String`
*   `GET_FIRST_TOKEN(list: TokenList) -> Token`
*   `GET_LAST_STRING(list: StringList) -> String`
*   `GET_LAST_TOKEN(list: TokenList) -> Token`
*   `GET_AT_STRING(list: StringList, idx: Int) -> String`
*   `GET_AT_TOKEN(list: TokenList, idx: Int) -> Token`
*   `SLICE_TOKENS(list: TokenList, start: Int, end: Int) -> TokenList`
*   `JOIN(list: StringList, sep: String) -> String`
*   `LEN_TOKENS(list: TokenList) -> Int`
*   `DROP_FIRST(list: TokenList) -> TokenList`
*   `DROP_LAST(list: TokenList) -> TokenList`
*   `REMOVE_TYPE(tokens: TokenList, type: RegexToken) -> TokenList`
*   `INDEX_OF_TYPE(tokens: TokenList, type: RegexToken) -> Int`
*   `GET_REMAINDER_TOKENS(original: TokenList, used: TokenList) -> TokenList`: Returns tokens that have not been used yet.
*   `GET_UNMATCHED_TOKENS(tokens: TokenList) -> TokenList`: Alias for Remainder (everything not yet part of NameObj).

### 2.3 Token / Regex Blocks ("Muscles")
Terminals (Regex Patterns):
*   `TOKEN_SALUTATION`: `(Herr|Frau|Mr\.?|Mrs\.?|Ms\.?|Mme\.?|Hr\.?|Fr\.?)`
*   `TOKEN_TITLE`: `(Dr\.?|Prof\.?|Dipl\.-?Ing\.?|...)` (Academic Degrees)
*   `TOKEN_SUFFIX`: `(Jr\.?|Sr\.?|...)`
*   `TOKEN_PARTICLE`: `(von|zu|de|...)`
*   `TOKEN_INITIAL`: `([A-Z]\.)`

Functions:
*   `TOKENIZE(s: String) -> TokenList`: Decomposes String into Tokens (Greedy Strategy).
*   `FILTER_BY_TYPE(tokens: TokenList, type: RegexToken) -> TokenList`
*   `COUNT_TYPE(tokens: TokenList, type: RegexToken) -> Int`
*   `GET_GENDER_FROM_SALUTATION(token: Token) -> Gender`: Mapping (e.g., "Herr"->"m").

### 2.4 Feature Detectors / Predicates
*   `HAS_COMMA(s: String) -> Bool`
*   `CONTAINS_PATTERN(s: String, pattern: RegexToken) -> Bool`
*   `IS_TITLE(t: Token) -> Bool`
*   `IS_SALUTATION(t: Token) -> Bool`
*   `IS_INITIAL(t: Token) -> Bool`
*   `HAS_TITLE(tokens: TokenList) -> Bool`

### 2.5 Object / JSON Builder
*   `MAKE_NAME_OBJ(raw: String, given: String, family: String, middle: StringList, title: StringList, salutation: String, gender: Gender, suffix: StringList, particles: StringList) -> NameObj`
*   `SET_CONFIDENCE(obj: NameObj, c: Float) -> NameObj`
*   `SET_FIELD(obj: NameObj, key: String, val: Any) -> NameObj`

## 3. Example Tree (DSL)
```lisp
(IF_BOOL_OBJ (HAS_COMMA ARG0)
    (MAKE_NAME_OBJ
        ARG0
        (GET_LAST_STRING (SPLIT_ON_COMMA ARG0)) -- Given Name
        (GET_FIRST_STRING (SPLIT_ON_COMMA ARG0)) -- Family Name
        ...
    )
    ...
)
```

## 4. Next Steps
1.  Implementation of these Primitives in Python (DEAP `gp.PrimitiveSetTyped`).
2.  Definition of JS equivalents for the Transpiler.
