import streamlit as st
import streamlit.components.v1 as components
#import asyncio # unused
#import pandas as pd # unused
#from streamlit_extras.stylable_container import stylable_container
from bokeh.embed import file_html
#from datetime import date,datetime # unused

#import time # unused
import html
from fohao import json as fohao_json

from illustration import bokeh_draw as draw
#from fractions import Fraction # unused
from favorites import MyFavorites
#from toolfuncs import get_any_df # unused
#from spreads import CreditOptionSpread # unused
from trading_group import Quote, StockData, StockGroup
from getsymbols import get_symbols

# Import background utility
from st_utils import set_page_background_color,play_audio



# https://github.com/leosmigel/analyzingalpha/blob/master/2022-01-14-yfinance-python/2022-01-14-yfinance-python.ipynb

# Initialize a session state variable that tracks the sidebar state (either 'expanded' or 'collapsed').
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'


# Streamlit set_page_config method has a 'initial_sidebar_state' argument that controls sidebar state.
#st.set_page_config(initial_sidebar_state=st.session_state.sidebar_state)
st.set_page_config(page_title='Bull',layout="wide",initial_sidebar_state=st.session_state.sidebar_state)

st.sidebar.header('Bulls Detector')

stk_and_charts = st.empty()
container = st.container()
with container:
    spinner_text = st.text('')


class StQuote(Quote):
    #async 
    def plot_raw_data(self,symbol,whole_view,in_y2,width,length,height,symbol_info):
        #min(selected_length,len(df)-1)
        df = self.df[-length:]
        if len(df) < 1:
            spinner_text.text(f'No df of {symbol}')
            return
        
        # 设置页面背景颜色 - 传递整个数据框
        set_page_background_color(df)
        
        p = draw(symbol,df,just_data=True,whole_view=whole_view,\
            in_y2=in_y2,width=width,height=height,interval=self.interval,symbol_info=symbol_info)
        
        components.html(file_html(p, 'cdn',), width=width,height=height)    
        #st.bokeh_chart(p,use_container_width=True)


class StStockData(StockData):
    # class names must be definded before use in file in Python
    clsQuote = StQuote
    # no exclusions here for manual trading


class StStockGroup(StockGroup):
    clsStockData = StStockData
    single_chart = True


@st.cache_data
def set_symbols(type):
    if type == 'Simple':
        symbols = MyFavorites.pick_ups
    elif type == 'Bios':
        symbols = MyFavorites.bios
    elif type == 'Pairs':
        symbols = MyFavorites.pairs
    elif type == 'NS100':
        symbols = MyFavorites.ns100
    elif type == 'SP500':
        symbols = MyFavorites.spy500stks
    elif type == 'Favors':
        symbols = MyFavorites.favors
    elif type == 'Gists':
        symbols = MyFavorites.gists 
    elif type == 'Rally':
        symbols = MyFavorites.now_down
    elif type == 'Pool':
        symbols = MyFavorites.bull_pool
    elif type == 'Top_SP':
        #symbols = MyFavorites.bull_sp
        symbols = MyFavorites.top_sp
    elif type == 'ETF':
        actives = get_symbols('active etfs')
        print(len(actives),actives)
        trends = get_symbols('trending etfs')
        symbols = (set(actives+trends))
    elif type == 'Stock':
        actives = get_symbols('active stocks')
        print(len(actives),actives)
        trends = get_symbols('trending stocks')
        symbols = (set(actives+trends))
    return symbols



#@st.cache_data
@st.cache_resource
def prepare_group(symbols,interval,pe_limit,gists=True):
    stk_group = StStockGroup.bull_starting(
        symbols,
        init_interval=interval,
        sort_by_interval=interval,
        all_intervals=[interval],
        pe_limit=pe_limit,
        due_symbols={'^VIX'},
        gists=gists
    )
    return stk_group

#@st.cache_data
def refine_list(_stk_group,dceil,filter):
    symbol_list = _stk_group.select(dceil=dceil,filter=filter)
    return symbol_list



#def build_page():

if True:
    #col0, col1, col2, col4, col5, col6, col7, col8, col9, col10 = st.columns(10)
    col0, col1, col2, col4, col5, col6, col7, col8, col9 = st.columns(9)
    with col0:
        selected_type = st.selectbox('Type',['Bios','Gists','Simple','Favors','Pairs','NS100','Rally','Top_SP','Pool','SP500','ETF','Stock'])    
    with col1:
        selected_interval = st.selectbox('Interval', ['1mo','1wk','1d','1h',])
    with col2:
        selected_width = st.number_input('Width', value=1150) #=2500 if selected_whole_view else 1200)
    with col4:
        selected_height = st.number_input('Height', value=500) #if selected_stock in ['SPY','QQQ'] else 500
    with col5:
        d_ceiling = st.number_input('d <=', value=95)
    with col6:
        selected_y2 = st.selectbox('Indicator',['none','both','kdj','bias',]) # 'bbbp',
        selected_whole_view = selected_y2 == 'none'
    with col7:
        # Any length will be acceptable, since df[-length] will make it right
        selected_length = st.selectbox('Bars to Display',[150,300,600,1200,2400,4800,9600,])#st.number_input('Bars to Display', value=1000) #9000 if selected_whole_view else 900)
    with col8:
        selected_filter = st.selectbox('Filter', ['All','Foot','Fork','Leap','Potential','sput','buy','sell','scall','cmas_up','breakm','watch','maGood','<BBM','>=BBM','<bb4l','<bb6l','<bbl','<cmal', '<7', '>=7', 'DonJ', 'JonD', ])
    with col9:
        symbols = set_symbols(type=selected_type)
        pe_limit = 30 if selected_type == 'Stocks' else None
        stk_group = prepare_group(symbols,interval=selected_interval,pe_limit=pe_limit) #, gists=selected_type=='Gists')

        # This needs to be done *before* the selectbox for selected_symbol is rendered
        symbol_list = refine_list(stk_group,dceil=d_ceiling,filter=selected_filter)
        selected_symbol = st.selectbox('Symbol', symbol_list)
    
def build_page(selected_symbol=selected_symbol,stk_group=stk_group,symbol_list=symbol_list):

    #selected_y2 = 'kdj' 

    len_all_intervals = len(stk_group.all_intervals)
    # add two tabs for each symbol
    #tab1, tab2 = st.tabs(['Pair', 'Details'])
    #with tab1:
    if selected_symbol:
        symbol = selected_symbol

        #paired_symbol = MyFavorites.pairs_dict.get(selected_symbol)
        #for symbol in [selected_symbol]: #[selected_symbol,paired_symbol]:
        symbol_info = stk_group.get_longName(symbol)
        interval = selected_interval
        q = stk_group.full_dict[symbol].quotes[interval]
        
        #q.df_predict()
        
        q.plot_raw_data(
            symbol,selected_whole_view,selected_y2,
            width=selected_width - 30,
            length=selected_length, #//2,
            height=selected_height//(len_all_intervals) - 10,
            symbol_info=symbol_info
        )
        info = stk_group.get_info(symbol)
        st.write(info)
    else:
        st.write('No symbol selected')

    

    group_info = stk_group.info
    if group_info:
        df = stk_group.get_info_df(symbol_list)
        st.dataframe(df)
        # write all column names in a list
        # st.write('Columns:')
        # st.write(df.columns.tolist())
        #st.write(df.columns)
    else:
        st.write(symbol_list)

    play_audio()

build_page()

#data='http://123.254.104.8:26/a/2/3719.m4a'
#data = "http://123.254.104.8:26/a/2/80.m4a"
#data = "http://123.254.104.8:26/a/2/653.m4a" # guang hui fa shi
#data = "http://123.254.104.8:26/a/2/58.m4a" # 4 characters 
#data = "http://123.254.104.8:26/a/2/3350.m4a" # 6 characters, li na
#data = "http://123.254.104.8:26/a/2/329.m4a"
#data = "http://123.254.104.8:26/a/2/458.m4a" # huang huiyin


#st.json(fohao_json)

# # For a local audio file
# local_file_path = './local_458.m4a'  # Ensure the file is in the same directory as your script

# # Read the local audio file
# with open(local_file_path, 'rb') as audio_file:
#     data = audio_file.read()
# st.audio(data,format='audio/mp4a',autoplay=True)
