import streamlit as st
import streamlit.components.v1 as components
from bokeh.embed import file_html
# Import background utility
from st_utils import set_page_background_color
from fohao import json as fohao_json
from illustration import bokeh_draw as draw
from favorites import MyFavorites
from trading_group import Quote, StockData, StockGroup
from getsymbols import get_symbols



# https://github.com/leosmigel/analyzingalpha/blob/master/2022-01-14-yfinance-python/2022-01-14-yfinance-python.ipynb

# Initialize a session state variable that tracks the sidebar state (either 'expanded' or 'collapsed').
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

# Streamlit set_page_config method has a 'initial_sidebar_state' argument that controls sidebar state.
#st.set_page_config(initial_sidebar_state=st.session_state.sidebar_state)
st.set_page_config(page_title='Yang',layout="wide",initial_sidebar_state=st.session_state.sidebar_state)

st.sidebar.header('Yang Inspector')

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
        
        # 设置页面背景颜色
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





all_intervals = [
    StStockGroup.max_interval,
    StStockGroup.large_interval,
    StStockGroup.long_interval,
    StStockGroup.middle_interval,
]

tab1_interval = StStockGroup.middle_interval

#init_interval = StStockGroup.middle_interval
init_interval = StStockGroup.long_interval
#init_interval = StStockGroup.max_interval

# better use this however the hourly data is not good
#sort_by_interval=StStockGroup.middle_interval
#sort_by_interval=StStockGroup.large_interval
sort_by_interval=StStockGroup.long_interval
#sort_by_interval=StStockGroup.max_interval

@st.cache_data
def set_symbols(type):
    if type == 'Pool':
        symbols = MyFavorites.pairs
    if type == 'ETF':
        actives = get_symbols('active etfs')
        print(len(actives),actives)
        trends = get_symbols('trending etfs')
        symbols = list(set(actives+trends))
    elif type == 'Stock':
        actives = get_symbols('active stocks')
        print(len(actives),actives)
        trends = get_symbols('trending stocks')
        symbols = list(set(actives+trends))
    return symbols


#@st.cache_data
@st.cache_resource
def prepare_group(symbols,pe_limit):
    stk_group = StStockGroup.all_ready(symbols,init_interval,sort_by_interval=sort_by_interval,all_intervals=all_intervals,pe_limit=pe_limit)
    return stk_group

#@st.cache_data
def refine_list(_stk_group,dceil,filter):
    symbol_list = _stk_group.select(dceil=dceil,filter=filter)
    return symbol_list



def build_page():
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    with col1:
        selected_type = st.selectbox('Type',['Pool','ETF','Stock'])    
    with col2:
        selected_y2 = st.selectbox('Indicator',['both','kdj','bias','none']) # 'bbbp',
        selected_whole_view = selected_y2 == 'none'
    with col3:
        selected_width = st.number_input('Width', value=1150) #=2500 if selected_whole_view else 1200)
    with col4:
        selected_height = st.number_input('Height', value=500) #if selected_stock in ['SPY','QQQ'] else 500
    with col5:
        # Any length will be acceptable, since df[-length] will make it right
        selected_length = st.selectbox('Bars to Display',[120,150,300,9000,500,1500,3000,5000])#st.number_input('Bars to Display', value=1000) #9000 if selected_whole_view else 900)
    with col6:
        d_ceiling = st.number_input('d <=', value=35)
    with col7:
        selected_filter = st.selectbox('Filter', ['All','breakm','watch','sell','buy','scall','sput','maGood','<BBM','>=BBM','<bb4l','<bb6l','<bbl','<cmal', '<7', '>=7', 'DonJ', 'JonD', ])
    with col8:
        symbols = set_symbols(type=selected_type)
        pe_limit = 30 if selected_type == 'Stocks' else None
        stk_group = prepare_group(symbols,pe_limit=pe_limit)
        symbol_list = refine_list(stk_group,dceil=d_ceiling,filter=selected_filter)
        selected_symbol = st.selectbox('Symbol', symbol_list)
    
    # add two tabs for each symbol
    tab1, tab2 = st.tabs(['Pairs', 'Details'])
    with tab1:
        if selected_symbol:
            paired_symbol = MyFavorites.pairs_dict.get(selected_symbol)
            for symbol in [selected_symbol,paired_symbol]:
                symbol_info = stk_group.get_longName(symbol)
                interval = tab1_interval
                q = stk_group.full_dict[symbol].quotes[interval]
                q.df_predict()
                q.plot_raw_data(
                    symbol,selected_whole_view,selected_y2,
                    width=selected_width - 30,
                    length=selected_length//2,
                    height=selected_height//2 - 20,
                    symbol_info=symbol_info
                )
                #st.write(stk_group.full_dict)
                #stk_group = prepare_group(symbols,pe_limit=pe_limit)
                #symbol_list = refine_list(stk_group,dceil=d_ceiling,filter=selected_filter)
                #selected_symbol = st.selectbox('Symbol', symbol_list)
                #stk_group = StStockGroup.all_ready(symbols,init_interval,sort_by_interval=sort_by_interval,all_intervals=all_intervals,pe_limit=pe_limit)
                #stk_group.get_quotes(selected_symbol,intervals=all_intervals)
                #stk_group.get_quotes(selected_symbol,intervals=[StStockGroup.middle_interval])
                #st.write(f'{symbol}')
        else:
            st.write('No symbol selected')

    with tab2:

        len_all_intervals = len(stk_group.all_intervals)
        num_cols = len_all_intervals//2
        row_of_cols = [st.columns(num_cols),st.columns(num_cols)]
        if selected_symbol:
            symbol_info = stk_group.get_longName(selected_symbol)
            all_intervals = stk_group.all_intervals.copy()
            for idx,intervals in enumerate([all_intervals[:2],all_intervals[2:]]):
                iterator = iter(row_of_cols[idx])
                for interval in intervals:
                    with next(iterator):
                        q = stk_group.potential_dict[selected_symbol].quotes[interval]
                        q.plot_raw_data(
                            selected_symbol,selected_whole_view,selected_y2,
                            width=selected_width//num_cols-30,
                            length=selected_length//num_cols,
                            height=selected_height//len(row_of_cols)-20,
                            symbol_info=symbol_info
                        )

    info = stk_group.info
    if info:
        st.dataframe(stk_group.get_info_df(symbol_list))
    else:
        st.write(symbol_list)

build_page()

#data='http://123.254.104.8:26/a/2/3719.m4a'
#data = "http://123.254.104.8:26/a/2/80.m4a"
#data = "http://123.254.104.8:26/a/2/653.m4a" # guang hui fa shi
#data = "http://123.254.104.8:26/a/2/58.m4a" # 4 characters 
#data = "http://123.254.104.8:26/a/2/3350.m4a" # 6 characters, li na
#data = "http://123.254.104.8:26/a/2/329.m4a"
data = "http://123.254.104.8:26/a/2/458.m4a" # huang huiyin
st.audio(data,format='audio/mp4a',autoplay=True)

st.json(fohao_json)
		