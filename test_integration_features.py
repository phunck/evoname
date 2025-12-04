import unittest
from primitive_set import tokenize, RegexToken, is_conjunction, Token

class TestIntegrationFeatures(unittest.TestCase):
    def test_conjunction_tokenization(self):
        # Test German
        tokens_de = tokenize("Hans und Franz", locale="de")
        self.assertEqual(len(tokens_de), 3)
        self.assertEqual(tokens_de[1].type, RegexToken.CONJUNCTION)
        self.assertEqual(tokens_de[1].value, "und")

        # Test English
        tokens_en = tokenize("Mr. and Mrs. Smith", locale="en")
        # Mr. (Salutation) and (Conjunction) Mrs. (Salutation) Smith (Word)
        # Note: "Mr." might be Salutation, "and" Conjunction, "Mrs." Salutation, "Smith" Word.
        # Let's check types.
        print(f"Tokens EN: {tokens_en}")
        self.assertEqual(tokens_en[1].type, RegexToken.CONJUNCTION)
        self.assertEqual(tokens_en[1].value, "and")

        # Test Ampersand
        tokens_amp = tokenize("A & B", locale="en")
        self.assertEqual(tokens_amp[1].type, RegexToken.CONJUNCTION)
        self.assertEqual(tokens_amp[1].value, "&")

    def test_is_conjunction_primitive(self):
        t = Token("und", RegexToken.CONJUNCTION, (0, 3))
        self.assertTrue(is_conjunction(t))
        
        t2 = Token("Hans", RegexToken.WORD, (0, 4))
        self.assertFalse(is_conjunction(t2))

    def test_particle_merging(self):
        from primitive_set import merge_particles
        
        # Johann von Goethe
        tokens = tokenize("Johann von Goethe", locale="de")
        print(f"DEBUG TOKENS: {tokens}")
        # [Johann, von, Goethe]
        merged = merge_particles(tokens)
        print(f"DEBUG MERGED: {merged}")
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0].value, "Johann")
        self.assertEqual(merged[1].value, "von Goethe")
        
        # Oscar de la Renta
        tokens2 = tokenize("Oscar de la Renta", locale="en")
        # [Oscar, de, la, Renta]
        merged2 = merge_particles(tokens2)
        self.assertEqual(len(merged2), 2)
        self.assertEqual(merged2[1].value, "de la Renta")
        
        # Vincent van Gogh
        tokens3 = tokenize("Vincent van Gogh", locale="en")
        print(f"DEBUG TOKENS 3: {tokens3}")
        merged3 = merge_particles(tokens3)
        print(f"DEBUG MERGED 3: {merged3}")
        self.assertEqual(merged3[1].value, "van Gogh")

    def test_degree_extraction(self):
        from primitive_set import extract_degree_list
        
        # John Doe, PhD
        tokens = tokenize("John Doe, PhD", locale="en")
        # [John, Doe, ,, PhD]
        # Note: PhD should be TOKEN_DEGREE
        print(f"DEBUG TOKENS DEGREE: {tokens}")
        degrees = extract_degree_list(tokens)
        self.assertEqual(len(degrees), 1)
        self.assertEqual(degrees[0], "PhD")
        
        # Max Mustermann, M.A.
        tokens2 = tokenize("Max Mustermann, M.A.", locale="de")
        print(f"DEBUG TOKENS DEGREE 2: {tokens2}")
        degrees2 = extract_degree_list(tokens2)
        self.assertTrue("M.A." in degrees2)

if __name__ == '__main__':
    unittest.main()
