"""
library of functions for job scraper
"""
import requests
import mysql.connector

import bs4
from dateutil import parser

"""
Scrapes Secret Tel Aviv jobs board, adds new jobs into a database
"""


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


def update_db(result):
    """
    moves the data to a permanent record
    """
    username = 'root'
    password = 'root'

    # convert nested lists into tuples (for sql import)
    new_result = [tuple(l) for l in result]

    # it's relational DB time!
    con = mysql.connector.connect(user=username, password=password,
                                  database='jobs')
    cursor = con.cursor()

    # before inserting, we'll check the records aren't in here already
    # taking title + company as unique identifiers
    cursor.execute("""SELECT distinct Title, Company from jobs;""")
    current_by_unique_id = [row for row in cursor]

    new_result_by_unique_id = list((a[0], a[1]) for a in new_result)
    to_add = []
    for index, elem in enumerate(new_result_by_unique_id):
        if elem not in current_by_unique_id:
            to_add.append(new_result[index])

    # the injection...
    insertion = """INSERT INTO jobs (Title, Company, Location, Type,
        Date_Posted, Public) VALUES (%s,%s,%s,%s,%s, %s)"""

    try:
        cursor.executemany(insertion, to_add)
        con.commit()
    except Exception as e:
        print e
        con.rollback()
        con.close()
