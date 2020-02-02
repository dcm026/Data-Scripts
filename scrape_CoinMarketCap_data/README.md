# Scrape_CoinMarketCap_Data

I wanted to test out data from CoinMarketCap (CMC) on cryptocurrencies on Binance and Bittrex exchange to test out trading strategies.

Grabs historical data from coinmarketcap.com by scraping one crypto at a time according to the csv, where the startpoint is when it 
was first listed on the exchange to avoid bias.

The get_current_day_data() fx parses the page on CMC that shows the current price of every crypto. This can be ran multiple times a day 
for higher resolution data throughout the day or just ran once a day to have up to date end of day data (which would lack accurate 
intraday measurements such as high and low prices). 

A delay of 10s is included between historical data requests to respect CMC’s wishes.
