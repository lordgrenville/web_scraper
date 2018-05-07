"""nyt api querier"""
from nytimesarticle import articleAPI
import time

API_KEY = '470544558ed84462bf9a0a74c837fbce'
test_tuple = (u'Sales Administrator', u'Tufin', u'Tel Aviv/ Ramat Gan',
              u'1 Full-time', 'datetime.datetime(2018, 5, 3, 0, 0)')
new_result = (test_tuple,)


def api_query(topics):
    """hits the NYT API"""
    api = articleAPI(API_KEY)
    for x in topics:
        articles = api.search(x[1])
        time.sleep(2)
        return articles


if __name__ == '__main__':
    # print api_query(new_result)
    # just for testing!
    api = articleAPI(API_KEY)
    # print api.search(q='blockchain')
    try:
        h = api.search(q='Tufin')
        print h
    except ValueError:
        print 'No data found'
