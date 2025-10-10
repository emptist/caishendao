class MySetts:  # (USTradingTime):
    use_proxy = False #True # However we don't need a proxy running, I don't know why
    yf_proxy = "http://127.0.0.1:7890" if use_proxy else None
    yfs_proxy = yf_proxy

    ai_provider = "alibabacloud" if use_proxy else "gemini"  # 可选: "gemini", "alibabacloud"
    alibabacloud_api_base = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    # AI分析缓存设置
    n_hour = 48
    ai_analysis_cache_ttl_seconds = 3600 * n_hour  # n_hour 小时缓存时间限制

    hour_bars_per_day = 17  # 9 # use half of total: 25 in Futu, 17 in YF
    

    @staticmethod
    def calc_hrow_max(interval):
        if interval == "1wk":
            hrow_max = 3
        elif interval == "1mo":
            hrow_max = 2
        elif interval in {"1d", "1 day"}:
            hrow_max = 7
        else:
            hrow_max = 7
        return hrow_max

    @staticmethod
    def get_interval_period(bar_type):
        # SPY: Period '700d' is invalid, must be one of ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
        if bar_type == "quarterly":
            interval = "15m"
            period = "1mo"
        elif bar_type == "hourly":
            interval = "1h"
            period = "2y"
        elif bar_type == "daily":
            interval = "1d"
            period = "max"  #'10y'
        elif bar_type == "weekly":
            interval = "1wk"
            period = "max"
        elif bar_type == "monthly":
            interval = "1mo"
            period = "max"
        return interval, period

    @staticmethod
    def get_period(interval):
        # SPY: Period '700d' is invalid, must be one of ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
        # available intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
        if interval in ["1m", "2m", "5m"]:
            period = "5d"
        elif interval in [
            "15m",
            "30m",
        ]:
            period = "1mo"
        elif interval in ["60m", "90m", "1h"]:
            period = "3mo"
        elif interval in ["1d", "5d"]:
            period = "max"
        elif interval in ["1wk", "3mo"]:
            period = "max"  #'6mo'
        elif interval in [
            "1mo",
        ]:
            period = "10y"  #'max' #'5y'
        return period

    # We can trade on multiple underlines
    @staticmethod
    def underline_symbols(trade_mode):
        if trade_mode == "basic_option_mode":
            underline_symbols = [
                "SPY",
                "QQQ",
            ]
        # future version, under work
        elif trade_mode == "bull_etf_mode":
            underline_symbols = [
                "TQQQ",
                #'SOXL',
                #'LABU',
                #'TNA',
            ]
        elif trade_mode == "bear_etf_mode":
            underline_symbols = [
                "SQQQ",
                #'SOXS',
                #'LABD',
                #'TZA',
            ]
        print(
            f"<<<< trade_mode: {trade_mode}, underline_symbols {underline_symbols} >>>>"
        )
        return underline_symbols

    ####### settings #######
    strike_delta = 0.00096 #0.00191 #0.00382
    #strike_delta = 0.00382 #
    #strike_delta = 0.00618
    # BE CAREFUL: 
    #   xdays are simply calendar days but not trading days
    # xdays > 28 will have less strikes available    
    xdays = 4 #25 #21 # 2 #7 #3
    
    opt_quantity = 1  # 2
    
    # when strike_delta = 0.00618, xdays = 4, for SPY,QQQ, perhaps IBIT
    call_price = 4.5
    put_price = 4

    # available intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
    bar_type = "daily"
    # bar_type = 'hourly'
    # bar_type = 'quarterly'

    # total percentage of money to use by auto-trading
    total_percent = 80
    stock_percent = 99

    # minimal rows of df to keep from been cut off
    remain_bars = 300

    hourly = bar_type == "hourly"
    quarterly = bar_type == "quarterly"
    daily = bar_type == "daily"
    weekly = bar_type == "weekly"
    monthly = bar_type == "monthly"
    # Use trade_mode to change underline stock and trading behaviour

    interval, period = get_interval_period(bar_type)

    hrow_max = calc_hrow_max(interval)

    d_level = 55

"""
    #class method demo
    @classmethod
    #def get_underline_symbol(cls, trade_mode):
        # if use cls variables inside cls method add cls.var_name, 
        # cls is not needed outside methods

        options_underline_symbol = 'SPY' #'QQQ' 
        bull_etf_symbol = 'TQQQ'
        bear_etf_symbol = 'SQQQ'

        if trade_mode == 'basic_option_mode':
            underline_symbol = options_underline_symbol.upper()
        # future version, under work
        elif trade_mode == 'bull_etf_mode':
            underline_symbol = bull_etf_symbol.upper()
        elif trade_mode == 'bear_etf_mode':
            underline_symbol = bear_etf_symbol.upper()    
        print(f'<<<< trade_mode: {trade_mode}, underline_symbol {underline_symbol} >>>>')

        return underline_symbol
"""

# ib settings


# ib get data settings
# https://interactivebrokers.github.io/tws-api/historical_bars.html
# Legal ones are: 1 secs, 5 secs, 10 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 10 mins, 15 mins, 20 mins, 30 mins, 1 hour, 2 hours, 3 hours, 4 hours, 8 hours, 1 day, 1W, 1M,
def get_bar_size(interval):
    if "1mo" == interval:
        return "1M"
    elif "1wk" == interval:
        return "1W"
    elif "1d" == interval:
        return "1 day"
    elif "1h" == interval:
        return "1 hour"
    elif "1m" == interval:
        return "1 min"
    elif "1s" == interval:
        return "1 secs"
    elif "mo" in interval:
        return "1M"  # no n months data
    elif "wk" in interval:
        return "1W"  # no n weeks data
    elif "d" in interval:
        return "1 day"  # no n days data
    elif "h" in interval:
        return interval[:-1] + " hours"
    elif "m" in interval:
        return interval[:-1] + " mins"
    elif "s" in interval:
        return interval[:-1] + " secs"


