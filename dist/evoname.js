/**
 * evoname - Generated Parser
 * Transpiled from Python GP Tree
 */
const lib = require('../library');

function parse(raw_input) {
    // The evolved tree expects 'raw_input' as argument
    return lib.set_confidence(lib.make_name_obj(lib.EMPTY_STR, lib.extract_given_str(lib.tokenize(raw_input)), lib.extract_family_str(lib.drop_first(lib.remove_type(lib.tokenize(raw_input), lib.identity_token_type(lib.RegexToken.SALUTATION)))), lib.split_on_comma(lib.EMPTY_STR), lib.extract_title_list(lib.tokenize(raw_input)), lib.get_last_string(lib.split_on_comma(lib.extract_given_str(lib.EMPTY_TOK_LIST))), lib.Gender.MALE, lib.split_on_comma(lib.trim(lib.EMPTY_STR)), lib.extract_title_list(lib.EMPTY_TOK_LIST)), 0.57);
}

module.exports = parse;
