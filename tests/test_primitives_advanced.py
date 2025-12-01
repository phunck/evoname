import unittest
import sys
import os

# Add parent directory to path to allow importing primitive_set
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from primitive_set import (
    Token, RegexToken, TokenList,
    get_tokens_before_comma, get_tokens_after_comma,
    is_all_caps, is_capitalized, is_short,
    is_common_family_name, is_common_given_name
)

class TestAdvancedPrimitives(unittest.TestCase):
    def setUp(self):
        # Create some sample tokens
        # "Doe, John"
        self.t_doe = Token("Doe", RegexToken.WORD, (0, 3), 0)
        self.t_comma = Token(",", RegexToken.PUNCT, (3, 4), 1)
        self.t_john = Token("John", RegexToken.WORD, (5, 9), 2)
        self.tokens_comma = TokenList([self.t_doe, self.t_comma, self.t_john])

        # "JAMES"
        self.t_caps = Token("JAMES", RegexToken.WORD, (0, 5), 0)
        
        # "Dr"
        self.t_short = Token("Dr", RegexToken.TITLE, (0, 2), 0)
        
        # "Müller"
        self.t_mueller = Token("Müller", RegexToken.WORD, (0, 6), 0)
        
        # "Unknown"
        self.t_unknown = Token("Xyzabc", RegexToken.WORD, (0, 6), 0)

    def test_context_primitives(self):
        # Before comma
        before = get_tokens_before_comma(self.tokens_comma)
        self.assertEqual(len(before), 1)
        self.assertEqual(before[0].value, "Doe")

        # After comma
        after = get_tokens_after_comma(self.tokens_comma)
        self.assertEqual(len(after), 1)
        self.assertEqual(after[0].value, "John")
        
        # No comma
        no_comma = TokenList([self.t_doe, self.t_john])
        self.assertEqual(len(get_tokens_before_comma(no_comma)), 2) # Should return all
        self.assertEqual(len(get_tokens_after_comma(no_comma)), 0)  # Should return empty

    def test_boolean_primitives(self):
        # is_all_caps
        self.assertTrue(is_all_caps(self.t_caps))
        self.assertFalse(is_all_caps(self.t_doe))
        
        # is_capitalized
        self.assertTrue(is_capitalized(self.t_doe))
        self.assertFalse(is_capitalized(Token("lower", RegexToken.WORD, (0,5), 0)))
        
        # is_short (<= 3)
        self.assertTrue(is_short(self.t_short)) # "Dr" len 2
        self.assertTrue(is_short(Token("A", RegexToken.INITIAL, (0,1), 0)))
        self.assertFalse(is_short(self.t_john)) # "John" len 4

    def test_lexicon_primitives(self):
        # Family names
        self.assertTrue(is_common_family_name(self.t_mueller)) # "Müller" in list
        self.assertTrue(is_common_family_name(Token("Smith", RegexToken.WORD, (0,5), 0)))
        self.assertFalse(is_common_family_name(self.t_john)) # "John" usually given
        
        # Given names
        self.assertTrue(is_common_given_name(self.t_john))
        self.assertTrue(is_common_given_name(self.t_caps)) # "JAMES" (case insensitive check?)
        # Let's check implementation: t.value.lower() in GENDER_DB
        # GENDER_DB has lowercase keys.
        self.assertTrue(is_common_given_name(Token("James", RegexToken.WORD, (0,5), 0)))
        self.assertFalse(is_common_given_name(self.t_mueller))

if __name__ == '__main__':
    unittest.main()
