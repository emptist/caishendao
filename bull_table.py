import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from bokeh.embed import file_html
#import html
#import requests
#import json

from illustration import bokeh_draw as draw
from favorites import MyFavorites
from settings import MySetts
from trading_group import Quote, StockData, StockGroup
from getsymbols import get_symbols

# Import AI analysis function
from ai_analysis import st_ai_analysis_area
from st_utils import set_page_background_color



# Initialize a session state variable that tracks the sidebar state (either 'expanded' or 'collapsed').
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

st.set_page_config(page_title='Bull',layout="wide",initial_sidebar_state=st.session_state.sidebar_state)

st.sidebar.header('Bulls Detector')

stk_and_charts = st.empty()
container = st.container()
with container:
    spinner_text = st.text('')


# bull_table应用专用配置
class BullTableSettings:
    # UI配置项
    stock_types = ['Indices','Gists','Bios','Simple','Favors','NS100','Top_SP','SP500','Pairs','Rally']
    intervals = ['1d','1mo','1wk','1h']
    filters = ['All','Foot','Fork','Leap','Potential','sput','buy','sell','scall','cmas_up','breakm','watch','maGood','<BBM','>=BBM','<bb4l','<bb6l','<bbl','<cmal', '<7', '>=7', 'DonJ', 'JonD']
    indicators = ['none','consis','both','kdj','bias']
    display_lengths = [150,300,600,1200,2400,4800,9600]
    
    # 默认配置
    default_width = 1100
    default_height = 500
    default_d_ceiling = 105
    default_pe_limit = 30


class StQuote(Quote):
    #async 
    def plot_raw_data(self,symbol,whole_view,in_y2,width,length,height,symbol_info):
        #min(selected_length,len(df)-1)
        df = self.df[-length:]
        if len(df) < 1:
            spinner_text.text(f'No df of {symbol}')
            return

        p = draw(symbol,df,just_data=True,whole_view=whole_view,\
            in_y2=in_y2,width=width,height=height,interval=self.interval,symbol_info=symbol_info)
        
        components.html(file_html(p, 'cdn',), width=width,height=height)    
        #st.bokeh_chart(p,use_container_width=True)
        set_page_background_color(df)


class StStockData(StockData):
    # class names must be definded before use in file in Python
    clsQuote = StQuote
    # no exclusions here for manual trading


class StStockGroup(StockGroup):
    """Streamlit专用的Stock组类，继承自StockGroup
    
    用于在Streamlit应用中处理和展示多只Stock的数据
    
    Attributes:
        clsStockData: 使用StStockData类处理单只Stock数据
    """
    clsStockData = StStockData


@st.cache_data(ttl=3600)  # 缓存60分钟
def set_symbols(type):
    """根据类型获取Stock/ETF代码列表
    
    Args:
        type (str): Stock/ETF类型，如'Simple'、'Bios'、'Pairs'等
        
    Returns:
        set: 对应类型的Stock/ETF代码集合
    """
    if type == 'Simple':
        symbols = MyFavorites.pick_ups
    elif type == 'Indices':
        symbols = MyFavorites.indices
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
        symbols = set(actives+trends)
    elif type == 'Stock':
        actives = get_symbols('active stocks')
        print(len(actives),actives)
        trends = get_symbols('trending stocks')
        symbols = set(actives+trends)
    return symbols




@st.cache_resource(ttl=3600)  # 缓存1小时
def prepare_group(symbols_set, interval, pe_limit, gists=True):
    """准备Stock组数据
    
    Args:
        symbols_set (set): Stock代码集合，用于缓存健壮性
        interval (str): 时间间隔
        pe_limit (int): 市盈率限制
        gists (bool): 是否使用gists
        
    Returns:
        StStockGroup: 包含指定Stock的StStockGroup实例
    """
    stk_group = StStockGroup.bull_starting(
        symbols_set,
        init_interval=interval,
        sort_by_interval=interval,
        all_intervals=[interval],
        pe_limit=pe_limit,
        due_symbols={'NVDA','SHLD'},
        gists=gists
    )
    return stk_group


def refine_list(_stk_group,dceil,filter):
    """根据筛选条件优化Stock列表
    
    Args:
        _stk_group (StStockGroup): StStockGroup实例
        dceil (int): d值上限
        filter (str): 筛选条件
        
    Returns:
        list: 符合条件的Stock代码列表
    """
    symbol_list = _stk_group.select(dceil=dceil,filter=filter)
    return symbol_list


#-- AI functions have been moved to ai_analysis.py module
#-- All AI-related functionality is now handled by the imported ai_analysis module


def build_page():
    """构建Streamlit应用页面，包括控件、表格和图表展示
    
    功能包括：
    - 提供各种筛选控件供用户选择
    - 展示Stock数据表格
    - 根据用户选择绘制Stock图表
    - 生成并显示AI分析报告
    - 播放提示音频
    """

    # --- Controls ---
    col0, col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(10)
    with col0:
        selected_type = st.selectbox('Type', BullTableSettings.stock_types)
    with col1:
        selected_interval = st.selectbox('Interval', BullTableSettings.intervals)
    with col2:
        selected_width = st.number_input('Width', value=BullTableSettings.default_width)
    with col3:
        # Add AI Provider selection
        ai_provider = st.selectbox('AI Provider',  ['alibabacloud','gemini', ] if MySetts.use_proxy else ['gemini','alibabacloud'])
    with col4:
        selected_height = st.number_input('Height', value=BullTableSettings.default_height)
    with col5:
        d_ceiling = st.number_input('d <=', value=BullTableSettings.default_d_ceiling)
    with col6:
        selected_y2 = st.selectbox('Indicator', BullTableSettings.indicators)
        selected_whole_view = selected_y2 == 'none'
    with col7:
        # Any length will be acceptable, since df[-length] will make it right
        selected_length = st.selectbox('Bars to Display', BullTableSettings.display_lengths)
    with col8:
        selected_filter = st.selectbox('Filter', BullTableSettings.filters)
    with col9:
        symbols = set_symbols(type=selected_type)
        pe_limit = BullTableSettings.default_pe_limit if selected_type == 'Stocks' else None
        stk_group = prepare_group(symbols, interval=selected_interval, pe_limit=pe_limit) #, gists=selected_type=='Gists')

        # This needs to be done *before* the selectbox for selected_symbol is rendered
        symbol_list = refine_list(stk_group,dceil=d_ceiling,filter=selected_filter)
        st.session_state.selected_symbol = symbol_list[0] if symbol_list else None
        #print('selected_symbol: ', st.session_state.selected_symbol, symbol_list)

        # Initialize or get the selected symbol from session state
        # if 'selected_symbol' not in st.session_state:
        #     st.session_state.selected_symbol = symbol_list[0] if symbol_list else None

        # # Ensure the selected symbol is still in the current list
        # if st.session_state.selected_symbol not in symbol_list:
        #     st.session_state.selected_symbol = symbol_list[0] if symbol_list else None


    len_all_intervals = len(stk_group.all_intervals)
    # This is the list of columns we want to display in our table.
    info_columns = [
        #'longName', 
        'numberOfAnalystOpinions',
        'recommendationKey',
        'currentPrice',
        'targetMedianPrice',
        'targetMeanPrice',
        'targetLowPrice',
        'targetHighPrice',
        #'regularMarketChange', 
        #'regularMarketChangePercent', 
        #'regularMarketVolume',
        'trailingPE', 
        'forwardPE',  
        'marketCap', 
        'earningsTimestamp', 
        'shortRatio', 
        'heldPercentInstitutions', 
        'heldPercentInsiders',
        'totalCash', 
        'totalDebt',
    ]

    group_info = stk_group.info
    if group_info and symbol_list:
        # Use the new method to get a filtered dataframe
        df = stk_group.get_filtered_info_df(symbol_list, columns=info_columns)

        # Move bias, cnst7, velo7, cnstvelo, trailingPE columns to the front for easier ordering
        # Get the current columns
        cols = df.columns.tolist()
        # Define the columns we want to move to the front
        special_cols = ['bias','cnstvelo', 'cnst7', 'velo7','trailingPE']
        # Create new column order: special_cols followed by other columns
        new_cols = []
        for col in special_cols:
            if col in cols:
                new_cols.append(col)
                cols.remove(col)
        # Add the remaining columns
        new_cols.extend(cols)
        # Reorder the dataframe
        df = df[new_cols]

        # Add the 'symbol' column to the dataframe, which is currently in the index
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'symbol'}, inplace=True)

        # Sort by number of analyst opinions
        #if 'numberOfAnalystOpinions' in df.columns:
        #    df.sort_values('numberOfAnalystOpinions', ascending=False, inplace=True, na_position='last')
        
        # sort by cnstvelo
        df.sort_values('cnstvelo', ascending=False, inplace=True, na_position='last')

        # --- AG Grid Table Implementation ---

        # Configure the grid options
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection(
            'single',
            use_checkbox=False,
            #pre_selected_rows= [i for i, sym in enumerate(df['symbol']) if sym == st.session_state.selected_symbol] # Pre-select the row
        )
        # Configure default columns with width constraints
        gb.configure_default_column(
            maxWidth=60,  # Limit maximum column width to 200px
            minWidth=40,   # Set minimum column width to 40px
            width=55,       # Default column width of 55px
            sortable=True, 
            resizable=True, 
            filterable=True,
            #domLayout=['autoHeight','autoSize'],
        )

        gridOptions = gb.build()

        # Manually add grid options for auto-sizing and auto-height
        gridOptions['domLayout'] = 'autoHeight'
        
        # Removed autoSizeStrategy to use fixed widths for better control
        # gridOptions['autoSizeStrategy'] = {'type': 'fitCellContents'}

        # Display the grid
        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.AS_INPUT,
            width='100%',
            allow_unsafe_jscode=True,  # Set it to True to allow jsfunction to be injected
            enable_enterprise_modules=False,
            key='stock_grid' # Add a key to avoid recreation issues
        )

        # If a new row is selected in the grid, update the selected_symbol
        # and rerun the script to update the chart
        selected_rows = grid_response['selected_rows']
        if selected_rows is not None:
            if not selected_rows.empty and selected_rows.iloc[0]['symbol'] != st.session_state.selected_symbol:
                st.session_state.selected_symbol = selected_rows.iloc[0]['symbol']

    elif symbol_list:
        st.write(symbol_list)
    else:
        st.write("No stocks found matching the criteria.")

    # If a symbol is selected (either from the dropdown or the grid), draw the chart
    if st.session_state.selected_symbol:
        # --- Charting area ---
        symbol = st.session_state.selected_symbol
        symbol_info = stk_group.get_longName(symbol)
        interval = selected_interval
        q = stk_group.full_dict[symbol].quotes[interval]
        q.plot_raw_data(
            symbol, selected_whole_view, selected_y2,
            width=selected_width - 30,
            length=selected_length,
            height=selected_height // len_all_intervals - 10,
            symbol_info=symbol_info
        )
        # --- AI analysis area ---
        info = stk_group.get_info(symbol)
        st_ai_analysis_area(symbol,info,ai_provider, session_state=st.session_state)

    else:
        st.write('No symbol selected')
    
build_page()


import os
local_file_path = './dizang.mp3'  # Ensure the file is in the same directory as your script
# Read the local audio file with error handling
if os.path.exists(local_file_path):
    try:
        with open(local_file_path, 'rb') as audio_file:
            data = audio_file.read()
        st.audio(data,format='audio/mp3',autoplay=True)
    except Exception as e:
        st.warning(f"Can't play audio: {e}")
else:
    st.info(f"File not found: {local_file_path}")