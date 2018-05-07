"""click wrapper - master function"""
import click
from job_scraper import *
import quandl_api
import sys  # for debugging purposes


@click.command()
def run_scraper():
    """running the scraper"""
    soup = scrape_secret()
    jobs = clean_jobs(soup)
    result = organise(jobs)
    production_data = data_cleanser(result)

    # enriching through an API
    tickers = {}
    for item in production_data:
        name = item[1]  # company is in position 1
        ticker = quandl_api.ticker_query(name)
        if ticker is not None:
            item.append(True)
            if ticker not in tickers.keys():
                stock_data = quandl_api.stock_lookup(name)
                if stock_data is not None:
                    tickers[ticker] = stock_data
        else:
            item.append(False)

    update_db(production_data)
    print tickers

if __name__ == '__main__':
    # run_scraper()
    run_scraper(sys.argv[1:])  # for debugging
