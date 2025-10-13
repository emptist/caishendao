import streamlit as st
import streamlit.components.v1 as components
#from streamlit_extras.stylable_container import stylable_container
from bokeh.embed import file_html
from datetime import datetime # date unused
# Import background utility
from st_utils import set_page_background_color
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
st.set_page_config(page_title='detector',layout="wide",initial_sidebar_state=st.session_state.sidebar_state)


#available_intervals = ['1d', '1h', '15m', '1wk', '1mo', '1m', '2m', '5m', '30m', '60m', '5d', '3mo'] #, '90m'
selected_whole_view = False
selected_y2 = 'kdj'
#selected_interval = '1d'
selected_width = 595 #=2500 if selected_whole_view else 1200)
selected_height = 250 #if selected_stock in ['SPY','QQQ'] else 500
# Any length will be acceptable, since df[-length] will make it right
selected_length = 80

stk_and_charts = st.empty()
container = st.container()
with container:
    spinner_text = st.text('')

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








class StQuote(Quote):
    def plot_raw_data(self,symbol,whole_view, width=selected_width,length=selected_length):
        #min(selected_length,len(df)-1)
        df = self.df[-length:]
        
        # 设置页面背景颜色
        set_page_background_color(df)
        
        p = draw(symbol,df,just_data=True,whole_view=whole_view,
            in_y2=selected_y2,width=width,height=selected_height,interval=self.interval)
        
        components.html(file_html(p, 'cdn',), width=width,height=selected_height)    
        #st.bokeh_chart(p,use_container_width=True)




class StStockData(StockData):
    # class names must be definded before use in file in Python
    clsQuote = StQuote
    #clsStockGroup = StStockGroup
    # no exclusions here for manual trading

    def tidy_update_quote(self,interval,df):
        with container:
            spinner_text.text(f'Checking {self.symbol} {interval} ...')
            with st.spinner(f'{self.symbol} {interval}...'): # spinner dosen't work!
                super().tidy_update_quote(interval,df)



    # build instance page(tab)
    def build_page(self):
        chrt01,chrt02 = st.columns([1,1])
        chrt013,chrt04 = st.columns([1,1])

        self.predict_quotes()

        with chrt01:
            spinner_text.text(f'Building page: {self.symbol} {StStockGroup.short_interval}')
            self.quotes[StStockGroup.short_interval].plot_raw_data(self.symbol,selected_whole_view)
        with chrt02:
            spinner_text.text(f'Building page: {self.symbol} {StStockGroup.middle_interval}')
            self.quotes[StStockGroup.middle_interval].plot_raw_data(self.symbol,selected_whole_view)
        with chrt013:
            spinner_text.text(f'Building page: {self.symbol} {StStockGroup.long_interval}')
            self.quotes[StStockGroup.long_interval].plot_raw_data(self.symbol,selected_whole_view) #,width=selected_width*2,length=selected_length*2)
        with chrt04:
            spinner_text.text(f'Building page: {self.symbol} {StStockGroup.max_interval}')
            self.quotes[StStockGroup.max_interval].plot_raw_data(self.symbol,selected_whole_view) #,width=selected_width*2,length=selected_length*2)





class StStockGroup(StockGroup):
    clsStockData = StStockData

    @classmethod
    def build_tabs(cls,symbols=MyFavorites.pairs_4_trade):
        all_intervals = [
            cls.short_interval,
            cls.middle_interval,
            cls.long_interval,
            #cls.large_interval,
            cls.max_interval
        ] 
        def detecting(q):
            return q.avrgs_bull() 
        def srt(e):
            return e.increase_by_percent() 
        
        stk_group, stk_group2 = cls.potential_groups(
            [cls.short_interval,cls.long_interval],
            cls.sort_by_interval,
            all_intervals,
            detecting,
            srt,
            symbols
        )
        if len(stk_group.potential_symbols) == 0:
            if len(stk_group2.potential_symbols) == 0:
                st.info(f'[{datetime.now()}] no target from {symbols}') #potentials: {stk_group.potentials}')
                return
        #system(f'say targe {stk_group.potential_symbols[0]}')
        tabs = []
        n = min(
            max(3,4-len(stk_group2.potential_symbols)),
            len(stk_group.potential_symbols)
        )
        for symbol in stk_group.potential_symbols[:min(n,len(stk_group.potential_symbols))]:
            tabs.append(symbol)
        num_elem1 = len(tabs)
        n = 4-num_elem1
        for symbol in stk_group2.potential_symbols[:min(n,len(stk_group2.potential_symbols))]:
            tabs.append(symbol)
        
        with stk_and_charts.container():
            for idx, tab in enumerate(st.tabs(tabs)):
                with tab:
                    if idx < num_elem1:
                        stk_group.potentials[idx].build_page()
                    else:
                        stk_group2.potentials[idx - num_elem1].build_page()

            st.info(f'[{datetime.now()}] potentials {stk_group.init_interval}: {stk_group.potential_symbols}, {stk_group2.init_interval}: {stk_group2.potential_symbols}') #potentials: {stk_group.potentials}')
            #spinner_text.text(f'[{datetime.now()}] potentials {stk_group.init_interval}: {stk_group.potential_symbols}, {stk_group2.init_interval}: {stk_group2.potential_symbols}') #potentials: {stk_group.potentials}')
            #setting_row()
            







#if True: 
first_run = True
while True:
    #stk_and_charts = st.empty()
    now = datetime.now()
    mod_15 = now.minute % 15

    if (first_run == False) and mod_15 != 0:
    #if (15 > mod_15 >= 14):
        #system(f'say sleeping for {mod_15} minutes')
        spinner_text.text(f'Sleeping @{now} ...') 
        minutes_to_sleep = 14 - mod_15
        time.sleep(60*minutes_to_sleep)
        #continue
    with container, st.spinner('updating....'):
        StStockGroup.build_tabs()
    
    time.sleep(60) # preventing repeatly re-draw at the same minute
    first_run = False

#st.title('St')

#START = '2015-01-01'
#TODAY = date.today().strftime('%Y-%m-%d')
