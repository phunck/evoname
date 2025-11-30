const lib = require('./library.js');
const fs = require('fs');

// Mock regex definitions injection
const regexDefs = JSON.parse(fs.readFileSync('regex_definitions.json', 'utf8'));
global.REGEX_DEFINITIONS = regexDefs;

function debug() {
    const raw = "Dr. Paul Boris Hunck";
    console.log(`Input: '${raw}'`);

    // Replicate champion logic:
    // make_name_obj(EMPTY_STR, extract_given_str(drop_first(tokenize(raw_input))), ...)

    const tokens = lib.tokenize(raw);
    console.log("Tokens:", tokens.map(t => t.value));

    const dropped = lib.drop_first(tokens);
    console.log("Dropped:", dropped.map(t => t.value));

    const given = lib.extract_given_str(dropped);
    console.log(`Given: '${given}'`);

    const obj = lib.make_name_obj(
        lib.EMPTY_STR,
        given,
        lib.extract_family_str(tokens),
        lib.EMPTY_STR_LIST,
        lib.extract_title_list(tokens),
        lib.extract_salutation_str(tokens),
        lib.Gender.FEMALE,
        lib.EMPTY_STR_LIST,
        lib.EMPTY_STR_LIST
    );

    console.log("Result raw:", obj.raw);
    console.log("Result given:", obj.given);
}

debug();
