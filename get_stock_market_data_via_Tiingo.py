
import pandas as pd
from tiingo import TiingoClient
import time
import json
import datetime
from datetime import timedelta
import numpy as np
import matplotlib.pyplot as plt

pd.set_option('display.expand_frame_repr', False)

client = TiingoClient({'api_key': 'insert_API_key_here'})
status = {} # dictionary to keep track of when a ticker was last updated

def p(data=''):
    print(data)

def print_head_tail(df, n=3):
    print(df.head(n))
    print('...')
    print(df.tail(n).to_string(header=False))
    print()

def slp():
    time.sleep(100000)

def load_status():
    global status
    with open('status.json', 'r') as f:
        status = json.load(f)
        f.close()

def save_status():
    with open('status.json', 'w') as f:
        json.dump(status, f)
        f.close()

def clean_data(df):
    # fill in missing gaps by interpolating
    for col in df.columns:
        if col == 'Ticker' or col == 'Date':
            continue
        df[col].interpolate(method='linear', limit_direction='forward', inplace=True)

    # convert to python matrix
    mat = []
    for col in df.columns:
        mat.append(list(df[col]))

    # ensure that there are no negative prices or volumes
    for i in range(2, 7):
        for j in range(len(mat[i])):
            if mat[i][j] < .001:
                mat[i][j] = 0

    for j in range(len(mat[0])):
        # ensure that each Low price is actually the lowest price, set price to open or close if either is lower
        if mat[4][j] > mat[2][j]: mat[4][j] = mat[2][j]
        if mat[4][j] > mat[5][j]: mat[4][j] = mat[5][j]
        # ensure that each High price is actually the lowest price, set price to open or close if either is lower
        if mat[3][j] < mat[2][j]: mat[3][j] = mat[2][j]
        if mat[3][j] < mat[5][j]: mat[3][j] = mat[5][j]

    # transpose the matrix back to standard form
    transposed_mat = []
    for j in range(len(mat[0])):
        row = [mat[i][j] for i in range(len(mat))]
        transposed_mat.append(row)
    return transposed_mat


def get_data(tickers_list, end_dates):
    i, j = -1, 0
    header = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividend']
    if len(status.keys()) < 1:
        df = pd.DataFrame([], columns=header)
        df.to_csv('usa_listed_stocks.csv', mode='a', index=False, header=True)
        df.to_csv('usa_delisted_stocks.csv', mode='a', index=False, header=True)

    for ticker in tickers_list:
        try:
            i += 1
            t0 = time.time()
            start_date = '1999-12-30' if ticker not in status.keys() else status[ticker]
            # skip the current ticker if we already have data that is updated to current date
            if datetime.datetime.strptime(start_date, '%Y-%m-%d').date() - datetime.timedelta(days=1) >= datetime.datetime.now().date():
                print('We already have data for', ticker)
                continue
            j += 1
            end_date = str(datetime.datetime.now().date() + datetime.timedelta(days=1))# format: %Y-%m-%d
            last_listed_date = datetime.datetime.strptime(end_dates[i], '%Y-%m-%d') + datetime.timedelta(days=5)
            if datetime.datetime.now().date() > last_listed_date.date():
                delisted = True
                end_date = last_listed_date
            else:
                delisted = False
            # get daily historical price for a ticker within a date range
            df = pd.DataFrame(client.get_ticker_price(ticker, startDate=start_date, endDate=end_date, frequency='daily'))
            df['Ticker'] = ticker
            del df['high'], df['low'], df['open'], df['close'], df['splitFactor'], df['volume']
            df.rename({'adjClose': 'Close', 'adjHigh': 'High', 'adjLow': 'Low', 'adjOpen': 'Open',
                       'adjVolume': 'Volume', 'date': 'Date', 'divCash': 'Dividend'}, axis=1, inplace=True)
            df = df[header] # change the order of the columns to match the header stated above
            cols = df.columns
            data = clean_data(df)
            df = pd.DataFrame(data, columns=cols)
            df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%dT%H:%M:%S.%fZ')
            print_head_tail(df)
            if j < 2:
                df.plot(x='Date', y='Close')
                plt.show()
            csv_title = 'usa_delisted_stocks.csv' if delisted else 'usa_listed_stocks.csv'
            df.to_csv(csv_title, mode='a', index=False, header=False)

            # save the date when ticker was last udpated to json file
            status[ticker] = str(datetime.datetime.now().date())
            save_status()
            print('Data aquired for', ticker, 'i =', i, 'Time taken:', time.time() - t0, '\n')

        except Exception as e:
            print('Failed to get data for', ticker, ' error:', e)
    save_status()


# get a list of tickers that Tiingo has and get data regarding to the market and start and end date, along with other metrics
tickers_df = pd.DataFrame(client.list_stock_tickers())

# filter out stocks that are only in the US stock markets and ones that have been listed
us_stocks_df = tickers_df[(tickers_df['exchange'] == 'NYSE') | (tickers_df['exchange'] == 'NASDAQ') | (tickers_df['exchange'] == 'AMEX')] # (12764, 6)
us_stocks_df = us_stocks_df[us_stocks_df['startDate'] != ''] # filter out stocks that have not been listed on the exchange -- (9129,6)
us_stocks_df = us_stocks_df[~us_stocks_df.ticker.str.contains('-')] # drop any subsets of tickers (8149,6)
us_stocks_df.reset_index(drop=True, inplace=True)
tickers = list(us_stocks_df['ticker'])
end_dates = list(us_stocks_df['endDate'])


# MAIN
try: load_status()
except: save_status()

# get usa stock market data data
get_data(tickers, end_dates)


