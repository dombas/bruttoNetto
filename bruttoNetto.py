from queue import Queue, Empty

import matplotlib.pyplot as plt
import numpy as np
import scrapy
import sys
from scrapy.crawler import CrawlerProcess


class EarningsSpider(scrapy.Spider):
    """
    A class for crawling the salary calculator on wynagrodzenia.pl

    Attributes
    ----------
    earnings : str OR int OR float
        earnings to input into the calculator
    queue : Queue
        results will be put into this queue
    user_input :

    Methods
    -------
    parse(response)
        Returns a scrapy.FormRequest and sets self.parse_results as callback

    parse_results(response)
        Extracts the calculated salary from html, cleans it and puts a [earnings, salary] into the queue.
    """

    name = 'wynagrodzenia.pl'
    start_urls = ['https://wynagrodzenia.pl/kalkulator-wynagrodzen/']

    def __init__(self, input_tuple, queue, name=None, **kwargs):
        """
        Parameters
        ----------
        input_tuple : (str, str or int or float)
            original user input and cleaned earnings to input into the calculator
        queue : Queue
            results will be put into this queue
        """
        super().__init__(name, **kwargs)
        self.user_input = str(input_tuple[0])
        self.earnings = str(input_tuple[1])
        self.queue = queue
        # form data that will be later sent
        self.post_data = {
            'sedlak_calculator[earnings]': self.earnings,
            'sedlak_calculator[selfEmployer]': '1',
            'sedlak_calculator[rentAndAnnuityCost]': '1',
            'sedlak_calculator[sicknesCost]': '1',
            'sedlak_calculator[healthCost]': '1',
            'sedlak_calculator[FPCost]': '1',
            'sedlak_calculator[FGSPCost]': '1',
            'sedlak_calculator[accidentPercent]': '1.67',
            'sedlak_calculator[end26Year]': '1',
            'sedlak_calculator[employeePercent]': '2',
            'sedlak_calculator[employerPercent]': '1.5',
            'sedlak_calculator[octoberIncome]': '1',
            'sedlak_calculator[businessExpenses]': '0',
            'work_accidentPercent': '1.67',
            'nonwork_accidentPercent': '1.67',
            'sedlak_calculator[contractType]': 'work',
            'sedlak_calculator[calculateWay]': 'gross',
            'sedlak_calculator[year]': '2019',
            'sedlak_calculator[mandateModels]': 'otherCompany',
            'sedlak_calculator[theSameCity]': '1',
            'sedlak_calculator[freeCost]': '1',
            'sedlak_calculator[constantEarnings]': '1',
        }
        for month_number in range(12):
            post_data_key = 'sedlak_calculator[monthlyEarnings][{}]'.format(month_number)
            self.post_data[post_data_key] = self.earnings

    def parse(self, response):
        """Overrides the scrapy.Spider parsing

        Parameters
        ----------
        response : scrapy.http.Response
            Response to parse

        Returns
        -------
        scrapy.FormRequest
            form request, filled from response and post_data
        """
        # the form has a hidden field with a token, so we're actually submitting the form
        # (instead of simply using requests and a POST request)
        return scrapy.FormRequest.from_response(response,
                                                formname='sedlak_calculator',
                                                formdata=self.post_data,
                                                callback=self.parse_results)

    def parse_results(self, response):
        """Callback for the form response

        Parameters
        ----------
        response : scrapy.http.Response
            Response to parse

        """
        salary_div = response.css('div.count-salary')
        spans_in_salary_div = salary_div.css('span::text')
        # get first span, it contains the text we're interested in
        salary = spans_in_salary_div.get()
        # extract only digits from salary
        salary = clean_money_string(salary)
        # send the results through a queue
        self.queue.put((self.earnings, salary, self.user_input))


def clean_money_string(earnings):
    """Clean the earnings string

    Change comma to dot(will convert to float), leave only numbers and dot

    Parameters
    ----------
    earnings : str
        The string representation of earnings to clean

    Returns
    -------
    str
        cleaned earnings string

    """
    # if there's a comma, change it to a dot
    earnings = earnings.replace(',', '.')
    # remove all characters except numbers and dots
    earnings = ''.join(list(filter(lambda x: str.isdigit(x) or '.' == x, earnings)))
    return earnings


class EarningsCalculator:
    """
    A class for converting a list of earnings into salary, using EarningsSpider as crawlers.

    Attributes
    ----------
    earnings_list : list of str
        a list of earnings to convert

    Methods
    -------
    add_earnings(earnings)
        Cleans earnings and adds to earnings_list
    get_salary()
        Converts the earnings_list to salary, returns an iterable
    """

    def __init__(self):
        self.inputs_list = list()

    def add_earnings(self, earnings):
        """Cleans earnings and adds to earnings_list
        Parameters
        ----------
        earnings : str or int or float
            earnings to add to the list
        """
        cleaned_earnings = clean_money_string(earnings)
        self.inputs_list.append((earnings, cleaned_earnings))

    # iterable
    # results are a list like this:
    # [(cleaned input, calculated, original input),...]
    # example:
    # [(2000, 1500, '2000'),
    # (3000, 2500, '3000 zł')]
    def get_salary(self):
        """Converts the earnings_list to salary, returns an iterable
        Runs a spider for each earning in the list, returns results an iterable
        Will wait up to 10 seconds for each spider.

        Returns
        -------
        iterable
            Each result will be returned using yield.
            A single result is of format [earnings : str, salary : str]

        """
        earnings_count = len(self.inputs_list)
        assert earnings_count > 0, 'no earnings to convert'
        # queue for receiving data from spiders
        queue = Queue(maxsize=earnings_count)
        process = CrawlerProcess(settings={
            'FEED_FORMAT': 'json',
            'FEED_URI': 'items.json',
            'LOG_FILE': 'scrapy.log'
        })
        # add a spider for each earning to convert
        for input_tuple in self.inputs_list:
            process.crawl(EarningsSpider, input_tuple=input_tuple, queue=queue)
        process.start()

        # wait for results from spiders
        waiting_for_results_count = earnings_count
        while waiting_for_results_count > 0:
            try:
                result = queue.get(block=True, timeout=10)
            except Empty:
                result = 'timeout'
            waiting_for_results_count -= 1
            yield result


def display_graph(results):
    """Displays a bar graph of EarningsCalculator results

    Parameters
    ----------
    results : list of list of str
        a list of [earnings, salary] to plot
    """
    height = list()
    y_pos = list()
    for result in results:
        # if the result did not timeout (it will be a string otherwise)
        if isinstance(result, (tuple, list)):
            brutto = float(result[1])
            netto = float(result[0])
            height.append(brutto)
            y_pos.append(netto)
    if len(height) == 0:
        # probably all crawlers timed out
        raise ValueError('No data for graph.')
    if len(results) == 1:
        plt.bar(y_pos, height)
    else:
        bar_width = np.min(np.diff(np.sort(y_pos))) * 0.9
        plt.bar(y_pos, height, width=bar_width)
    plt.title('Zarobki brutto do netto')
    plt.xlabel('Brutto')
    plt.ylabel('Netto')

    plt.xticks(y_pos, rotation=45)
    plt.subplots_adjust(bottom=0.15, top=0.95)
    plt.show()


def main():
    earnings_calculator = EarningsCalculator()
    arguments_count = len(sys.argv) - 1
    if arguments_count == 0:
        print('Please provide at least one argument')
        return
    for argument in sys.argv[1:]:
        earnings_calculator.add_earnings(argument)

    # print results
    print('[brutto, netto]')
    results_list = list()
    for result in earnings_calculator.get_salary():
        results_list.append(result)
        print(result)

    # display graph
    try:
        display_graph(results_list)
    except ValueError as error:
        print('Can\'t display graph: ' + str(error))


if __name__ == '__main__':
    main()

