import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from primitive_set import (
    Token, RegexToken, 
    token_length, is_initial, has_hyphen, has_period, 
    is_roman_numeral, is_particle, is_suffix
)

class TestPrimitivesStats(unittest.TestCase):
    
    def test_token_length(self):
        t = Token("Hello", RegexToken.WORD, (0, 5))
        self.assertEqual(token_length(t), 5)
        self.assertEqual(token_length(None), 0)

    def test_is_initial(self):
        t1 = Token("J.", RegexToken.INITIAL, (0, 2))
        t2 = Token("John", RegexToken.WORD, (0, 4))
        # Case where regex didn't catch it as INITIAL but it looks like one
        t3 = Token("K.", RegexToken.WORD, (0, 2)) 
        
        self.assertTrue(is_initial(t1))
        self.assertFalse(is_initial(t2))
        self.assertTrue(is_initial(t3))

    def test_has_hyphen(self):
        t1 = Token("Hans-Peter", RegexToken.WORD, (0, 10))
        t2 = Token("Hans", RegexToken.WORD, (0, 4))
        self.assertTrue(has_hyphen(t1))
        self.assertFalse(has_hyphen(t2))

    def test_has_period(self):
        t1 = Token("St.", RegexToken.PARTICLE, (0, 3))
        t2 = Token("Saint", RegexToken.WORD, (0, 5))
        self.assertTrue(has_period(t1))
        self.assertFalse(has_period(t2))

    def test_is_roman_numeral(self):
        t1 = Token("III", RegexToken.SUFFIX, (0, 3))
        t2 = Token("iv", RegexToken.SUFFIX, (0, 2)) # lowercase check
        t3 = Token("IV.", RegexToken.SUFFIX, (0, 3)) # with dot
        t4 = Token("Müller", RegexToken.WORD, (0, 6))
        
        self.assertTrue(is_roman_numeral(t1))
        self.assertTrue(is_roman_numeral(t2))
        self.assertTrue(is_roman_numeral(t3))
        self.assertFalse(is_roman_numeral(t4))

    def test_is_particle(self):
        t1 = Token("von", RegexToken.PARTICLE, (0, 3))
        t2 = Token("Müller", RegexToken.WORD, (0, 6))
        self.assertTrue(is_particle(t1))
        self.assertFalse(is_particle(t2))

    def test_is_suffix(self):
        t1 = Token("Jr.", RegexToken.SUFFIX, (0, 3))
        t2 = Token("Müller", RegexToken.WORD, (0, 6))
        self.assertTrue(is_suffix(t1))
        self.assertFalse(is_suffix(t2))

if __name__ == '__main__':
    unittest.main()
