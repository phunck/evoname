import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from primitive_set import NameObj, StringList
from post_processor import repair_name_object

class TestPostProcessor(unittest.TestCase):
    def test_repair_2words_no_title(self):
        # Case 1: "John Doe" -> Should be repaired
        obj = NameObj(raw="John Doe")
        # Simulate model failure (e.g. everything in given)
        obj.given = "John Doe"
        obj.family = ""
        
        repaired = repair_name_object(obj)
        self.assertEqual(repaired.given, "John")
        self.assertEqual(repaired.family, "Doe")
        self.assertEqual(len(repaired.middle), 0)

    def test_no_repair_with_title(self):
        # Case 2: "Dr. Doe" -> Should NOT be repaired if title is present
        obj = NameObj(raw="Dr. Doe")
        obj.title = StringList(["Dr."])
        obj.family = "Doe"
        
        repaired = repair_name_object(obj)
        # Should remain as is (or at least not forced to "Dr" "Doe")
        self.assertEqual(repaired.family, "Doe")
        self.assertNotEqual(repaired.given, "Dr.") 

    def test_no_repair_3words(self):
        # Case 3: "John Paul Doe" -> Should NOT be repaired
        obj = NameObj(raw="John Paul Doe")
        obj.given = "John Paul"
        obj.family = "Doe"
        
        repaired = repair_name_object(obj)
        self.assertEqual(repaired.given, "John Paul")
        self.assertEqual(repaired.family, "Doe")

    def test_no_repair_1word(self):
        # Case 4: "Müller" -> Should NOT be repaired
        obj = NameObj(raw="Müller")
        obj.family = "Müller"
        
        repaired = repair_name_object(obj)
        self.assertEqual(repaired.family, "Müller")
        self.assertEqual(repaired.given, "")

if __name__ == '__main__':
    unittest.main()
