import scrapy
from scrapy.crawler import CrawlerProcess


class EarningsSpider(scrapy.Spider):

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        earnings = str(kwargs.get('earnings', '5000'))
        self.post_data = {
            'sedlak_calculator[earnings]': earnings
        }
        for month_number in range(12):
            post_data_key = 'sedlak_calculator[monthlyEarnings][{}]'.format(month_number)
            self.post_data[post_data_key] = earnings

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
        return {'salary': salary}


process = CrawlerProcess(settings={
    'FEED_FORMAT': 'json',
    'FEED_URI': 'stdout:'
})
process.crawl(EarningsSpider, earnings='3500')
process.start()
