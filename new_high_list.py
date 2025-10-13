import streamlit as st
import streamlit.components.v1 as components
#from streamlit_extras.stylable_container import stylable_container

import time

# Import background utility
from st_utils import set_page_background_color
from datetime import datetime # date unused
from bokeh.embed import file_html
#from os import system # Unused
#from fractions import Fraction # Unused

#from settings import MySetts # Unused
from getsymbols import get_symbols
from trading_group import Quote, StockData, StockGroup
from illustration import bokeh_draw as draw
#from spreads import CreditOptionSpread # Unused



# https://github.com/leosmigel/analyzingalpha/blob/master/2022-01-14-yfinance-python/2022-01-14-yfinance-python.ipynb

# Initialize a session state variable that tracks the sidebar state (either 'expanded' or 'collapsed').
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

# Streamlit set_page_config method has a 'initial_sidebar_state' argument that controls sidebar state.
#st.set_page_config(initial_sidebar_state=st.session_state.sidebar_state)
st.set_page_config(page_title='New Highs',layout="wide",initial_sidebar_state=st.session_state.sidebar_state)
st.sidebar.header('New Highs')


#available_intervals = ['1d', '1h', '15m', '1wk', '1mo', '1m', '2m', '5m', '30m', '60m', '5d', '3mo'] #, '90m'
selected_whole_view = True
selected_y2 = 'kdj'
#selected_interval = '1d'
selected_width = 500 #=2500 if selected_whole_view else 1200)
selected_height = 250 #if selected_stock in ['SPY','QQQ'] else 500
# Any length will be acceptable, since df[-length] will make it right
selected_length = 50

stk_and_charts = st.empty()
container = st.container()
with container:
    spinner_text = st.text('')
    info_text = st.text('')

# def setting_row(): # MOVED to extra/pages_extra.py
#     global selected_height, selected_whole_view, selected_y2, selected_width, selected_length
#     col2, col3, col4, col5, col6, col7, col8 = st.columns(7)

#     #with col1:
#     #    #selected_stock = st.text_input('Symbol', 'QQQ').upper()
#     #    selected_whole_view = st.selectbox('Whole view', [False, True])
#     with col2:
#         selected_y2 = st.selectbox('Indicator',['both','kdj','bias','none']) # 'bbbp',
#         selected_whole_view = selected_y2 == 'none'
#     with col3:
#         selected_width = st.number_input('Width', value=500) #=2500 if selected_whole_view else 1200)
#     with col4:
#         selected_height = st.number_input('Height', value=250) #if selected_stock in ['SPY','QQQ'] else 500
#     with col5:
#         # Any length will be acceptable, since df[-length] will make it right
#         selected_length = st.number_input('Bars to Display', value=50) #900 if selected_whole_view else 40)
#     #with col6:
#         #selected_interval = st.selectbox('Interval', intervals)








class StQuote(Quote):
    def plot_raw_data(self,symbol,whole_view, width=selected_width,length=selected_length,stk_group=None):
        #min(selected_length,len(df)-1)
        df = self.df[-length:]
        
        # 设置页面背景颜色
        set_page_background_color(df)
        
        symbol_info = stk_group.get_longName(symbol) 
        p = draw(symbol,df,just_data=True,whole_view=whole_view,\
            in_y2=selected_y2,width=width,height=selected_height,interval=self.interval,symbol_info=symbol_info)
        
        components.html(file_html(p, 'cdn',), width=width,height=selected_height)    
        #st.bokeh_chart(p,use_container_width=True)




class StStockData(StockData):
    # class names must be definded before use in file in Python
    clsQuote = StQuote
    # no exclusions here for manual trading

    def tidy_update_quote(self,interval,df):
        with container:
            spinner_text.text(f'Checking {self.symbol} {interval} ...')
            with st.spinner(f'{self.symbol} {interval}...'): # spinner dosen't work!
                super().tidy_update_quote(interval,df)


    def build_page(self,chart_col=None,stk_group=None):
        self.predict_quotes()

        if chart_col:
            with chart_col:
                spinner_text.text(f'Building page: {self.symbol} {getattr(StStockGroup, use_interval)}')
                self.quotes[getattr(StStockGroup, use_interval)].plot_raw_data(self.symbol,selected_whole_view,stk_group=stk_group)
                #col1,col2 = st.columns(2)
                #with col1:
                #    st.button("Buy",key=f"buy_{self.symbol}",on_click=self.buy,args=[self.symbol])
                #with col2:    
                #    st.button("Sell",key=f"sell_{self.symbol}",on_click=self.sell,args=[self.symbol])
        else:
            chrt01,chrt02 = st.columns(2)
            #chrt013,chrt04 = st.columns(2)
            with chart_pair[0]:
                spinner_text.text(f'Building page: {self.symbol} {StStockGroup.short_interval}')
                self.quotes[StStockGroup.short_interval].plot_raw_data(self.symbol,selected_whole_view,stk_group=stk_group)
            with chart_pair[1]:
                spinner_text.text(f'Building page: {self.symbol} {StStockGroup.middle_interval}')
                self.quotes[StStockGroup.middle_interval].plot_raw_data(self.symbol,selected_whole_view,stk_group=stk_group)
            #with chrt013:
            #    spinner_text.text(f'Building page: {self.symbol} {StStockGroup.long_interval}')
            #    self.quotes[StStockGroup.long_interval].plot_raw_data(self.symbol,selected_whole_view) #,width=selected_width*2,length=selected_length*2)
            #with chrt04:
            #    spinner_text.text(f'Building page: {self.symbol} {getattr(StStockGroup, use_interval)}')
            #    self.quotes[getattr(StStockGroup, use_interval)].plot_raw_data(self.symbol,selected_whole_view) #,width=selected_width*2,length=selected_length*2)



use_interval = 'large_interval' # 1wk
#use_interval = 'max_interval' # 1mo

class StStockGroup(StockGroup):
    clsStockData = StStockData
    single_chart = True

    @classmethod
    def build_tabs(cls,symbols):
        stk_group = cls.new_high_group(
            symbols,
            interval=getattr(cls,use_interval),
            pe_limit=None,
        )
        if len(stk_group.potential_symbols) == 0:
            info_text.text(f'[{datetime.now()}] no target from {symbols}') #potentials: {stk_group.potentials}')
            return
        
        top_n = 15
        p_symbols = stk_group.potential_symbols
        #print(p_symbols)
 
        p_symbols=p_symbols#[:top_n]       
        with stk_and_charts.container():
            if cls.single_chart:
                charts = []
                for i in range(0,len(p_symbols),2):
                    charts += st.columns(2)
                for idx,symbol in enumerate(p_symbols):
                    stk_group.potential_dict[symbol].build_page(charts[idx],stk_group=stk_group)
            else:
                for symbol in p_symbols:
                    stk_group.potential_dict[symbol].build_page(stk_group=stk_group)
            






type_of_symbols = 'sp500' #'active etfs'
symbols = get_symbols(type_of_symbols)
print(f'symbols: {symbols}')
first_run = True

if True: 
#while True:
    #stk_and_charts = st.empty()
    now = datetime.now()
    x = 60 #15
    mod = now.minute % x

    if (not first_run) and (mod != 0):
        #system(f'say sleeping for {mod} minutes')
        spinner_text.text(f'Sleeping @{now} ...') 
        minutes_to_sleep = x - 1 - mod
        time.sleep(60*minutes_to_sleep)
        #continue

    first_run = False
    with container, info_text.text('updating....'):
        StStockGroup.build_tabs(symbols)
    
    time.sleep(60) # preventing repeatly re-draw at the same minute
    if now.minute in [1,2]:
        spinner_text.text('update symbols ...')


#st.title('St')

#START = '2015-01-01'
#TODAY = date.today().strftime('%Y-%m-%d')
