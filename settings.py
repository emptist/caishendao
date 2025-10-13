import math
from fractions import Fraction
import urllib.request
from proxy_detector import is_running_on_localhost

class MySetts:  # (USTradingTime):
    # 检测是否在本地运行（localhost）
    use_proxy = is_running_on_localhost()
    
    # 在本地运行时使用代理，在服务器上运行时不使用代理
    
    # 代理配置
    proxies = urllib.request.getproxies()
    default_proxy = 'http://127.0.0.1:7890'
    yf_proxy = proxies.get('http', default_proxy)
    yfs_proxy = proxies.get('https', default_proxy)
    yf_socks_proxy = proxies.get('socks', default_proxy)

    ai_provider = "alibabacloud" if use_proxy else "gemini"  # 可选: "gemini", "alibabacloud"
    alibabacloud_api_base = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    # AI分析缓存设置
    n_hour = 48
    ai_analysis_cache_ttl_seconds = 3600 * n_hour  # n_hour 小时缓存时间限制

    hour_bars_per_day = 17  # 9 # use half of total: 25 in Futu, 17 in YF
    
    @staticmethod
    def equivalence_to_days(interval: str) -> Fraction:
        match interval:
            case '1d':
                return Fraction(1,1)
            case "1wk":
                return Fraction(5,1)
            case "1mo":
                return Fraction(20,1)
            case "3mo":
                return Fraction(60,1)
            case "1h":
                return Fraction(1,16)
            case "2h":
                return Fraction(1,8)
            case "4h":
                return Fraction(1,4)
            case "60m":
                return Fraction(1,16)
            case "30m":
                return Fraction(1,32)
            case "15m":
                return Fraction(1,64)
            case "5m":
                return Fraction(1,192)
            case "3m":
                return Fraction(1,320)
            case "1m":
                return Fraction(1,960)
            case _:
                return Fraction(1,1)


    @staticmethod
    def bb_ma_window(interval: str,window_d: int = 140) -> int:
        equiv_d = MySetts.equivalence_to_days(interval)
        return math.ceil(window_d/equiv_d)

    # --- some old codes are not carefully designed ---
    @staticmethod
    def calc_hrow_max(interval: str) -> int:
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

