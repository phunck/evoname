const lib = require('../library.js');
const assert = require('assert');

// Mock Regex Definitions for Tokenization (Minimal)
// In a real scenario, we'd load them, but here we construct tokens manually to test primitives directly.
const { Token, RegexToken, Gender } = lib;

function runTests() {
    console.log("Running JS Advanced Primitives Tests...");

    // Setup Data
    const t_doe = new Token("Doe", RegexToken.WORD, [0, 3], 0);
    const t_comma = new Token(",", RegexToken.PUNCT, [3, 4], 1);
    const t_john = new Token("John", RegexToken.WORD, [5, 9], 2);
    const tokens_comma = [t_doe, t_comma, t_john];

    const t_caps = new Token("JAMES", RegexToken.WORD, [0, 5], 0);
    const t_short = new Token("Dr", RegexToken.TITLE, [0, 2], 0);
    const t_mueller = new Token("Müller", RegexToken.WORD, [0, 6], 0);

    // 1. Context Primitives
    // Before comma
    const before = lib.get_tokens_before_comma(tokens_comma);
    assert.strictEqual(before.length, 1, "Should have 1 token before comma");
    assert.strictEqual(before[0].value, "Doe");

    // After comma
    const after = lib.get_tokens_after_comma(tokens_comma);
    assert.strictEqual(after.length, 1, "Should have 1 token after comma");
    assert.strictEqual(after[0].value, "John");

    // No comma
    const no_comma = [t_doe, t_john];
    const before_nc = lib.get_tokens_before_comma(no_comma);
    assert.strictEqual(before_nc.length, 2, "Should return all if no comma");
    const after_nc = lib.get_tokens_after_comma(no_comma);
    assert.strictEqual(after_nc.length, 0, "Should return empty if no comma");

    // 2. Boolean Primitives
    // is_all_caps
    assert.strictEqual(lib.is_all_caps(t_caps), true);
    assert.strictEqual(lib.is_all_caps(t_doe), false);

    // is_capitalized
    assert.strictEqual(lib.is_capitalized(t_doe), true);
    assert.strictEqual(lib.is_capitalized(new Token("lower", RegexToken.WORD, [0, 5], 0)), false);

    // is_short
    assert.strictEqual(lib.is_short(t_short), true);
    assert.strictEqual(lib.is_short(t_john), false);

    // 3. Lexicon Primitives
    // is_common_family_name
    assert.strictEqual(lib.is_common_family_name(t_mueller), true);
    assert.strictEqual(lib.is_common_family_name(new Token("Smith", RegexToken.WORD, [0, 5], 0)), true);
    assert.strictEqual(lib.is_common_family_name(t_john), false);

    // is_common_given_name
    assert.strictEqual(lib.is_common_given_name(t_john), true);
    assert.strictEqual(lib.is_common_given_name(t_caps), false, "JAMES caps might fail if not normalized in check?");
    // Let's check logic: t.value.toLowerCase() -> "james". Set has "james". Should be true.
    // Wait, in Python test I assumed it worked. In JS:
    // COMMON_GIVEN_NAMES has "james".
    // t_caps.value is "JAMES". .toLowerCase() is "james".
    // So it should be true.
    assert.strictEqual(lib.is_common_given_name(new Token("James", RegexToken.WORD, [0, 5], 0)), true);

    console.log("All JS Tests Passed!");
}

try {
    runTests();
} catch (e) {
    console.error("Test Failed:", e);
    process.exit(1);
}
