import unittest

from bruttoNetto import clean_money_string, EarningsCalculator


class FunctionsTestCase(unittest.TestCase):
    def test_clean_money_string(self):
        # (input, expected output)
        test_data = [
            ('4000', '4000'),
            ('2555,44', '2555.44'),
            ('455.111', '455.111'),
            ('1900.', '1900.'),
            ('5555 PLN', '5555'),
            ('2433,22zł', '2433.22'),
        ]
        for tpl in test_data:
            input_value = tpl[0]
            expected_value = tpl[1]
            with self.subTest(input=input_value):
                returned_value = clean_money_string(input_value)
                self.assertEqual(returned_value, expected_value)


class EarningsCalculatorTestCase(unittest.TestCase):
    def testEarningsCalculator(self):
        test_data = {
            '4000': '2907.96',
            '50000': '32637.25',
            '9999.99': '7140.38',
            '2239 PLN': '1666.14',
            '4000,00 zł': '2907.96',
        }
        earnings_calculator = EarningsCalculator()
        for input_data in test_data:
            earnings_calculator.add_earnings(input_data)
        for result_tuple in earnings_calculator.get_salary():
            with self.subTest():
                input_value = result_tuple[2]
                expected_value = test_data[input_value]
                returned_value = result_tuple[1]
                self.assertEqual(returned_value, expected_value)


if __name__ == '__main__':
    unittest.main()
