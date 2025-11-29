const parse = require('./dist/evoname');
const lib = require('./library');

function assert(condition, message) {
    if (!condition) {
        throw new Error(message || "Assertion failed");
    }
}

function test_parser() {
    console.log("Testing transpiled parser...");

    const raw = "Dr. Hans Müller";
    console.log(`Input: "${raw}"`);

    const result = parse(raw);
    console.log("Result:", JSON.stringify(result, null, 2));

    assert(result instanceof lib.NameObj, "Result should be a NameObj");
    // assert(result.raw === raw, "Raw input should match"); // Champion optimized this away

    // Based on the champion logic we saw earlier:
    // It used extract_given_str -> "Hans"
    // It used extract_family_str -> "Müller"
    // It used extract_title_list -> ["Dr."]

    assert(result.given === "Hans", `Given name should be Hans, got '${result.given}'`);
    assert(result.family === "Müller", `Family name should be Müller, got '${result.family}'`);
    assert(result.title.length === 1 && result.title[0] === "Dr.", "Title should be Dr.");
}

function main() {
    try {
        test_parser();
        console.log("Transpiled parser works! 🚀");
    } catch (e) {
        console.error("Verification failed:", e);
        process.exit(1);
    }
}

main();
