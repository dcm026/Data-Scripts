
import time
import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup
from scrapy import Selector
import re
from time import strptime


def save_csv(text, fileName, folderName='', header=False, write_append='w'):
    import pandas as pd
    if folderName[-1:] != '\\' and len(folderName) > 0 and folderName[-4:] != '.csv':
        folderName += '\\'
    filePath = str(folderName) + str(fileName) + '.csv'
    if folderName[-4:] == '.csv':
        filePath = folderName
    else:
        import os
        if not os.path.exists(str(folderName) + "/"):
            os.makedirs(str(folderName) + "/")
    df = pd.DataFrame(text)
    df.to_csv(filePath, index=False, header=header, mode=write_append)

def get_html_recur(ticker, url, attempt):
    if attempt == 3:
        print('could not get data for', ticker)
        return -1
    try:
        response = urlopen(url, timeout=12)
        html = response.read()
        response.close()
        print('success')
        return html
    except:
        time.sleep(15)
        print('failed to get data for', ticker, ' trying again')
        return get_html_recur(ticker, url, (attempt + 1))

def get_historical_data():
    # load cryptos from csv which we want price data on
    df_desiredCryptos = pd.read_csv('Crypto List.csv')
    cmcNames = list(df_desiredCryptos['cmcName'])
    tickers = list(df_desiredCryptos['Ticker'])
    startDates = list(df_desiredCryptos['StartDate'])
    failed = [] #
    mat = [['Ticker', 'Date(YMD)', 'Open', 'High', 'Low', 'Close', 'Vol', 'MktCap']]

    for i in range(len(tickers)):
        ticker = tickers[i]
        name = cmcNames[i]
        time.sleep(5)

        try:
            print('getting data for:', ticker, '  i:', i)
            startDate = '20' + str(startDates[i])
            endDate = time.strftime('%Y%m%d') # current date in yyyymmdd format as endpoint
            url = 'https://coinmarketcap.com/currencies/' + str(name) + '/historical-data/?start=' + str(startDate) + '&end=' + str(endDate)  # url for getting current price for every coin
            html = get_html_recur(ticker, url, attempt=0)
            if html == -1:
                failed.append(ticker)
                continue
            soup = BeautifulSoup(html, features="html.parser")
            table = soup.find('tbody') # format changed from table to tbody as of 6/26/2019
            for tr in table.find_all('tr'):
                row = [td.text for td in tr.find_all('td')]
                try:
                    if len(row) == 0:
                        continue
                    date = str(row[0]).replace(',', '').split(' ') # 'Jun 04, 2019' -> ['Jun', '04', '2019']
                    month = str(strptime(date[0], '%b').tm_mon) # 'Jun' -> '6'
                    month = '0' + month if len(month) < 2 else month
                    yyyymmdd = str(date[2]) + month + str(date[1])
                    vol = int(float(row[5].replace(',', '')))
                    mktCap = row[6].replace(',', '').replace('-', '-1') # if market cap is blank, insert -1
                    mktCap = int(float(mktCap))
                    #           ticker, date      open,   high,   low,    close,
                    mat.append([ticker, yyyymmdd, row[1], row[2], row[3], row[4], vol, mktCap])
                    # print(len(mat), mat)
                except Exception as e:
                    print('error @ ', ticker, 'error: ', e)
        except Exception as e:
            print('error @ ', ticker, 'error: ', e)
            failed.append(ticker)
        save_csv(mat, fileName=('historicalData' + str(time.strftime('%Y%m%d'))), folderName='CMCdata', header=False, write_append='a')
        mat = []
        time.sleep(10)
    print('Failed to get data for coins: ', failed)

def get_current_day_data():
    print('getting data for current day')
    # load cryptos from csv which we want price data on
    df_desiredCryptos = pd.read_csv('Crypto List.csv')
    desiredCryptos = list(df_desiredCryptos['Ticker'])

    url = 'https://coinmarketcap.com/all/views/all/' # url for getting current price for every coin
    html = get_html_recur('get_current_day_data', url, attempt=0)
    if html == -1:
        return
    soup = BeautifulSoup(html, features="html.parser")

    mat = [['Ticker', 'YMD', 'Price', 'Vol', 'MktCap']]

    sel = Selector(text=soup.prettify())
    coins = sel.xpath("//tr[contains(@id, 'id-')]").extract()
    date = time.strftime('%Y%m%d') # current date in yyyymmdd format

    for coin in coins:
        try:
            soup = BeautifulSoup(coin, features='html.parser')
            sel = Selector(text=soup.prettify())

            ticker = sel.xpath("//td[contains(@class, 'col-symbol')]/text()").extract_first()
            ticker = re.sub(r'\W', '', ticker) # remove all spaces, newlines, & tabs
            if ticker not in desiredCryptos and ticker != 'BTC':
                continue
            price = sel.xpath("//a[@class='price']/@data-usd").extract_first()
            volume = sel.xpath("//a[@class='volume']/@data-usd").extract_first()
            volume = int(float(volume))
            mktCap = sel.xpath("//td[contains(@class, 'market-cap')]/@data-usd").extract_first()
            mktCap = -1 if str(mktCap) == '?' else int(float(mktCap))

            row = [ticker, date, price, volume, mktCap]
            mat.append(row)
        except Exception as e:
            print(e)
    save_csv(mat, fileName=str(time.strftime("%Y%m%d%H%M%S")), folderName='CMCdata')

if __name__ == '__main__':
    '''Get price data for this current moment'''
    get_current_day_data()

    '''Get historical price data'''
    get_historical_data()

