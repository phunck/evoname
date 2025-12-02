import pytest
from primitive_set import (
    tokenize, load_regex_definitions, RegexToken, Token, 
    get_gender_from_salutation, Gender, make_name_obj
)

def test_regex_loader():
    patterns = load_regex_definitions(locale="de")
    assert RegexToken.SALUTATION in patterns
    assert RegexToken.TITLE in patterns
    
    # Check if "Herr" matches SALUTATION
    assert patterns[RegexToken.SALUTATION].match("Herr")
    assert patterns[RegexToken.SALUTATION].match("Frau")
    
    # Negative Test: "Dr." should NOT match SALUTATION
    assert not patterns[RegexToken.SALUTATION].match("Dr.")

def test_tokenize_simple_de():
    raw = "Herr Dr. Hans Müller"
    tokens = tokenize(raw, locale="de")
    
    assert len(tokens) == 4
    
    # Check Indices and Spans
    assert tokens[0].index == 0
    assert tokens[0].value == "Herr"
    assert tokens[0].type == RegexToken.SALUTATION
    
    assert tokens[1].index == 1
    assert tokens[1].value == "Dr."
    assert tokens[1].type == RegexToken.TITLE
    
    assert tokens[2].index == 2
    assert tokens[2].value == "Hans"
    assert tokens[2].type == RegexToken.WORD
    
    assert tokens[3].index == 3
    assert tokens[3].value == "Müller"
    assert tokens[3].type == RegexToken.WORD
    
    # Ensure no PUNCT tokens (unless expected)
    assert all(t.type != RegexToken.PUNCT for t in tokens)

def test_tokenize_priority():
    # "Mr. Dr." -> Should be Salutation then Title
    raw = "Mr. Dr. Jekyll"
    tokens = tokenize(raw, locale="en")
    
    assert len(tokens) == 3
    
    assert tokens[0].value == "Mr."
    assert tokens[0].type == RegexToken.SALUTATION
    
    assert tokens[1].value == "Dr."
    assert tokens[1].type == RegexToken.TITLE
    
    assert tokens[2].value == "Jekyll"
    assert tokens[2].type == RegexToken.WORD

def test_gender_extraction():
    t_herr = Token("Herr", RegexToken.SALUTATION, (0,4), 0)
    assert get_gender_from_salutation(t_herr) == Gender.MALE
    
    t_frau = Token("Frau", RegexToken.SALUTATION, (0,4), 0)
    assert get_gender_from_salutation(t_frau) == Gender.FEMALE
    
    t_unknown = Token("Dr.", RegexToken.TITLE, (0,3), 0)
    assert get_gender_from_salutation(t_unknown) == Gender.UNKNOWN
    
    # English checks
    t_mr = Token("Mr.", RegexToken.SALUTATION, (0,3), 0)
    assert get_gender_from_salutation(t_mr) == Gender.MALE

def test_make_name_obj():
    obj = make_name_obj(
        raw="Test",
        given="Hans",
        family="Müller",
        middle_list=[],
        title_list=["Dr."],
        salutation="Herr",
        gender=Gender.MALE,
        suffix_list=[],
        particles_list=[]
    )
    json_out = obj.to_json()
    assert json_out["raw"] == "Test"
    assert json_out["solution"]["given"] == "Hans"
    assert json_out["solution"]["family"] == "Müller"
    assert json_out["solution"]["title"] == ["Dr"]
    assert json_out["solution"]["salutation"] == "Herr"
    assert json_out["solution"]["gender"] == "m"
