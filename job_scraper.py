"""
library of functions for job scraper
"""
import requests
import mysql.connector
import time
import datetime

import bs4
from dateutil import parser
import quandl_api

"""
Scrapes Secret Tel Aviv jobs board, adds new jobs into a database
"""

JOBS_COLS = ['Title', 'Company', 'Location', 'Type', 'Date_Posted', 'Public']
COMPANY_COLS = ['ticker', 'day', 'day_open', 'high', 'low', 'day_close',
                'volume', 'ex_dividend', 'split_ratio', 'adj_open', 'adj_high',
                'adj_low', 'adj_close', 'adj_volume']


def remove_value_from_list(the_list, val):
    """
    removes multiple occurrences of a given term
    """
    return [value for value in the_list if value != val]


def length_enforcer(the_list, length):
    """
    remove from list of tuples those which go above a given length
    """
    return [value for value in the_list if len(value) == length]


def scrape_secret():
    """
    hit the website and scrape the first page
    """
    url = "https://jobs.secrettelaviv.com/"
    req = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    page = req.text

    # jobs are in spans
    parse_only = bs4.SoupStrainer('span')
    return bs4.BeautifulSoup(page, "lxml", parse_only=parse_only)


def clean_jobs(soup):
    """
    tidy the data - first steps
    """
    jobs = [span.get_text().strip() for span in soup.findChildren()]
    # remove extraneous elements
    rem_list = ['',
                'Subscribe to our EVENTS Newsletter',
                'Join our facebook GROUP']
    for removal_string in rem_list:
        jobs.remove(removal_string)
    jobs = remove_value_from_list(jobs, '')
    return remove_value_from_list(jobs, 'new')


def organise(jobs):
    """
    make list of lists
    """
    result = []
    new_list = []
    for job in jobs:
        if len(new_list) == 7:
            a = list(new_list)
            result.append(a)
            new_list = [job]
        else:
            new_list.append(job)
    result.append(new_list)
    return length_enforcer(result, 7)


def data_cleanser(result):
    """
    complete data cleaning, add headers
    """
    for i in result:
        del i[1]
        del i[2]
        try:
            i[4] = parser.parse(i[4])
        except ValueError:
            pass

    # delete last record - it's not a job
    try:
        del result[100]
    except IndexError:
        pass
    return result


def formulate_insertion(table_name, column_list):
    """make well-formed MySQL insertion"""
    insertion = "INSERT INTO " + table_name + " (" + ", ".join(column_list) +\
                ") VALUES " + "(" + "%s," * (len(column_list) - 1) + "%s)"
    return insertion


def enrich_data(raw_data):
    """enriching through an API"""
    tickers = {}
    for item in raw_data:
        name = item[1]  # company is in position 1

        ticker = quandl_api.ticker_query(name)
        if ticker is not None:
            item.append(True)
            if ticker not in tickers.keys():
                stock_data = quandl_api.stock_lookup(ticker)
                if stock_data is not None:
                    tickers[ticker] = stock_data
        else:
            item.append(False)
    return raw_data, tickers


def tuple_conversion(listings):
    """convert into tuples (for sql import)"""
    return [tuple(l) for l in listings]


def prevent_job_duplicates(old, new):
    """remove results already in table"""
    current_by_unique_id = [row for row in old]

    new_by_unique_id = list((a[0], a[1]) for a in new)
    to_add = []
    for index, elem in enumerate(new_by_unique_id):
        if elem not in current_by_unique_id:
            to_add.append(new[index])
    return new


def update_db(listing_tuples):
    """
    moves the data to a permanent record
    """
    username = 'root'
    password = 'root'
    con = mysql.connector.connect(user=username, password=password,
                                  database='jobs')
    cursor = con.cursor()

    # before inserting, we'll check the records aren't in here already
    cursor.execute("""SELECT distinct Title, Company from jobs;""")
    to_add = prevent_job_duplicates(cursor, listing_tuples)
    insertion = formulate_insertion("jobs", JOBS_COLS)

    # add new tickers
    cursor.execute("""SELECT distinct ticker from company_names;""")
    tickers = [x[0] for x in cursor]
    for listing in listing_tuples:
        company_ticker = quandl_api.ticker_query(listing[1])
        if company_ticker not in tickers and company_ticker is not None:
            print "New public company - add to table"
            print company_ticker

    # check if stocks updated today
    stock_already_updated = True
    cursor.execute("""SELECT day FROM companies ORDER BY day DESC LIMIT 1;;""")
    for x in cursor:
        if x[0] == datetime.date.today():
            pass
        else:
            stock_already_updated = False
            # get company names and check stock prices
            cursor.execute("""SELECT distinct ticker from company_names;""")
            stock_tuples = []
            for x in cursor:
                quote = [x[0], time.strftime('%Y-%m-%d')]
                if quandl_api.stock_lookup(x) is not None:
                    quote.extend(quandl_api.stock_lookup(x).tolist())
                    stock_tuples.append(tuple(quote))

            stock_insertion = formulate_insertion("companies", COMPANY_COLS)

    try:
        cursor.executemany(insertion, to_add)
        if not stock_already_updated:
            cursor.executemany(stock_insertion, stock_tuples)
        con.commit()
    except Exception as e:
        print e
        con.rollback()
        con.close()
