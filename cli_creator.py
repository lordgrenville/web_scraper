"""click wrapper - master function"""
import click
from job_scraper import *
import sys  # for debugging purposes


@click.command()
def run_scraper():
    """running the scraper"""
    soup = scrape_secret()
    jobs = clean_jobs(soup)
    result = organise(jobs)
    raw_data = data_cleanser(result)
    listings, tickers = enrich_data(raw_data)
    listing_tuples = tuple_conversion(listings)
    update_db(listing_tuples)


if __name__ == '__main__':
    # run_scraper()
    run_scraper(sys.argv[1:])  # for debugging
