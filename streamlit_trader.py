import streamlit as st
import streamlit.components.v1 as components
#from streamlit_extras.stylable_container import stylable_container
from bokeh.embed import file_html
# Import background utility
from st_utils import set_page_background_color
from datetime import datetime # date unused
import time

from illustration import bokeh_draw as draw
from favorites import MyFavorites
from trading_group import Quote, StockData, StockGroup

# https://github.com/leosmigel/analyzingalpha/blob/master/2022-01-14-yfinance-python/2022-01-14-yfinance-python.ipynb

# Initialize a session state variable that tracks the sidebar state (either 'expanded' or 'collapsed').
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

# Streamlit set_page_config method has a 'initial_sidebar_state' argument that controls sidebar state.
#st.set_page_config(initial_sidebar_state=st.session_state.sidebar_state)
st.set_page_config(page_title='Trader',layout="wide",initial_sidebar_state=st.session_state.sidebar_state)


selected_whole_view = False
selected_y2 = 'kdj'
selected_width = 570 #=2500 if selected_whole_view else 1200)
selected_height = 250 #if selected_stock in ['SPY','QQQ'] else 500
# Any length will be acceptable, since df[-length] will make it right
selected_length = 50 #100

stk_and_charts = st.empty()
container = st.container()
with container:
    spinner_text = st.text('')


class StQuote(Quote):
    #async 
    def plot_raw_data(self,symbol,whole_view, width=selected_width,length=selected_length):
        df = self.df[-length:]
        if len(df) < 1:
            spinner_text.text(f'No df of {symbol}')
            return
        
        # 设置页面背景颜色
        set_page_background_color(df)
        
        p = draw(symbol,df,just_data=True,whole_view=whole_view,\
            in_y2=selected_y2,width=width,height=selected_height,interval=self.interval)
        
        components.html(file_html(p, 'cdn',), width=width,height=selected_height)    
        #st.bokeh_chart(p,use_container_width=True)




class StStockData(StockData):
    # class names must be definded before use in file in Python
    clsQuote = StQuote
    # no exclusions here for manual trading

    def tidy_update_quote(self,interval,df):
        with container:
            spinner_text.text(f'Checking {self.symbol} {interval} ...')
            #with st.spinner(f'{self.symbol} {interval}...'): # spinner dosen't work!
            super().tidy_update_quote(interval,df)


    # build instance page(tab)
    def build_page(self,chart_col=None):
        self.predict_quotes()

        if chart_col:
            with chart_col:
                spinner_text.text(f'Building page: {self.symbol} {StStockGroup.current_interval}')
                self.quotes[StStockGroup.current_interval].plot_raw_data(self.symbol,selected_whole_view)
                #col1,col2 = st.columns(2)
                #with col1:
                #    st.button("Buy",key=f"buy_{self.symbol}",on_click=self.buy,args=[self.symbol])
                #with col2:    
                #    st.button("Sell",key=f"sell_{self.symbol}",on_click=self.sell,args=[self.symbol])
        else:
            chrt01,chrt02 = st.columns(2)
            #chrt013,chrt04 = st.columns(2)
            with chrt01: #chart_pair[0]:
                spinner_text.text(f'Building page: {self.symbol} {StStockGroup.current_interval}')
                self.quotes[StStockGroup.current_interval].plot_raw_data(self.symbol,selected_whole_view)
            with chrt02: #chart_pair[1]:
                spinner_text.text(f'Building page: {self.symbol} {StStockGroup.middle_interval}')
                self.quotes[StStockGroup.middle_interval].plot_raw_data(self.symbol,selected_whole_view)
            #with chrt013:
            #    spinner_text.text(f'Building page: {self.symbol} {StStockGroup.long_interval}')
            #    self.quotes[StStockGroup.long_interval].plot_raw_data(self.symbol,selected_whole_view) #,width=selected_width*2,length=selected_length*2)
            #with chrt04:
            #    spinner_text.text(f'Building page: {self.symbol} {StStockGroup.max_interval}')
            #    self.quotes[StStockGroup.max_interval].plot_raw_data(self.symbol,selected_whole_view) #,width=selected_width*2,length=selected_length*2)


    #@st.dialog("Submission")
    #def buy(self,symbol):
        #spinner_text.text
    #    print(f'buy {symbol} at {self.price()}')

    #@st.dialog("Submission")
    #def sell(self,symbol):
    #    spinner_text.text(f'sell {symbol} at {self.price()}')

    #def price(self):
    #    return self.quotes[StStockGroup.current_interval].df.close.iloc[-1]



class StStockGroup(StockGroup):
    clsStockData = StStockData
    single_chart = True
    current_interval = '1h' #'1d' # #'15m' #'1h' #cls.short_interval

    @classmethod
    def build_tabs(cls,symbols):
        stk_group = cls.trade_group(symbols,cls.current_interval,cls.current_interval,all_intervals=[cls.current_interval])
        with stk_and_charts.container():
            if cls.single_chart:
                charts = []
                for i in range(0,len(symbols),2):
                    charts += st.columns(2)
                for idx,symbol in enumerate(symbols):
                    stk_group.stockdata_dict[symbol].build_page(charts[idx])
            else:
                for symbol in symbols:
                    stk_group.stockdata_dict[symbol].build_page()
            





def sleep(first_run):
    now = datetime.now()
    x = 15
    mod = now.minute % x

    if (not first_run) and (mod != 0):
        #system(f'say sleeping for {mod} minutes')
        spinner_text.text(f'Sleeping @{now} ...') 
        minutes_to_sleep = x - 1 - mod
        time.sleep(60*minutes_to_sleep)
        #continue

first_run = True
#if True: 
while True:
    #stk_and_charts = st.empty()
    sleep(first_run)
    first_run = False
    with container, st.spinner('updating....'):
        StStockGroup.build_tabs(MyFavorites.pairs_4_trade)
    
    time.sleep(60) # preventing repeatly re-draw at the same minute
    





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
#         selected_length = st.number_input('Bars to Display', value=900 if selected_whole_view else 40)
#     #with col6:
#         #selected_interval = st.selectbox('Interval', intervals)

