import unittest

from grocery_system.validation import parse_quantity, parse_price


class InputFormatTests(unittest.TestCase):
    def test_quantities_and_batch_ids(self):
        self.assertEqual(parse_quantity(" 02 "), 2)
        self.assertEqual(parse_quantity("0", minimum=0), 0)
        for invalid in ("1_0", "+1", "-1", "0", "2.0", "1e2", ""):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_quantity(invalid)

    def test_rm_amounts(self):
        for text, sen in [("100", 10000), ("100.0", 10000), ("100.00", 10000),
                          ("0.01", 1), ("99999.00", 9999900)]:
            self.assertEqual(parse_price(text), sen)
        for invalid in ("1e2", "1_00", "7.501", "0", "99999.01", "NaN", "+2", ""):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_price(invalid)
