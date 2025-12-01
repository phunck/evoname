const {
    Token, RegexToken,
    token_length, is_initial, has_hyphen, has_period,
    is_roman_numeral, is_particle, is_suffix
} = require('../library');

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

function test_token_length() {
    const t = new Token("Hello", RegexToken.WORD, [0, 5]);
    assert(token_length(t) === 5, "token_length should be 5");
    assert(token_length(null) === 0, "token_length(null) should be 0");
}

function test_is_initial() {
    const t1 = new Token("J.", RegexToken.INITIAL, [0, 2]);
    const t2 = new Token("John", RegexToken.WORD, [0, 4]);
    const t3 = new Token("K.", RegexToken.WORD, [0, 2]);

    assert(is_initial(t1) === true, "J. should be initial");
    assert(is_initial(t2) === false, "John should not be initial");
    assert(is_initial(t3) === true, "K. should be initial (pattern check)");
}

function test_has_hyphen() {
    const t1 = new Token("Hans-Peter", RegexToken.WORD, [0, 10]);
    const t2 = new Token("Hans", RegexToken.WORD, [0, 4]);
    assert(has_hyphen(t1) === true, "Hans-Peter should have hyphen");
    assert(has_hyphen(t2) === false, "Hans should not have hyphen");
}

function test_has_period() {
    const t1 = new Token("St.", RegexToken.PARTICLE, [0, 3]);
    const t2 = new Token("Saint", RegexToken.WORD, [0, 5]);
    assert(has_period(t1) === true, "St. should have period");
    assert(has_period(t2) === false, "Saint should not have period");
}

function test_is_roman_numeral() {
    const t1 = new Token("III", RegexToken.SUFFIX, [0, 3]);
    const t2 = new Token("iv", RegexToken.SUFFIX, [0, 2]);
    const t3 = new Token("IV.", RegexToken.SUFFIX, [0, 3]);
    const t4 = new Token("Müller", RegexToken.WORD, [0, 6]);

    assert(is_roman_numeral(t1) === true, "III should be roman");
    assert(is_roman_numeral(t2) === true, "iv should be roman");
    assert(is_roman_numeral(t3) === true, "IV. should be roman");
    assert(is_roman_numeral(t4) === false, "Müller should not be roman");
}

function test_is_particle() {
    const t1 = new Token("von", RegexToken.PARTICLE, [0, 3]);
    const t2 = new Token("Müller", RegexToken.WORD, [0, 6]);
    assert(is_particle(t1) === true, "von should be particle");
    assert(is_particle(t2) === false, "Müller should not be particle");
}

function test_is_suffix() {
    const t1 = new Token("Jr.", RegexToken.SUFFIX, [0, 3]);
    const t2 = new Token("Müller", RegexToken.WORD, [0, 6]);
    assert(is_suffix(t1) === true, "Jr. should be suffix");
    assert(is_suffix(t2) === false, "Müller should not be suffix");
}

try {
    test_token_length();
    test_is_initial();
    test_has_hyphen();
    test_has_period();
    test_is_roman_numeral();
    test_is_particle();
    test_is_suffix();
    console.log("All JS Tests Passed!");
} catch (e) {
    console.error(e);
    process.exit(1);
}
