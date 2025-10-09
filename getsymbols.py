import warnings

warnings.simplefilter(action="ignore")  # , category=FutureWarning)
import pandas as pd

# import yfinance as yf # Unused
import os
from settings import MySetts


# Then use pd.read_html as normal

# https://finance.yahoo.com/markets/etfs/gainers/?start=0&count=250
# https://finance.yahoo.com/markets/etfs/losers/?start=0&count=250
# https://finance.yahoo.com/markets/etfs/best-historical-performance/?start=0&count=250
# https://finance.yahoo.com/markets/etfs/most-active/?start=0&count=250
# active_etfs_url = 'https://finance.yahoo.com/markets/etfs/most-active/?start=1&count=250'
active_etfs_url = "https://finance.yahoo.com/markets/etfs/most-active/?start=1&count=50"
active_stocks_url = (
    "https://finance.yahoo.com/markets/stocks/most-active/?start=1&count=250"
)
trending_stocks_url = "https://finance.yahoo.com/markets/stocks/trending/"
trending_etfs_url = "https://finance.yahoo.com/markets/etfs/trending/"
sp500url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
nsdq100url = "https://en.m.wikipedia.org/wiki/Nasdaq-100"



# to get other info out, we can:
#   filtered_df['fv'] = filtered_df['Volume'].str[:-1].astype(float)
#   filtered_df.fv
def get_symbols(url_name="nsdq100", verbose=False):
    """
    When using yahoo source, the returned symbol contains description.

    Parameters:
    url_name:
        'active|trending etfs'/'active|trending stocks'/'sp500'
    verbose:
        return a df with symbols at 0 and info at 1, otherwise symbols list

        to get a list of symbols:
            sidf[0].tolist()
        to get info for symbol:
            info=sidf.loc[sidf[0]==symbol,1].item()
    """


    if url_name == "nsdq100":
        def list_wikipedia_nasdaq100() -> pd.DataFrame:
            # Ref: https://stackoverflow.com/a/75846060/
            url = 'https://en.m.wikipedia.org/wiki/Nasdaq-100'
            df = pd.read_html(url, attrs={'id': "constituents"}, index_col='Ticker')[0]
            return df.index.tolist()
        return list_wikipedia_nasdaq100()


    match url_name:
        case "active etfs":
            url = active_etfs_url
        case "trending etfs":
            url = trending_etfs_url
        case "active stocks":
            url = active_stocks_url
        case "trending stocks":
            url = trending_stocks_url
        case "sp500":
            url = sp500url
        #case "nsdq100":
        #    url = nsdq100url

    
    mask_str = "Symbol"

    if MySetts.use_proxy:
        os.environ["HTTP_PROXY"] = MySetts.yf_proxy
        os.environ["HTTPS_PROXY"] = MySetts.yfs_proxy
        os.environ["NO_PROXY"] = "localhost,127.0.1"  # Optional: for hosts to bypass proxy

    data_table = pd.read_html(url)
    df = data_table[3] if url_name == "nsdq100" else data_table[0]
    # mask = ~df['Symbol'].str.contains('[.,]', regex=True)
    mask = ~df[mask_str].str.contains("[.,!?]", regex=True)
    filtered_df = df[mask]
    # filtered_df['Info'], filtered_df['Symbol'] = filtered_df['Symbol'], filtered_df['Symbol'].str.split(' ',expand=True)[0]
    sidf = filtered_df["Symbol"].str.split(" ", n=1, expand=True)

    if verbose:
        return sidf
    else:
        tickers = sidf[0].tolist()
        return tickers


if __name__ == '__main__':
    print(f'ns100 = {get_symbols(url_name="nsdq100",verbose=False)}')


# sample of sidf

#        0                                                  1
# 0   YINN           Direxion Daily FTSE China Bull 3X Shares
# 1   NVDL               GraniteShares 2x Long NVDA Daily ETF
# 2    FXI                        iShares China Large-Cap ETF
# 3   KWEB                 KraneShares CSI China Internet ETF
# 4    SLV                               iShares Silver Trust
# 5   YANG           Direxion Daily FTSE China Bear 3X Shares
# 6   SOXL        Direxion Daily Semiconductor Bull 3X Shares
# 7    GLD                                   SPDR Gold Shares
# 8    VWO         Vanguard Emerging Markets Stock Index Fund
# 9   MCHI                             iShares MSCI China ETF
# 10  CWEB   Direxion Daily CSI China Internet Bull 2X Shares
# 11  NVDX              T-Rex 2X Long NVIDIA Daily Target ETF
# 12   AGQ                             ProShares Ultra Silver
# 13   GDX                             VanEck Gold Miners ETF
# 14  BITX                            2x Bitcoin Strategy ETF
# 15   EEM                  iShares MSCI Emerging Markets ETF
# 16  GDXJ                      VanEck Junior Gold Miners ETF
# 17   VOO                               Vanguard S&P 500 ETF
# 18   DIA        SPDR Dow Jones Industrial Average ETF Trust
# 19   SMH                           VanEck Semiconductor ETF
# 20  NVDY           YieldMax NVDA Option Income Strategy ETF
# 21  TQQQ                             ProShares UltraPro QQQ
# 22  QDTE  Roundhill Innovation-100 0DTE Covered Call Str...
# 23  SOXS        Direxion Daily Semiconductor Bear 3X Shares
# 24  NUGT    Direxion Daily Gold Miners Index Bull 2X Shares
