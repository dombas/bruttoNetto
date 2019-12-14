import unittest
from queue import Queue

from scrapy.crawler import CrawlerProcess

from bruttoNetto import clean_money_string, EarningsCalculator


class FunctionsTestCase(unittest.TestCase):
    def test_clean_money_string(self):
        # (input, expected output)
        test_data = [
            ('4000', '4000'),
            ('2555,44', '2555'),
            ('455.111', '455'),
            ('1900.', '1900'),
            ('5555 PLN', '5555'),
            ('2433,22zł', '2433'),
        ]
        for tpl in test_data:
            with self.subTest():
                input_value = tpl[0]
                expected_value = tpl[1]
                returned_value = clean_money_string(input_value)
                self.assertEqual(returned_value, expected_value)


class EarningsCalculatorTestCase(unittest.TestCase):
    def testEarningsCalculator(self):
        test_data = {
            '4000': '2907',
            '2239': '1666',
            '50000': '32637',
        }
        earnings_calculator = EarningsCalculator()
        for input_data in test_data:
            earnings_calculator.add_earnings(input_data)
        for input_output_tuple in earnings_calculator.get_salary():
            with self.subTest():
                input_value = input_output_tuple[0]
                expected_value = test_data[input_value]
                returned_value = input_output_tuple[1]
                self.assertEqual(returned_value, expected_value)


if __name__ == '__main__':
    unittest.main()
