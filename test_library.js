const lib = require('./library');

function assert(condition, message) {
    if (!condition) {
        throw new Error(message || "Assertion failed");
    }
}

function test_tokenize() {
    console.log("Testing tokenize...");
    const raw = "Dr. Hans Müller";
    const tokens = lib.tokenize(raw, "de");

    console.log("Tokens:", tokens);

    assert(tokens.length === 3, "Should have 3 tokens");
    assert(tokens[0].value === "Dr.", "First token should be Dr.");
    assert(tokens[0].type === lib.RegexToken.TITLE, "First token should be TITLE");
    assert(tokens[1].value === "Hans", "Second token should be Hans");
    assert(tokens[2].value === "Müller", "Third token should be Müller");
}

function test_macro_primitives() {
    console.log("Testing macro primitives...");
    const raw = "Herr Dr. Hans Müller";
    const tokens = lib.tokenize(raw, "de");

    const salutation = lib.extract_salutation_str(tokens);
    assert(salutation === "Herr", "Salutation should be Herr");

    const titles = lib.extract_title_list(tokens);
    assert(titles.length === 1, "Should have 1 title");
    assert(titles[0] === "Dr.", "Title should be Dr.");

    const given = lib.extract_given_str(tokens);
    assert(given === "Hans", "Given name should be Hans");

    const family = lib.extract_family_str(tokens);
    assert(family === "Müller", "Family name should be Müller");
}

function test_make_name_obj() {
    console.log("Testing make_name_obj...");
    const obj = lib.make_name_obj("raw", "Hans", "Müller", [], ["Dr."], "Herr", lib.Gender.MALE, [], []);

    assert(obj.given === "Hans");
    assert(obj.family === "Müller");
    assert(obj.title[0] === "Dr.");
    assert(obj.gender === lib.Gender.MALE);
}

function main() {
    try {
        test_tokenize();
        test_macro_primitives();
        test_make_name_obj();
        console.log("All tests passed!");
    } catch (e) {
        console.error("Test failed:", e);
        process.exit(1);
    }
}

main();
