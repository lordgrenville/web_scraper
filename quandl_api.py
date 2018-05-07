"""quandl api querier"""
import quandl
import requests
import json
# quandl.ApiConfig.api_key = "G8yT1Es4LcyARrmBzP8g"  # not always needed
quandl.ApiConfig.api_version = '2015-04-09'


def ticker_query(company):
    """query yahoo API to get ticker from company name"""
    converter = \
        'http://d.yimg.com/autoc.finance.yahoo.com/autoc?query=%s&lang=en' \
        % company
    req = requests.get(converter, headers={'User-Agent': 'Mozilla/5.0'})
    nice_data = json.loads(req.text)
    try:
        ticker = nice_data['ResultSet']['Result'][0]['symbol']
    except IndexError:
        ticker = None
    return ticker


def stock_lookup(ticker):
    """hit quandl API with ticker, get 1st row of data"""
    try:
        mydata = quandl.get("WIKI/%s" % ticker, rows=1)
        return mydata.iloc[0]
    except (RuntimeError, ValueError):
        return None


if __name__ == '__main__':
    pass
