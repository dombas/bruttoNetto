import scrapy, sys
import matplotlib.pyplot as plt
import numpy as np
from scrapy.crawler import CrawlerProcess
from queue import Queue, Empty


class EarningsSpider(scrapy.Spider):

    def __init__(self, earnings, queue, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.queue = queue
        self.earnings = str(earnings)
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

    name = 'wynagrodzenia.pl'
    start_urls = ['https://wynagrodzenia.pl/kalkulator-wynagrodzen/']

    def parse(self, response):
        with open('form.html', 'wb') as file:
            file.write(response.body)
        # the form has a hidden field with a token, so we're actually submitting the form
        # (instead of simply using requests and a POST request)
        return scrapy.FormRequest.from_response(response,
                                                formname='sedlak_calculator',
                                                formdata=self.post_data,
                                                callback=self.parse_results)

    def parse_results(self, response):
        with open('result.html', 'wb') as file:
            file.write(response.body)
        salary_div = response.css('div.count-salary')
        spans_in_salary_div = salary_div.css('span::text')
        # get first span, it contains the text we're interested in
        salary = spans_in_salary_div.get()
        # extract only digits from salary and cut off the cents
        salary_no_cents = ''.join(list(filter(str.isdigit, salary)))[:-2]
        # send the results through a queue
        self.queue.put([self.earnings, salary_no_cents])


class EarningsCalculator:

    def __init__(self):
        self.earnings_list = list()

    def add_earnings(self, earnings):
        self.earnings_list.append(earnings)

    # iterable
    # results are a list like this:
    # [[2000, 1500],
    # [3000, 2500]]
    def get_salary(self):
        earnings_count = len(self.earnings_list)
        assert earnings_count > 0, 'no earnings to convert'
        # queue for receiving data from spiders
        queue = Queue(maxsize=earnings_count)
        process = CrawlerProcess(settings={
            'FEED_FORMAT': 'json',
            'FEED_URI': 'items.json'
        })
        # add a spider for each earning to convert
        for earning_to_convert in self.earnings_list:
            process.crawl(EarningsSpider, earnings=earning_to_convert, queue=queue)
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
    height = list()
    y_pos = list()
    for result in results:
        # if the result did not timeout (it will be a string otherwise)
        if isinstance(result, list):
            brutto = float(result[1])
            netto = float(result[0])
            height.append(brutto)
            y_pos.append(netto)
    bar_width = np.min(np.diff(np.sort(y_pos))) * 0.9
    plt.bar(y_pos, height, width=bar_width)
    plt.title('Zarobki brutto do netto')
    plt.xlabel('Brutto')
    plt.ylabel('Netto')
    plt.show()


earnings_calculator = EarningsCalculator()
arguments_count = len(sys.argv) - 1
for argument in sys.argv[1:]:
    earnings_calculator.add_earnings(argument)

# print results
print('[brutto, netto]')
results_list = list()
for result in earnings_calculator.get_salary():
    results_list.append(result)
    print(result)

# display graph
display_graph(results_list)
