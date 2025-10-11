# trading_group.py
# pandas-ta https://pub.towardsai.net/technical-analysis-with-python-quickstart-guide-for-pandas-ta-fe4b152e95a2

import warnings

# 输入验证函数，防止路径遍历攻击
def validate_user_input(input_str, allowed_chars=None):
    """验证用户输入，防止路径遍历和其他注入攻击
    
    Args:
        input_str: 用户输入的字符串
        allowed_chars: 允许的字符集（正则表达式格式）
        
    Returns:
        清理后的安全字符串，或在验证失败时返回None
    """
    if not input_str or not isinstance(input_str, str):
        return None
    
    # 检查是否包含路径遍历字符
    if any(ch in input_str for ch in ['../', '..\\', '/..', '\\..']):
        return None
    
    # 检查是否包含绝对路径字符
    if any(input_str.startswith(prefix) for prefix in ['/', '\\', 'C:', 'D:']):
        return None
    
    # 检查是否包含控制字符
    for char in input_str:
        if ord(char) < 32 and char not in ['\t', '\n']:
            return None
    
    # 如果提供了允许的字符集，则进行更严格的验证
    if allowed_chars:
        import re
        if not re.match(allowed_chars, input_str):
            return None
    
    return input_str
warnings.simplefilter(action='ignore') #, category=FutureWarning)
#import pytz # Unused
import pandas as pd
#import pandas_ta as ta # Unused
#import yfinance as yf # Unused (was already commented, Vulture missed this)

from exceptions import *
from favorites import MyFavorites
from toolfuncs import dfs_for_interval,get_pe,tidy_yf_df,predicted,final_sma_series_up,recent_rbl_ma


class Quote:
    def __init__(self,interval,df,gists=True):
        self.interval = interval
        self.df = df
        self.df_predicted = False
        self.gists = gists

    #def __dir__(self):
    #    return f'interval: {self.interval} df: {self.df.shape}'

    def tidy_df(self):
        self.df = tidy_yf_df(self.df)
        return self

    def df_predict(self):
        if self.df_predicted == False:
            self.df = predicted(self.df, self.interval,gists=self.gists)
            self.df_predicted = True
        return self

    def approved(self,dceil,filter):
        df = self.df
        if (df.d.iloc[-1] <= dceil):
            equal = (df.sma7.iloc[-1] == df.lcmah7.iloc[-1]) if self.interval in ['1d','1wk'] else True
            match filter:
                case 'Fork':
                    return equal & (df.lrows7.iloc[-1] > 0)
                case 'Foot':
                    return equal & (df.close.iloc[-1] < df.bbu.iloc[-1]) #(df.close.iloc[-1] < df.bb6u.iloc[-1])
                case 'Leap':
                    return equal & (df.lrows7.iloc[-1] == 0)
                case 'buy':
                    return equal & df.buy.iloc[-1]
                case 'sput':
                    return equal & df.sput.iloc[-1]
                case 'All':
                    return equal
                case 'Potential':
                    return not equal
                case 'cmas_up':
                    return df.cmas_up.iloc[-1]
                case 'breakm': # m means month data
                    breakbars = ((df.high >= df.cmah) & (df.high >= df.lcmah)) 
                    return breakbars.iloc[-1] & ~breakbars.iloc[-2]
                case 'watch':
                    return df.watch.iloc[-1]
                case 'sell':
                    return df.sell.iloc[-1]
                case 'scall':
                    return df.scall.iloc[-1]
                case 'maGood':
                    return df.ma_good.iloc[-1]
                case 'JonD':
                    return df.j.iloc[-1] > df.d.iloc[-1]
                case 'DonJ':
                    return df.j.iloc[-1] < df.d.iloc[-1]
                case '<7':
                    return df.close.iloc[-1] < df.sma7.iloc[-1]
                case '>=7':
                    return df.close.iloc[-1] >= df.sma7.iloc[-1]
                case '<BBM':
                    return df.close.iloc[-1] < df.bbm.iloc[-1]
                case '>=BBM':
                    return df.close.iloc[-1] >= df.bbm.iloc[-1]
                case '<bb4l':
                    return df.close.iloc[-1] < df.bb4l.iloc[-1]
                case '<bb6l':
                    return df.close.iloc[-1] < df.bb6l.iloc[-1]
                case '<bbl':
                    return df.close.iloc[-1] < df.bbl.iloc[-1]
                case '<cmal':
                    return df.close.iloc[-1] < df.cmal.iloc[-1]
                case _:
                    return True
        else:
            return False

    def watch(self):
        return self.df_predict().df.watch.iloc[-1]

    def ma_good(self):
        return self.df_predict().df.ma_good.iloc[-1]

    def sput(self):
        return self.df_predict().df.sput.iloc[-1]

    def buy(self):
        return self.df_predict().df.buy.iloc[-1]


    def up_break(self,x=2):
        #x = 2 #months/weeks
        if len(self.df) < x+2:
            return False

        df = self.df_predict().df
        return (df.hrows.iloc[-2] >= x) & (df.hrows.iloc[-2] > df.hrows.iloc[-1])
        #return df.hrows.iloc[-1] <= 1


    def new_high(self, n=1):
        return self.df_predict().df.hrows.iloc[-1] < n

    def j_not_high(self,j=98,d=98): # j=123
        df = self.df_predict().df
        jnh = df.j.iloc[-1] < j
        dnh = df.d.iloc[-1] < d
        dup = df.d.iloc[-1] >= df.d.iloc[-2]
        kup = df.k.iloc[-1] >= df.k.iloc[-2]
        mup = df.m.iloc[-1] >= df.m.iloc[-2]
        #print('j not_high:', jnh)
        return jnh & dnh & (dup | kup | mup)

    def key_macma_up(self):
        df = self.df_predict().df
        up = df.cmas_up.iloc[-1]
        #print('final cmas_up: ', up)
        return up #up.iloc[-1]

    # ==== fast since don't need df_predict ====
 
    def percent_value(self):
        df = self.df #df_predict().df
        if len(df) < 2:
            return True

        p = (df.close.iloc[-1]/df.close.iloc[-2]-1)*100
        return round(p, 2)

    def high_cnstvelo(self,limit=4):
        v = self.cnstvelo_value()
        match self.interval:
            case '1h':
                limit = limit/20
            case '1d':
                limit = limit
            case '1w':
                limit = limit*5
            case '1mo':
                limit = limit*20
            case '3mo':
                limit = limit*60
            case _:
                limit = limit
        result = v >= limit
        return result

    def cnstvelo_value(self):
        df = self.df_predict().df
        cnstvelo = df.cnsvel7.iloc[-1] 
        #print(f'cnstvelo_value: {cnstvelo}')
        return cnstvelo

    def high_cnst(self,limit=40):
        v = self.cnst_value() 
        result = v >= limit
        return result

    def cnst_value(self):
        df = self.df_predict().df
        cnst = df.cnst7.iloc[-1]
        #print(f'cnst_value: {cnst}')
        return cnst


    def high_velo(self,limit=0.1):
        v = self.velo_value() 
        match self.interval:
            case '1h':
                limit = limit/20
            case '1d':
                limit = limit
            case '1w':
                limit = limit*5
            case '1mo':
                limit = limit*20
            case '3mo':
                limit = limit*60
            case _:
                limit = limit
        result = v >= limit
        return result

    def velo_value(self):
        df = self.df_predict().df
        velo = df.velo7.iloc[-1]
        #print(f'velo_value: {velo}')
        return velo
    

    def bias_not_high(self, limit=3):
        return self.bias_value() <= limit

    def bias_value(self):
        df = self.df_predict().df
        bias = df.bias.iloc[-1]
        #print(f'bias_value: {bias}')
        return bias

    def kdj_value(self):
        df = self.df
        j = df.j.iloc[-1] if len(df.j)>0 else 1000 
        d = df.d.iloc[-1] if len(df.d)>0 else 1000 
        return j+d

    def amount(self):
        df = self.df #df_predict().df
        #return df.close.iloc[-2] * df.volume.iloc[-2]
        if len(df.close) > 1:
            return df.close.iloc[-2] * df.volume.iloc[-2]
        else:
            return True


    def amount_suitable(self):
        amnt = self.amount()
        yi = 100000000  # 10 billion
        yi = yi * 0.01 # 100 w
        match self.interval:
            case '1h':
                #print('1h',amnt)
                # amnt could be 0.0 in hour data
                return True #amnt > yi / 50
            case '1d':
                return amnt > yi
            case '1w':
                return amnt > 4*yi
            case '1mo':
                return amnt > 18*yi
            case _:
                return amnt > yi / 100


    def cma_rbl(self,sma):
        df = self.df_predict().df
        return recent_rbl_ma(df,sma).iloc[-1]

    
    def final_smas_up(self):
        up = final_sma_series_up(self.df,self.interval,gists=self.gists)
        #print(f'gists: {self.gists} final_smas_up: {up}')
        return up
    
    def lrows7_not_zero(self):
        n = self.df_predict().df.lrows7.iloc[-1] 
        return n > 1





class StockData:
    # class names must be definded before use in file in Python
    clsQuote = Quote
    # not for auto-trading


    def __init__(self, symbol, sort_by_interval, pe_ratio):
        self.symbol = symbol
        self.sort_by_interval = sort_by_interval
        self.pe_ratio = pe_ratio
        self.quotes = {}
        
    #def __dir__(self):
        #return f'{self.symbol} sort with {self.sort_by_interval}, pe_ration {self.pe_ratio} quotes: {self.quotes}'        
    #    return f'{self.symbol} sort with {self.sort_by_interval}' #, pe_ration {self.pe_ratio} quotes: {self.quotes}'        



    def detect_potential(self,stk_group,detecting,pe_limit=None,key_interval=None,gists=True):
        working_interval = stk_group.init_interval if key_interval is None else key_interval
        if self.quotes.__contains__(working_interval):
            if (pe_limit is not None) and self.pe_ratio > pe_limit:
                return
            #print(f'symbol: {self.symbol} items: {self.quotes}')
            #print(f'***** debug before detecting {self.symbol}')
            q = self.quotes[working_interval]
            q.gists = gists
            length = len(q.df)
            if (length > 1) and q.amount_suitable() and detecting(q,self.symbol):
                stk_group.move_to_potentials(self)
                #print(f'***** debug detect_potential {self.symbol}')
            elif self.symbol in stk_group.due_symbols:
                #print('due symbol:',self.symbol)
                stk_group.move_to_potentials(self)
            
            

    def tidy_update_quote(self,interval,df):
        self.quotes[interval] = self.clsQuote(interval,df).tidy_df()
        return self.quotes[interval]

        
    def predict_quotes(self):
        for interval in self.quotes.keys():    
            self.quotes[interval].df_predict()
        return self.quotes

    def sort_by_interval_cma_rbl(self,sma):
        return self.quotes[self.sort_by_interval].cma_rbl(sma)
    
    def sort_by_interval_bias(self):
        return self.quotes[self.sort_by_interval].bias_value()
    
    
    def sort_by_interval_kdj(self):
        return self.quotes[self.sort_by_interval].kdj_value()

    def sort_by_interval_cnstvelo(self):
        return self.quotes[self.sort_by_interval].cnstvelo_value()

    def sort_by_interval_amount(self):
        return self.quotes[self.sort_by_interval].amount()


    def sort_by_interval_percent(self):
        return self.quotes[self.sort_by_interval].percent_value()





class StockGroup:
    clsStockData = StockData
    #stockdata_dict = {} #  symbol:StockData
    short_interval = '15m'
    middle_interval = '1h'
    long_interval = '1d'
    large_interval = '1wk'
    max_interval = '1mo'

    cls_all_intervals = [
        #short_interval,
        #middle_interval,
        long_interval,
        large_interval,
        max_interval,
    ]

    sort_by_interval = long_interval #if \
    #(datetime.now(USTradingTime.eastern).time().hour > 9) else middle_interval
        
    EXCLUDES = {}

    @classmethod
    def get_long_name(cls, tickers, symbol):#not used
        try:
            longName = tickers[symbol].info['longName']
        except Exception as e:
            longName = symbol
        return longName

    @classmethod
    def include_symbols(cls,symbols,ignoreds={}):
        if symbols:    
            ignoreds = cls.EXCLUDES.union(ignoreds)
            symbols = [symbol for symbol in symbols if symbol not in ignoreds]
        return symbols

    @classmethod
    def bull_starting(cls,symbols,init_interval='1d',sort_by_interval='1d',all_intervals=['1d'],pe_limit=None,top_n=None,ignoreds={},due_symbols={},gists=True):
        g = cls.trade_group(
            symbols=symbols.union(due_symbols),
            init_interval=init_interval,
            sort_by_interval=sort_by_interval,
            all_intervals=all_intervals,
            pe_limit=pe_limit,
            due_symbols=due_symbols,
        )
        def detecting(q,symbol=''):
            up = q.final_smas_up()
            #print(f'final_smas_up: {up}')
            return up
            
        g.find_potential_target(detecting=detecting,srt=None,gists=gists)
        
        g.recollect_dicts()
        
        def detecting(q:Quote,symbol=''):
            bias_limit = 15 #3
            bull_starts = q.bias_not_high(bias_limit) and q.key_macma_up() # and q.j_not_high(j=97,d=95) 
            # hc_limit = 38
            # hv_limit = 0.04
            # bull_starts = bull_starts and q.high_cnst(limit=hc_limit) and q.high_velo(limit=hv_limit)
            bull_starts = bull_starts and q.high_cnstvelo()
            return bull_starts
        
        g.find_potential_target(detecting=detecting,srt=None,gists=gists)
    

        for interval in all_intervals:
            if interval != init_interval:
                g.potential_dict_add_data_for(interval)

        #x = -2
        #g.find_potential_target(detecting=detecting,srt=None,key_interval=g.all_intervals[x])

        def srt(e:StockData):
            return e.sort_by_interval_cnstvelo()
            #return e.sort_by_interval_percent()
            #return e.sort_by_interval_kdj()
            #return e.sort_by_interval_bias()
            #return e.sort_by_interval_amount() 
            #return e.sort_by_interval_cma_rbl('sma7') # use sma30 with month data 
        g.sort_potentials(srt,reverse=True)
        return g



    @classmethod
    def all_ready(cls,symbols,init_interval='1d',sort_by_interval='1mo',all_intervals=['1mo','1d'],pe_limit=None,top_n=None,ignoreds={}):
        g = cls.trade_group(
            symbols,
            init_interval=init_interval,
            sort_by_interval=sort_by_interval,
            all_intervals=all_intervals,
            pe_limit=pe_limit
        )
        def detecting(q,symbol=''):
            up = q.final_smas_up()
            #print(f'final_smas_up: {up}')
            return up
            
        g.find_potential_target(detecting=detecting,srt=None)
        
        g.recollect_dicts()
        
        def detecting(q,symbol=''):
            return q.j_not_high() and q.key_macma_up() #and q.ma_good() 
            #return q.buy()
        
        g.find_potential_target(detecting=detecting,srt=None)
    

        for interval in all_intervals:
            if interval != init_interval:
                g.potential_dict_add_data_for(interval)

        #x = -2
        #g.find_potential_target(detecting=detecting,srt=None,key_interval=g.all_intervals[x])

        def srt(e):
            #return e.sort_by_interval_percent()
            return e.sort_by_interval_kdj()
            #return e.sort_by_interval_amount() 
            #return e.sort_by_interval_cma_rbl('sma7') # use sma30 with month data 
        g.sort_potentials(srt,reverse=True)
        return g



    @classmethod
    def new_high_group(cls,symbols,interval,pe_limit=None,top_n=None,ignoreds={}):
        new_high_symbols, base_data = cls.new_high_stocks(symbols,interval)
        tickers = base_data[2]
        if tickers is not None:
            list = ['Bond','Loan','AAA','Rate','Duration','Bitcoin','Coin']
            symbols = [symbol for symbol in new_high_symbols \
                if not any(map(tickers[symbol].info['longName'].__contains__,list))
            ]
            #print(f'filtered symbols {symbols}')


        def detecting(q,symbol=''):
            return q.ma_good() 
            #return q.up_break() 

        def srt(e):
            return e.sort_by_interval_percent()
            #return e.sort_by_interval_cma_rbl('sma7') # use sma30 with month data 

        stk_group = cls.potential_group(
            detecting,
            srt,
            symbols=symbols, #new_high_symbols,
            init_interval=interval,
            pe_limit=pe_limit,
            base_data_tuple=base_data
        )
        stk_group.set_info(base_data[2])
        return stk_group





    @classmethod
    def trade_group(cls,symbols,init_interval,sort_by_interval=None,all_intervals=None,pe_limit=None,due_symbols={}):
        stk_group = cls(init_interval,sort_by_interval,all_intervals=all_intervals,pe_limit=pe_limit,due_symbols=due_symbols)
        stk_group.init_stockdata_dict(symbols,name_except='Bond')
        return stk_group


    @classmethod
    def potential_group(cls,detecting,srt,symbols=None,all_intervals=None,init_interval=None,sort_by_interval=None,pe_limit=None,ignoreds={},base_group=None,base_data_tuple=None):
        """
            def detecting(q,symbol=''):
                return q.ma_good() 
            def srt(e):
                return e.sort_by_interval_percent() 
        """
        
        symbols = cls.include_symbols(symbols,ignoreds)
        stk_group = cls(init_interval,sort_by_interval,all_intervals,pe_limit)
        stk_group.init_stockdata_dict(symbols=symbols,base_group=base_group,base_data_tuple=base_data_tuple)
        stk_group.find_potential_target(detecting,srt)
        return stk_group



    @classmethod
    def potential_groups(cls,init_intervals,sort_by_interval,all_intervals,detecting,srt,symbols=MyFavorites.pairs,pe_limit=None,ignoreds={},base_data_tuple=None):
        """
            def detecting(q,symbol=''):
                return q.ma_good() 
                #return q.sput() 
            def srt(e):
                return e.sort_by_interval_percent() 
                #return e.decrease_by_percent()
        """

        symbols = cls.include_symbols(symbols,ignoreds)        
        all_intervals = cls.cls_all_intervals if all_intervals is None else all_intervals 
        stk_group1 = cls.potential_group(
            detecting,
            srt,
            symbols=symbols,
            all_intervals=all_intervals,
            init_interval=init_intervals[0],
            sort_by_interval=sort_by_interval,
            pe_limit=pe_limit,
            ignoreds=ignoreds,
            base_data_tuple=base_data_tuple
        )
        
        stk_group2 = None if (len(init_intervals) < 2) else cls.potential_group(
            detecting,
            srt,
            symbols=None,                       # use stk_group1 remained symbols
            all_intervals=all_intervals,
            init_interval=init_intervals[1],
            sort_by_interval=sort_by_interval,
            pe_limit=pe_limit,
            ignoreds=ignoreds,
            base_data_tuple=base_data_tuple,
            base_group=stk_group1
        )
        return stk_group1, stk_group2



    @classmethod
    def new_high_stocks(cls,symbols,judge_interval,ignoreds={}):
        symbols = cls.include_symbols(symbols,ignoreds)
        dfs, alldata = dfs_for_interval(judge_interval,symbols,withInfo=True)

        def filter_top_new_high(dfs):
            high_prices = dfs.xs('High', axis=1, level=1)
            all_time_highs = high_prices.max()
            latest_high = high_prices.iloc[-1]
            at_new_high = latest_high >= all_time_highs #* 0.995  # Allow for small fluctuations (0.5% tolerance)
            stocks_at_new_high = at_new_high[at_new_high].index.tolist()
            #print('stocks',stocks_at_new_high)
            return stocks_at_new_high
 
        tickers = None if alldata is None else alldata.tickers
        return filter_top_new_high(dfs),(judge_interval,dfs,tickers)


    def __init__(self,init_interval,sort_by_interval=None,all_intervals=None,pe_limit=None,due_symbols={}):
        if sort_by_interval is None:
            sort_by_interval = init_interval
        
        if all_intervals is None: 
            if sort_by_interval == init_interval:
                all_intervals = [init_interval]
            else:
                all_intervals = [init_interval, sort_by_interval]
         
        self.init_interval = init_interval
        self.sort_by_interval = sort_by_interval
        self.all_intervals = all_intervals
        self.pe_limit = pe_limit
        self.due_symbols = due_symbols

        # the following dicts are like this: {symbol: StockData}
        self.full_dict = {}
        self.stockdata_dict = {}    
        self.potential_dict = {}

        self.potentials = []
        self.potential_symbols = []
        
        self.info = None


    #def __dir__(self):
    #    return f'{self.stockdata_dict} {self.potential_dict}'

    def select(self,dceil=95,filter='All'):
        result = []
        if self.potentials is None:
            print(f'*** DEBUG *** {self.potentials}')
        for stk_data in self.potentials:
            #print(f'*** debug {stk_data.symbol}')
            quote = stk_data.quotes[self.init_interval]
            if quote.df_predict().approved(dceil,filter):
                #print(f'*** debug {stk_data.symbol}')
                result.append(stk_data.symbol)
        return result

    def recollect_dicts(self):
        """
            for recursive detection on last result
        """
        self.stockdata_dict = self.potential_dict
        self.potential_dict = {}


    def potential_dict_add_data_for(self,interval):
        symbols = list(self.potential_dict.keys())
        if len(symbols) == 0:
            return self
        dfs, _ = dfs_for_interval(interval,symbols)
        if dfs is None:
            print(f'df is None for {interval}')
            return self 

        column_names = dfs.columns.levels[0]
        for symbol in symbols:
            if symbol in column_names:
                df = dfs[symbol]
                self.potential_dict[symbol].tidy_update_quote(interval,df).df_predict()
        return self


    # add data if there is no data_dict initialized
    def init_stockdata_dict(self,symbols=None,base_group=None,base_data_tuple=None,dfs_filter=None,withInfo=True,name_except=None):
        """
            base_data_tuple: (interval, dfs)
            dfs is got using dfs for interval
        """
        if symbols is None and base_group is None:
            print('*** no symbols to init stockdata_dict')
            return self
        
        if base_group:
            self.stockdata_dict = base_group.stockdata_dict
            self.full_dict = self.stockdata_dict
            if symbols is None:
                symbols = self.stockdata_dict.keys()
        
        # 为股票代码定义允许的字符集（只允许字母、数字、点和连字符）
        symbol_pattern = r'^[a-zA-Z0-9.-]+$'

        for interval in self.all_intervals:
            if base_group and (interval in base_group.all_intervals):
                continue

            if base_data_tuple and (base_data_tuple[0] == interval):
                dfs = base_data_tuple[1]
            else:
                dfs, alldata = dfs_for_interval(interval,symbols,withInfo)
                if alldata is not None:
                    self.set_info(alldata.tickers)

            if dfs_filter:
                column_names = dfs_filter(dfs)
            else:
                column_names = dfs.columns.levels[0]
            for symbol in symbols:
                # 验证股票代码，防止路径遍历攻击
                validated_symbol = validate_user_input(symbol, symbol_pattern)
                if validated_symbol is None or validated_symbol != symbol:
                    print(f"警告: 忽略无效或潜在危险的股票代码 '{symbol}'")
                    continue
                
                if symbol in column_names:
                    df = dfs[symbol]
                    if withInfo and name_except:
                        long_name = self.get_longName(symbol=symbol)
                        if name_except in long_name:
                            continue

                    if not self.stockdata_dict.__contains__(symbol):
                        pe_ratio = get_pe(symbol)
                        self.stockdata_dict[symbol] = self.clsStockData(symbol,self.sort_by_interval,pe_ratio)
                    self.stockdata_dict[symbol].tidy_update_quote(interval,df)
                    self.full_dict[symbol] = self.stockdata_dict[symbol] 
        return self


    def set_info(self,tickers):
        self.info = {}
        for key, value in tickers.items(): #.keys(): #['TQQQ'].info
            try:
                self.info[key] = value.info
            except Exception as e:
                print(f'*** debug {key} error: {e} ticker info: {value.info}') # value.__dict__
                self.info[key] = {}
    
    def get_longName(self,symbol):
        #print(f'**** debug [{symbol}] **** type is: {type(self.info[symbol])}')
        return self.info[symbol]['longName'] if self.info and self.info[symbol] and 'longName' in self.info[symbol] else ''

    def get_info(self,symbol):
        #print(f'**** debug [{symbol}] **** type is: {type(self.info[symbol])}')
        return self.info[symbol] #['longName'] if self.info and self.info[symbol] and 'longName' in self.info[symbol] else ''


    def get_info_df(self,symbol_list):
        return pd.DataFrame.from_dict(self.info,orient='index').loc[symbol_list]

    def get_filtered_info_df(self, symbol_list, columns, extra_columns=['bias','cnst7','velo7']):
        full_df = pd.DataFrame.from_dict(self.info, orient='index')

        # Ensure the symbol_list is valid and exists in the dataframe
        valid_symbols = [s for s in symbol_list if s in full_df.index]
        if not valid_symbols:
            return pd.DataFrame(columns=columns + extra_columns)

        # Create a new dataframe with only the specified columns
        # and handle missing columns gracefully.
        filtered_df = pd.DataFrame(index=valid_symbols)
        for col in columns:
            if col in full_df.columns:
                filtered_df[col] = full_df.loc[valid_symbols, col]
            else:
                filtered_df[col] = None # or np.nan, or a default value
        
        # Add extra columns from self.full_dict, taking the last row value for each
        for symbol in valid_symbols:
            if symbol in self.full_dict:
                stock_data = self.full_dict[symbol]
                # Access data through the Quote object in the quotes dictionary
                # using the sort_by_interval attribute
                interval = stock_data.sort_by_interval
                if hasattr(stock_data, 'quotes') and interval in stock_data.quotes:
                    quote = stock_data.quotes[interval]
                    if hasattr(quote, 'df'):
                        df = quote.df
                        for col in extra_columns:
                            if col in df.columns:
                                # Get the last value from the column
                                filtered_df.loc[symbol, col] = df[col].iloc[-1]
                            else:
                                filtered_df.loc[symbol, col] = None
                        filtered_df.loc[symbol, 'cnstvelo'] = df['cnsvel7'].iloc[-1]
                else:
                    # Set all extra columns to None if no valid data found
                    for col in extra_columns:
                        filtered_df.loc[symbol, col] = None
        
        # Round float columns while preserving type
        float_cols = filtered_df.select_dtypes(include=['float64', 'float32']).columns
        if not float_cols.empty:
            filtered_df[float_cols] = filtered_df[float_cols].round(2)  

        # Format the earningsTimestamp column
        if 'earningsTimestamp' in filtered_df.columns:
            # Convert timestamp to datetime, coercing errors to NaT (Not a Time)
            filtered_df['earningsTimestamp'] = pd.to_datetime(filtered_df['earningsTimestamp'], unit='s', errors='coerce')
            # Format the datetime to a date string, leaving NaT as is
            filtered_df['earningsTimestamp'] = filtered_df['earningsTimestamp'].dt.strftime('%Y-%m-%d')

        return filtered_df
    
    
    def find_potential_target(self,detecting,srt=None,key_interval=None,gists=True):
        # loop through all stockdata instances
        keys = self.stockdata_dict.keys()
        # it needs to convert to list here to avoid the 
        # "dictionary changed size during iteration" error
        for symbol in list(keys):
            #print(f'***** find potential_target debug {symbol}')
            self.stockdata_dict[symbol].detect_potential(stk_group=self,detecting=detecting,pe_limit=self.pe_limit,key_interval=key_interval,gists=gists)

        if srt is not None:
            self.sort_potentials(srt)
        return self



    def move_to_potentials(self,stk):
        del self.stockdata_dict[stk.symbol]
        self.potential_dict[stk.symbol] = stk
        #self.potentials.append(stk)



    def sort_potentials(self,srt,reverse=True):
        if len(self.potential_dict.keys()) > 0:
            self.potentials = list(self.potential_dict.values())
            self.potentials.sort(reverse=reverse,key=srt)
            self.potential_symbols = [stk_dt.symbol for stk_dt in self.potentials]
            #print(f'potentials sorted by {srt}: {self.potential_symbols}, reverse={reverse}')
        #else:
        #    print(f'no potentials found in {self.stockdata_dict.keys()}')


    def target(self):
        return self.potentials[0]




