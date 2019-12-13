import scrapy, sys
from scrapy.crawler import CrawlerProcess
from queue import Queue


class EarningsSpider(scrapy.Spider):

    def __init__(self, earnings, queue, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.queue = queue
        self.earnings = str(earnings)
        self.post_data = {
            'sedlak_calculator[earnings]': self.earnings
        }
        for month_number in range(12):
            post_data_key = 'sedlak_calculator[monthlyEarnings][{}]'.format(month_number)
            self.post_data[post_data_key] = self.earnings

    name = 'wynagrodzenia.pl'
    start_urls = ['https://wynagrodzenia.pl/kalkulator-wynagrodzen/']

    def parse(self, response):
        with open('form.html', 'wb') as file:
            file.write(response.body)
        return scrapy.FormRequest.from_response(response,
                                                formname='sedlak_calculator',
                                                formdata=self.post_data,
                                                callback=self.parse_results)

    def parse_results(self, response):
        with open('result.html', 'wb') as file:
            file.write(response.body)
        salary_div = response.css('div.count-salary')
        spans_in_salary_div = salary_div.css('span::text')
        salary = spans_in_salary_div.get()
        # extract only digits from salary and cut off the cents
        salary_no_cents = ''.join(list(filter(str.isdigit, salary)))[:-2]
        self.queue.put([self.earnings, salary_no_cents])


class EarningsCalculator:

    def __init__(self):
        self.earnings_list = list()

    def add_earnings(self, earnings):
        self.earnings_list.append(earnings)

    def get_salary(self):
        earnings_count = len(self.earnings_list)
        assert earnings_count > 0, 'no earnings to convert'
        queue = Queue(maxsize=earnings_count)
        process = CrawlerProcess(settings={
            'FEED_FORMAT': 'json',
            'FEED_URI': 'items.json'
        })
        for earning_to_convert in self.earnings_list:
            process.crawl(EarningsSpider, earnings=earning_to_convert, queue=queue)
        process.start()

        waiting_for_results_count = earnings_count
        while (waiting_for_results_count > 0):
            result = queue.get(block=True, timeout=10)
            waiting_for_results_count -= 1
            yield result


earnings_calculator = EarningsCalculator()
arguments_count = len(sys.argv) - 1
for argument in sys.argv[1:]:
    earnings_calculator.add_earnings(argument)
for result in earnings_calculator.get_salary():
    print(result)
