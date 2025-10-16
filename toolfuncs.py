"""
# [yf](https://pypi.org/project/yfinance/)
# info:
[
    'phone', 'longBusinessSummary', 'maxAge', 'priceHint', 'previousClose', 'open', 'dayLow', 'dayHigh', 
    'regularMarketPreviousClose', 'regularMarketOpen', 'regularMarketDayLow', 'regularMarketDayHigh', 
    'trailingPE','volume', 'regularMarketVolume', 'averageVolume', 'averageVolume10days', 
    'averageDailyVolume10Day','bid', 'ask', 'bidSize', 'askSize', 'yield', 'totalAssets',
    'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'fiftyDayAverage', 'twoHundredDayAverage', 'navPrice', 'currency', 
    'category', 'ytdReturn', 'fundFamily', 'fundInceptionDate', 'legalType', 'exchange', 'quoteType', 
    'symbol', 'underlyingSymbol', 'shortName', 'longName', 'firstTradeDateEpochUtc', 'timeZoneFullName', 
    'timeZoneShortName', 'uuid', 'messageBoardId', 'gmtOffSetMilliseconds', 'trailingPegRatio'
 ]
"""
# [yfinance readme](https://github.com/ranaroussi/yfinance?tab=readme-ov-file#logging)
import yfinance as yf

import warnings
from settings import MySetts
if MySetts.use_proxy:
    yf_proxy = MySetts.yf_proxy
    yf.set_config(proxy=yf_proxy)
    warnings.warn(f'proxy setting to {yf_proxy} for {yf.YfData}',stacklevel=4)

warnings.simplefilter(action='ignore') #, category=FutureWarning)
import pandas as pd
import numpy as np

import pandas_ta as ta
from pandas_ta.overlap import rma
from pandas_ta.utils import non_zero_range #, verify_series # verify_series is unused

remain_bars = MySetts.remain_bars
period = MySetts.period
interval = MySetts.interval
hourly = MySetts.hourly

sma_bars = [7]#[7,14,30,60,140,300,500]
sma_names = ['sma7'] #['sma7','sma14','sma30','sma60','sma140','sma300','sma500'] #'bbm'
##################### Data ######################



hrow_max = MySetts.hrow_max 


###############################################################

# yahoo data trailingPE is not always correct, there are even pe values in 
# some ETFs which are definately wrong
def get_pe(symbol):
    ticker = yf.Ticker(symbol.upper())
    #print(f'DEBUGYF: {symbol} info: {len(ticker.info.keys())}')
    ticker_info = ticker.info
    # Extracting P/E Ratio
    pe = 'trailingPE'
    if ticker_info.__contains__(pe):
        pe_ratio = float(ticker_info[pe])
        # Extracting Debt-to-Equity Ratio
        #de_ratio = ticker_info['debtToEquity']
        #print(f"P/E Ratio: {pe_ratio}, Debt-to-Equity Ratio: {de_ratio}")
    else:
        pe_ratio = 0
    #print(f'***** debug get pe {symbol} {pe_ratio}')
    return pe_ratio



def dfs_for_interval(interval,symbols,withInfo=False): 
    period=MySetts.get_period(interval)
    tickers=symbols
    tickers = [ticker.upper() for ticker in tickers]
    len_t = len(tickers)
    if len_t == 0:
        return None
    elif len_t == 1:
        tickers.append('SHLD')

    if (interval in ['1d','1wk']) and ('y' not in period):
        period = 'max'#'5y'

    alldata = yf.Tickers(tickers)
    # get info: alldata.tickers[symbole].info
    dfs = alldata.history(
        period,
        interval,
        prepost=True, # oth data
        actions=False, # dividents data
        group_by='ticker',
        progress=False,
        rounding=True # round(x,2)
    )
    if withInfo:
        return dfs, alldata
    else:
        return dfs, None


def tidy_yf_df(df):
    df = df.copy()
    df.dropna(inplace=True)
    # change columns to lowercase
    df.columns = df.columns.str.lower()
    # print(f'DEBUG: df.columns.str.lower() -> {df.columns}')
    # rename index 'Datetime' to lowercase
    lowered = 'datetime'
    df.index.names = [lowered]
    df.index = pd.to_datetime(df.index)
    return df

    # try:
    #     lowered = df.index.name.lower()
    # except Exception as e:
    #     #print(f'*** debug df.columns: {df.columns} str: {df.columns.str}')
    #     print(f'*** tidy yf_df.index {df.index} name {df.index.name}: {e}')
    #     df.index = pd.to_datetime(df.index)
    
    # else:
    #     print(f'*** tidy yf_df.index name {df.index.name}')
    #     df.index.names = [lowered]
    #     df.index = pd.to_datetime(df.index)
    # return df



def get_any_df(symbol,fully=True,period=period,interval=interval,withInfo=False):
    symbol = symbol.upper()
    raw_df, info = get_df_from_yf(symbol,period,interval,withInfo=withInfo)
    df = tidy_yf_df(raw_df)
    df = predicted(df,interval,fully)
    if withInfo:
        return df, info
    else:
        return df 



def elevate_yf_df(raw_df,interval,fully=True):
    # we may do other predicts later on
    raw_df = tidy_yf_df(raw_df)
    df = predicted(raw_df,interval,fully)
    return df



def tidy_df_from_yf(symbol,period,interval):
    raw_df, info = get_df_from_yf(symbol,period,interval,withInfo=False)
    df = tidy_yf_df(raw_df)
    return df



# Get dataframe from yfinance
def get_df_from_yf(symbol,period,interval,withInfo=False):
    """
    def history(self, period="1mo", interval="1d",
            start=None, end=None, prepost=False, actions=True,
            auto_adjust=True, back_adjust=False,
            proxy=None, rounding=False, tz=None, timeout=None, **kwargs):
    :Parameters:
        period : str
            Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            Either Use period parameter or use start and end
        interval : str
            Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            Intraday data cannot extend last 60 days
        start: str
            Download start date string (YYYY-MM-DD) or _datetime.
            Default is 1900-01-01
        end: str
            Download end date string (YYYY-MM-DD) or _datetime.
            Default is now
        prepost : bool
            Include Pre and Post market data in results?
            Default is False
        auto_adjust: bool
            Adjust all OHLC automatically? Default is True
        back_adjust: bool
            Back-adjusted data to mimic true historical prices
        proxy: str
            Optional. Proxy server URL scheme. Default is None
        rounding: bool
            Round values to 2 decimal places?
            Optional. Default is False = precision suggested by Yahoo!
        tz: str
            Optional timezone locale for dates.
            (default data is returned as non-localized dates)
        timeout: None or float
            If not None stops waiting for a response after given number of
            seconds. (Can also be a fraction of a second e.g. 0.01)
            Default is None.
        **kwargs: dict
            debug: bool
                Optional. If passed as False, will suppress
                error message printing to console.
    """

    data = yf.Ticker(symbol)
    df = data.history(
        period,
        interval,
        prepost=True, # oth data
        actions=False, # dividents data
        rounding=True # round(x,2)
    )

    info = None
    if withInfo: # Only try to get .info if withInfo is True
        try:
            # Accessing .info can sometimes fail for certain tickers or if data is unavailable
            info = data.info
            # Further check for the specific yfinance structure that caused TypeError
            # The error was: if quote in result and len(result[quote]["result"]) > 0:
            # This structure comes from yfinance internal _quote.info
            # A simple check for info being a dict and having some content might be sufficient here
            # as a proxy for it being valid before returning.
            if not isinstance(info, dict) or not info:
                print(f"Warning: .info for {symbol} is not a valid dictionary or is empty.")
                # Optionally set info to a default dict or handle as an error condition
                # For now, we'll let it pass through as it is, or as None if initial fetch failed.
        except Exception as e:
            print(f"Could not retrieve or validate .info for {symbol}: {e}")
            info = None # Ensure info is None on error

    return df, info

####################### Predict #######################



def find_edges(series,hl,df,is_edge,extra_cond):
    edges = is_edge & extra_cond
    # Filter the DataFrame to only include the edge values that meet the condition
    shl = f'{series}{hl}'
    edge_values = df[series][edges]
    df[shl] = edge_values
    # Calculate the cumulative average of the edge values that meet the condition
    # We use the 'expanding' method to calculate the cumulative average up to the current row
    cma_shl = f'cma_{series}{hl}'
    df[cma_shl] = edge_values.expanding().mean()
    sma_shl = f'sma_{series}{hl}'
    window = 5
    df[sma_shl] = edge_values.rolling(window).mean()

    # The sma_shl and cma_shl columns will have NaN values for rows that are not edges
    # We can forward fill these NaN values with the last known edge average
    # If you want to start with NaNs until the first edge is encountered, you can skip the forward fill
    df[cma_shl] = df[cma_shl].ffill()
    df[sma_shl] = df[sma_shl].ffill()

    # but we don't do this so that we can preserve useful info
    #df[shl] = df[shl].ffill() # don't do this

def find_troughs(series, df, extra_cond):
    # shift(1) is the previous one, and shift(-1) is the next one
    is_trough = (df[series].shift(1) > df[series]) & (df[series].shift(-1) > df[series])
    hl = 'l'
    find_edges(series,hl,df,is_trough,extra_cond)

def find_peaks(series, df, extra_cond):
    # shift(1) is the previous one, and shift(-1) is the next one
    is_peak = (df[series].shift(1) < df[series]) & (df[series].shift(-1) < df[series])
    hl = 'h'
    find_edges(series,hl,df,is_peak,extra_cond)
    
# lowest inside high period version
# data: inout
def _no_calc_cma_(data,interval,num_std_dev=0.98):
    # Track the highest 'high' value encountered so far
    data['hsf'] = data['high'].cummax()
    # Increment 'high_period' each time a new peak is reached
    data['hprd'] = (data['high'] == data['hsf']).cumsum()
    # Calculate the row index within each group
    data['hrows'] = data.groupby('hprd').cumcount()
    # Calculate the cumulative moving average for 'high' values within each high period
    data['cmah'] = data.groupby('hprd')['high'].expanding().mean().values
    
    #data['lsf'] = data['low'].cummin()
    # Reset the lowest 'low' value tracking after each new high is encountered
    data['lsf'] = data.groupby('hprd')['low'].transform(lambda x: x.cummin())
    # Increment 'low_period' each time a new trough is reached within the current high period
    data['lprd'] = (data['low'] == data['lsf']).cumsum()
    # Calculate the row index within each group
    data['lrows'] = data.groupby('lprd').cumcount()
    # Calculate the cumulative moving average for 'low' values within each low period since the newest high
    data['cmal'] = data.groupby('lprd')['low'].expanding().mean().values
    
    # Track the highest 'high' value encountered in lprd so far
    data['lhsf'] = data.groupby('lprd')['high'].transform(lambda x: x.cummax()) #data['high'].cummax()
    # Increment 'high_period' each time a new peak is reached
    data['lhprd'] = (data['high'] == data['lhsf']).cumsum()
    # Calculate the row index within each group
    data['lhrows'] = data.groupby('lhprd').cumcount()
    # Calculate the cumulative moving average for 'high' values within each high period
    data['lcmah'] = data.groupby('lhprd')['high'].expanding().mean().values
    # Correct approach using numpy.where
    mh = np.where(data['cmah'] > data['lcmah'], data['cmah'], data['lcmah'])
    data['cmam'] = 0.5*(mh+data.cmal)
    return data

    # Not very useful:
    # Calculate the cumulative standard deviation for 'high' values within each high period
    #data['stdh'] = data.groupby('hprd')['high'].expanding().std().fillna(0.1).values
    # Calculate the upper and lower bands for 'high' values
    #data['bbuh'] = data['cmah'] + num_std_dev * data['stdh']
    #data['bblh'] = data['cmah'] - num_std_dev * data['stdh']
    # Calculate the cumulative standard deviation for 'low' values within each low period
    #data['stdl'] = data.groupby('lprd')['low'].expanding().std().fillna(0.1).values
    # Calculate the upper and lower bands for 'low' values
    #data['bbul'] = data['cmal'] + num_std_dev * data['stdl']
    #data['bbll'] = data['cmal'] - num_std_dev * data['stdl']
    
    #data['stdm'] = data.groupby('hprd')['close'].expanding().std().fillna(0.1).values
    #data['bbum'] = data['cmam'] + num_std_dev * data['stdm']
    #data['bblm'] = data['cmam'] - num_std_dev * data['stdm']


# hsf7,hsf14,hsf140,hsf300,hrows7,hrows14,hrows60,hrows140,hrows300,...
def extra_calcs(data,sma_name,interval):
    label = (sma_name if (sma_name == 'bbm') else sma_name[3:])
    data[f'hsf{label}'] = data[sma_name].cummax()
    data[f'hprd{label}'] = (data[sma_name] == data[f'hsf{label}']).cumsum()
    data[f'hrows{label}'] = data.groupby(f'hprd{label}').cumcount()

    # use original lowest here
    data[f'lsf{label}'] = data[sma_name].cummin()
    data[f'lprd{label}'] = (data[sma_name] == data[f'lsf{label}']).cumsum()
    data[f'lrows{label}'] = data.groupby(f'lprd{label}').cumcount()

    #if (interval in ['1d']) and (sma_name in ['sma7','sma140']):
    if (sma_name in ['bbm','sma7']):
        data[f'hlsf{label}'] = data.groupby(f'hprd{label}')[sma_name].transform(lambda x: x.cummin())
        data[f'hlprd{label}'] = (data[sma_name] == data[f'hlsf{label}']).cumsum()
        #data[f'hlrows{label}'] = data.groupby(f'hlprd{label}').cumcount()
        # Track the highest sma_name value encountered in lprd{label} so far
        data[f'lhsf{label}'] = data.groupby(f'hlprd{label}')[sma_name].transform(lambda x: x.cummax())
        # Increment 'high_period' each time a new peak is reached
        data[f'lhprd{label}'] = (data[sma_name] == data[f'lhsf{label}']).cumsum()
        #data[f'lhrows{label}'] = data.groupby(f'lhprd{label}').cumcount()
        # Calculate the cumulative moving average for 'high' values within each high period
        data[f'lcmah{label}'] = data.groupby(f'lhprd{label}')[sma_name].expanding().mean().values
        
        if sma_name in [
            #'bbm',
            'sma7'
        ]:
            # Calculate the cumulative moving average for 'low' values within each low period
            data[f'cmal{label}'] = data.groupby(f'lprd{label}')[sma_name].expanding().mean().values
            # Calculate a velocity indicator on the increase ratio of f'cmal{label}' in f'lrows{label}' rows
            # It measures the rate of change from the start of the current low period.
            cmal_series = data[f'cmal{label}']
            lrows_series = data[f'lrows{label}']

            # Get the first 'cmal' value in each 'lprd' group
            start_cmal = data.groupby(f'lprd{label}')[f'cmal{label}'].transform('first')
            # compound grouth velocity over bars periods
            bars = lrows_series + 1
            times_incr = cmal_series / start_cmal
            velocity = 100 * (times_incr ** (1/bars)) - 100
            # Handle division by zero or NaN results
            data[f'velo{label}'] = velocity.fillna(0)
        if sma_name == 'sma7':
            data['bias'] = 100 * data.close / data[sma_name] - 100
            #data['bias'] = 100 * data.close / data[f'lcmah{label}'] - 100

            data[f'cmah{label}'] = data.groupby(f'hprd{label}')[sma_name].expanding().mean().values
            # measure the consistency of the uptrend by sum of number of bars where hrows is 0 divided by the total number of bars
            #data[f'cnst{label}'] = 100 * (data[f'hrows{label}'] == 0).expanding(min_periods=1).mean()
            data[f'hlrows{label}'] = data.groupby(f'hlprd{label}').cumcount()
            data[f'lhrows{label}'] = data.groupby(f'lhprd{label}').cumcount()
            data[f'cnst{label}'] = 100 * ((data[f'sma{label}'] > data[f'sma{label}'].shift(1)) & (data[f'lhrows{label}'] == 0)).expanding(min_periods=1).mean()
            
            # Define the window size for consistency calculation
            cnst_window = 280 #28
            # Calculate the rolling consistency in a single, efficient operation
            # data[f'cnst{label}r'] = 100 * (data[f'hrows{label}'] == 0).rolling(
            #     window=cnst_window, min_periods=1
            # ).mean()
            data[f'cnsvel{label}'] = data[f'cnst{label}']*data[f'velo{label}']

    return data

# calculate cmas as they are see cma_on_whole.py



# Bbands and bbands width, and percentage
def fake_bb(df,cma,num_std_dev=1.99):
    df['bbm'] = cma
    std_exp = df.close.expanding().std().fillna(0.1).values
    ubbm = df.bbm + std_exp * num_std_dev
    lbbm = df.bbm - std_exp * num_std_dev
    df['bbu'] = ubbm
    df['bbl'] = lbbm
    df['bb6u'] = 0.618*df.bbu + 0.382*df.bbm
    df['bb4u'] = 0.382*df.bbu + 0.618*df.bbm
    df['bb4l'] = 0.382*df.bbl + 0.618*df.bbm
    df['bb6l'] = 0.618*df.bbl + 0.382*df.bbm
    bbb = 100*(df.bbu - df.bbl)/df.bbm
    df['bbb'] = bbb
    bbp = (df.close - df.bbl) / (df.bbu - df.bbl)
    df['bbp'] = 100*bbp
    return df



def fix_bb(df,cma,num_std_dev=1.99):
    std_exp = df.close.expanding().std().fillna(0.1).values
    df['bbm'] = df.bbm.fillna(cma)
    ubbm = df.bbm + std_exp * num_std_dev
    lbbm = df.bbm - std_exp * num_std_dev
    df['bbu'] = df.bbu.fillna(ubbm)
    df['bbl'] = df.bbl.fillna(lbbm)
    df['bb6u'] = 0.618*df.bbu + 0.382*df.bbm
    df['bb4u'] = 0.382*df.bbu + 0.618*df.bbm
    df['bb4l'] = 0.382*df.bbl + 0.618*df.bbm
    df['bb6l'] = 0.618*df.bbl + 0.382*df.bbm
    bbb = 100*(df.bbu - df.bbl)/df.bbm
    df['bbb'] = df.bbb.fillna(bbb)
    bbp = (df.close - df.bbl) / (df.bbu - df.bbl)
    df['bbp'] = 100*(df.bbp.fillna(bbp))
    return df



def ta_bb(df,bb_length,num_std_dev=1.99):
    """
        use only when df length > bb_length
    """
    bb = df.ta.bbands(length=bb_length,std=num_std_dev,talib=False,ddof=0)
    #print(f'origin bb.columns are {bb.columns}')
    bb.columns = [col[:3] for col in bb.columns.str.lower()]
    #print(f'>> after "[col[:3] for col in bb.columns.str.lower()]" bb.columns are \n {bb.columns}')
    df = df.join([bb])
    #print(f'>>> after "df = df.join([bb])" df.columns are \n {df.columns}')
    return df



# Bbands and bbands width, and percentage
# there are 24~25 hour bars in one trade day!
def calc_bb(df,cma,interval,num_std_dev=1.99):
    #print(f'> origin df.columns are \n {df.columns} shape {df.shape}')
    #bb_length = 420 if MySetts.hourly else 140 #60
    bb_length = MySetts.bb_ma_window(interval)

    df_length = len(df)
    if df_length > bb_length:
        df = ta_bb(df,bb_length=bb_length)
        df = fix_bb(df,cma)
    else:
        df = fake_bb(df,cma)

    df = extra_calcs(df,'bbm',interval)
    return df


def calc_smas(df,cma,interval):
    # it's said that us market has 252 trading days a year
    # so we might (or not) adjust the ma system accordingly
    for bars in sma_bars:
        df[f'sma{bars}'] = df.close.rolling(bars).mean()
    cols = df.columns
    for sma_name in sma_names:
        if sma_name in cols:
            df[sma_name] = df[sma_name].fillna(cma)
        else:
            df[sma_name] = cma
        df = extra_calcs(df,sma_name,interval)
    return df

# return a series of grouped cumulative counts of true
def series_bars_since(condition):
    # True and False should reversed(~) to get the right result
    return condition.groupby((~condition).cumsum()).cumsum()
    #df['jond'] = (df['j'] >= df['d']).groupby((df['j'] < df['d']).cumsum()).cumsum()

# replaced by my calc_kdj
# def calc_kdj_ta(df,interval):
#     # Calc kdj
#     # help(ta.kdj), help(df.ta.kdj)
#     #len_kdj = 7
#     #len_m = 7
#     #len_kdj = 14
#     len_kdj = 9
#     len_m = 10
#     if len(df) >= max(len_kdj,len_m):
#         kdj = df.ta.kdj(length=len_kdj,signal=3)
#         kdj.columns = [col[:1] for col in kdj.columns.str.lower()]
#         df = df.join([kdj])
#         df['m'] = rma(df.k,len_m)
#     else:
#         df['k'] = np.nan
#         df['d'] = np.nan
#         df['j'] = np.nan
#         df['m'] = np.nan

#     highest_high = df.high.expanding().max()
#     lowest_low = df.low.expanding().min()
#     rsv = 100 * (df.close - lowest_low) / non_zero_range(highest_high, lowest_low)
#     k = rsv.expanding().mean()
#     d = k.expanding().mean()
#     j = 3 * k - 2 * d
#     df.k = df.k.fillna(k)
#     df.d = df.d.fillna(d)
#     df.j = df.j.fillna(d)
#     df.m = df.m.fillna(k)
#     #print(df.m.info())    
#     return df



def calc_kdj(df,interval):
    len_kdj = 14
    len_m = 10
    len_k = 3
    len_d = 2
    len_df = len(df)
    if len_df >= max(len_kdj,len_m):
        highest_high = df.high.rolling(len_kdj).max()
        lowest_low = df.low.rolling(len_kdj).min()
        rsv = 100 * (df.close - lowest_low) / non_zero_range(highest_high, lowest_low)
        k = rma(rsv,len_k) #rsv.rolling(len_k).mean()
        d = rma(k,len_d) #k.rolling(len_d).mean()
        m = rma(k,len_m) #k.rolling(len_m).mean()
        j = 3 * k - 2 * d
        df['k'] = k
        df['d'] = d
        df['j'] = j
        df['m'] = m #rma(df.k,len_m)
    else:
        df['k'] = np.nan
        df['d'] = np.nan
        df['j'] = np.nan
        df['m'] = np.nan

    highest_high = df.high.expanding().max()
    lowest_low = df.low.expanding().min()
    rsv = 100 * (df.close - lowest_low) / non_zero_range(highest_high, lowest_low)
    k = rsv.expanding().mean()
    d = k.expanding().mean()
    j = 3 * k - 2 * d
    df.k = df.k.fillna(k)
    df.d = df.d.fillna(d)
    df.j = df.j.fillna(d)
    df.m = df.m.fillna(k)
    #print(df.m.info())    
    return df



# Dataframe preparing       
def df_prepare(df,interval):
    cma = df.close.expanding().mean()
    df = calc_bb(df,cma,interval,num_std_dev=1.99)
    # calc cmas this is not needed anymore, now we only use cma_for_smas
    needed = False
    if needed:
        df = _no_calc_cma_(df,interval)
    df = calc_smas(df,cma,interval)
    df = calc_kdj(df,interval)
    return df



def predicted(df,interval,fully=True):
    df = df_prepare(df,interval)
    # this part is not yet that useful
    prd_kdj = False
    if prd_kdj:
        df = predict_kdj(df,interval)
        
    df = set_entries(df,interval)
    df = refine_columns_for_backtesting(df)

    if fully == True:
        return df
    else:
        return slice_hlrows(df,'hrows7',remain_bars)


def refine_columns_for_backtesting(df):
    # todo: #6 use capitalized basic column names instead, check the pandas-ta manual
    # List of columns to capitalize, required by backtesting.py 
    columns_to_capitalize = ['open', 'high', 'low', 'close', 'volume']
    df = add_capd_columns(df, columns_to_capitalize)
    df.index.names = ['Date']
    return df



def add_capd_columns(df, columns_to_capitalize):
    # Using a dictionary comprehension to create a new dictionary with capitalized keys for selected columns
    capitalized_columns = {col.capitalize(): df[col] for col in columns_to_capitalize}

    # Assign the new capitalized columns to the DataFrame
    df = df.assign(**capitalized_columns)
    return df


# predict whether d is at an edge 
def predict_kdj(df,interval):
    predict_dh(df)
    predict_dl(df)
    return df

def set_entries(df,interval):
    # must set opt entries first
    set_opt_entries(df,interval)
    set_etf_entries(df,interval)
    #display(df.loc[(df.dl > 0) | (df.dh > 0),['dl','dh']])
    return df
    



# only suitable for bear market bottom
def predict_dl(df,threshold=25):
    # Apply the function to the 'd' column to get a boolean series where peaks are True and 'd' > 60
    extra_cond = (df.d < threshold) & (df.hrows7 >= hrow_max) #& (df.bbm < df.cmah7)
    find_troughs('d',df,extra_cond)

    df['std_dla'] = df.cma_dl.expanding().std()
    df['pdl_ua'] = df.cma_dl + (df.std_dla*1.1)
    # gap
    df['pdl_uga'] = df.dl - df.pdl_ua
    
    df['std_dl'] = df.dl.expanding().std()
    df['pdl_u'] = df.cma_dl + df.std_dl
    # gap
    df['pdl_ug'] = df.dl - df.pdl_u

    # fails
    df['pdl_fl'] =  (df.pdl_uga > 0) & (df.pdl_ug > 0)
    df['pdl_flrt'] = df.pdl_fl.cumsum()/(df.dl.notna() & df.std_dl.notna()).cumsum()
    


def predict_dh(df,threshold=70):
    # Apply the function to the 'd' column to get a boolean series where peaks are True and 'd' > 60
    #extra_cond = (df.d > threshold) & (df.hrows7 < hrow_max)    
    extra_cond = (df.d > threshold) & ((df.hrows7 < hrow_max) | (df.high > df.cmah7)) 
    find_peaks('d',df,extra_cond)

    df['std_dha'] = df.cma_dh.expanding().std()
    df['pdh_la'] = df.cma_dh - (df.std_dha*1.1)
    # gap
    df['pdh_lga'] = df.dh - df.pdh_la
    
    df['std_dh'] = df.dh.expanding().std()
    df['pdh_l'] = df.cma_dh - (df.std_dh*1.1)
    # gap
    df['pdh_lg'] = df.dh - df.pdh_l
    
    # fails
    df['pdh_fl'] = (df.pdh_lga < 0) & (df.pdh_lg < 0) 
    df['pdh_flrt'] = df.pdh_fl.cumsum()/(df.dh.notna() & df.std_dh.notna()).cumsum()
        

# move>>>
# def calc_last_half_rbl_ma_not_good(df,sma): # MOVED to extra/toolfuncs_extra.py
#     """
#     Calculate the average of the last half of data up to each row using vectorized operations.
#     """
#     rbl = np.where(
#         df['close'] < df[sma],
#         (df['close'] / df[sma] - 1),
#         0
#     )
    
#     # Convert to Series for rolling operations
#     s = pd.Series(rbl)

#     # Create list to store results
#     results = []
    
#     for i in range(len(df)):
#         window = max(1, (i + 1) // 2)  # Ensure window is at least 1
#         avg = s.iloc[max(0, i - window + 1):i + 1].mean()
#         results.append(avg)
    
#     # Use rolling with variable window size
#     df['cma_rbl'] = results
    
#     return df.cma_rbl
    


def recent_rbl_ma(df, sma):
    """
    Calculate ratio when price is below SMA and its running average for all data points
    
    Parameters:
    df (pandas.DataFrame): DataFrame with 'close' and 'sma' columns
    
    Returns:
    pandas.DataFrame: Original DataFrame with new columns 'rbl' and 'cma_rbl'
    """
    # Calculate ratio below SMA
    x='high'
    df['rbl'] = np.where(
        df[x] < df[sma],  # condition for below SMA
        (df[x] / df[sma] - 1),  # calculation when below
        0  # when not below
    )
    
    # Calculate running average including all rows
    # Use expanding() to compute running mean on all data points
    df['cma_rbl'] = df.rbl.expanding().mean()
    if False:
        n=2
        hdf = df[len(df)//n:] 
        df[len(df)//n:]['cma_rbl'] = hdf.rbl.expanding().mean()
    return df.cma_rbl


# move>>>
# def calculate_below_sma_sum(df,sma): # MOVED to extra/toolfuncs_extra.py
#     """
#     Calculate ratio when price is below SMA and its running sum
    
#     Parameters:
#     df (pandas.DataFrame): DataFrame with 'close' and 'sma' columns
    
#     Returns:
#     pandas.DataFrame: Original DataFrame with new columns 'rbl_ma' and 'srbl_ma'
#     """
#     # Calculate ratio below SMA
#     df['rbl_ma'] = np.where(
#         df['close'] < df[sma],  # condition for below SMA
#         (df['close'] / df[sma] - 1),  # calculation when below
#         0  # when not below
#     )
    
#     # Calculate running sum of ratios below SMA
#     df['srbl_ma'] = df['rbl_ma'].cumsum()
    
#     return df


#=============================================================


# I don't understand these, chat_gpt4 gives me:
# def comparing_example(df): # MOVED to extra/toolfuncs_extra.py
#     b = df.apply(lambda row:
#         (row.bbm < df.low.shift(row.lrows7))[row.name] & (row.bbm < df.bbm.shift(row.lrows7))[row.name],
#         axis=1
#     )
#     df['result'] = b

def final_risen(df,n,price):
    dfl = len(df) - 1
    pri_p = df[price].iloc[-n] if dfl > n else df[price].iloc[-dfl]
    test = df[price].iloc[-1] > pri_p
    return test

def final_both_risen(df,n,price1,price2):
    return (len(df) > 1) & final_risen(df,n,price1) & final_risen(df,n,price2)

def risen(df,price):
    if len(df) < 2:
        return False
    else:
        return df[price] > df[price].shift(1)
        


def cma_sma_equal(df,interval):
    return df.sma7 == df.lcmah7

# must use with (final_)sma_series_up
def cma_series_up(df,interval=None):
    big_interval = interval in ['3mo','1mo','1wk']
    sma7_upon_lcmah7 = big_interval | (df.sma7 >= df.lcmah7)
    cmas_up7 = sma7_upon_lcmah7 & rising(df,'lcmah7') & rising(df,'sma7')

    close_upon_lcmah7 = (df.close >= df.lcmah7)
    close_upon_sma7 = (df.close >= df.sma7)
    cmas_up = cmas_up7 & (close_upon_lcmah7 | close_upon_sma7)
    
    return cmas_up


def sma_series_up(df):
    return risen(df,'sma7') & risen(df,'bbm')


def final_sma_series_up(df,interval=None):
    dfl = len(df)
    bb_ma_window = MySetts.bb_ma_window(interval)
    far_bar = min(bb_ma_window+1, dfl)
    near_bar = min(7+1, dfl)
    return (dfl>1) & final_risen(df,near_bar,'close') & final_risen(df,far_bar,'close')
    

def falling(df,name,n=1):
    return df[name] < df[name].shift(n)

def rising(df,name,n=1):
    return df[name] > df[name].shift(n)

def consolidating(df,name,n=1):
    return df[name] == df[name].shift(n)


def falling_sma(df,x):
    '''
        sma{x} falling
    '''
    name = f'sma{x}'
    return falling(df,name)

def rising_sma(df,x):
    '''
        sma{x} rising
    '''
    name = f'sma{x}'
    return rising(df,name)

# consolidating
def consoling_sma(df,x):
    '''
        sma{x} consolidating
    '''
    name = f'sma{x}'
    return consolidating(df,name)


# utilize bull/bear etfs to focus on a bull market of underline, whether it be, say, TQQQ or SQQQ, etc.
# entries are for short on options only
# everything simplified
def set_opt_entries(df,interval):
    """
        
        KEY TO TREND DRIVE TRADING

        NEVER CHANGE THESE CONDITIONS

    """
    df['cmas_up'] = cma_series_up(df,interval) 
    df['smas_up'] = sma_series_up(df)
    df['avrgs_bull'] = df.smas_up & df.cmas_up
    df['avrgs_bear'] = ~df.smas_up & ~df.cmas_up
    

    # NOTE: only k >= d and low <= sma7 or first 2 bars that low > sma7 are marked True
    # count bars that k > d and low > sma 
    bars_k_on_d =series_bars_since((df.k > df.d) & (df.low > df.sma7))
    df['bcall'] = df.avrgs_bull & (df.k >= df.d) & (bars_k_on_d < 3) #& low_d

    # NOTE: only k < d and high > sma7 or first 2 bars that high < sma7 are marked True
    # count bars that k < d and high < sma 
    bars_d_on_k =series_bars_since((df.k < df.d) & (df.high < df.sma7))
    df['bput'] = ~df.avrgs_bull & (df.j < df.d) & (bars_d_on_k < 3) #& high_d

    




def set_etf_entries(df,interval):
    '''
        filter option entries to get etf entries
        more stict than conditions for buy/sell options
    '''
    df['buy'] = df.bcall & ((df.open <= df.bbu)|(df.close <= df.bbu))
    df['sell'] = df.bput & ((df.open >= df.bbl)|(df.close >= df.bbl))
    
    df['watch'] = (df.j.shift(1) < 8) & (df.j > df.j.shift(1)) & (df.close > df.bbm) & (df.bbm > df.bbm.shift(1))
    both_equal = cma_sma_equal(df,interval)
    df['hold'] = df.cmas_up & both_equal



