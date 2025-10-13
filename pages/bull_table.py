import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from bokeh.embed import file_html

from illustration import bokeh_draw as draw
from favorites import MyFavorites
from settings import MySetts
from trading_group import Quote, StockData, StockGroup
from getsymbols import get_symbols

# Import AI analysis function
from ai_analysis import st_ai_analysis_area
from st_utils import set_page_background_color, play_audio
from streamlit_js_eval import streamlit_js_eval



# Initialize a session state variable that tracks the sidebar state (either 'expanded' or 'collapsed').
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

st.set_page_config(page_title='Bull',layout="wide",initial_sidebar_state=st.session_state.sidebar_state)

st.sidebar.header('Bulls Detector')

#stk_and_charts = st.empty()
#container = st.container()
# with container:
#     spinner_text = st.text('')


# Bull Table Application Configuration
class BullTableSettings:
    # UI Configuration Items
    stock_types = ['Indices','Gists','Bios','Simple','Favors','NS100','Top_SP','SP500','Pairs','Rally']
    intervals = ['1d','1h','30m','15m','1wk','1mo']
    filters = ['All','Foot','Fork','Leap','Potential','sput','buy','sell','scall','cmas_up','breakm','watch','maGood','<BBM','>=BBM','<bb4l','<bb6l','<bbl','<cmal', '<7', '>=7', 'DonJ', 'JonD']
    indicators = ['none','consis','both','kdj','bias']
    display_lengths = [150,300,600,1200,2400,4800,9600]
    
    # Default Configuration
    default_width = 1150
    default_height = 500
    default_d_ceiling = 105
    default_pe_limit = 30


class StQuote(Quote):
    #async 
    def plot_raw_data(self,symbol,whole_view,in_y2,length,height,symbol_info):
        #min(selected_length,len(df)-1)
        df = self.df[-length:]
        if len(df) < 1 or not hasattr(df, 'j'):
            #spinner_text.text(f'No df of {symbol}')
            return

        p = draw(symbol,df,just_data=True,whole_view=whole_view,
            in_y2=in_y2,height=height,interval=self.interval,symbol_info=symbol_info)
        
        components.html(file_html(p, 'cdn',), width=None,height=height)    
        #st.bokeh_chart(p,use_container_width=True)
        set_page_background_color(df)


class StStockData(StockData):
    # class names must be definded before use in file in Python
    clsQuote = StQuote
    # no exclusions here for manual trading


class StStockGroup(StockGroup):
    """Streamlit-specific Stock Group class, inherited from StockGroup
    
    Used for processing and displaying multiple stocks' data in Streamlit applications
    
    Attributes:
        clsStockData: Uses StStockData class to process individual stock data
    """
    clsStockData = StStockData


@st.cache_data(ttl=600)
def set_symbols(type):
    """Get stock/ETF symbols list based on type
    
    Args:
        type (str): Stock/ETF type, such as 'Simple', 'Bios', 'Pairs', etc.
        
    Returns:
        set: Collection of stock/ETF symbols for the specified type
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




@st.cache_resource(ttl=600)
def prepare_group(symbols_set, interval, pe_limit):
    """Prepare stock group data
    
    Args:
        symbols_set (set): Stock symbols collection for cache robustness
        interval (str): Time interval
        pe_limit (int): PE ratio limit
        
    Returns:
        StStockGroup: StStockGroup instance containing the specified stocks
    """
    
    reserved_set = {'GDX','GDXU','GLD','UGL'}

    stk_group = StStockGroup.bull_starting(
        symbols_set.union(reserved_set),
        init_interval=interval,
        sort_by_interval=interval,
        all_intervals=[interval],
        pe_limit=pe_limit,
        due_symbols={},
    )
    return stk_group


def refine_list(_stk_group,dceil,filter):
    """Refine stock list based on filtering conditions
    
    Args:
        _stk_group (StStockGroup): StStockGroup instance
        dceil (int): Maximum d-value
        filter (str): Filtering condition
        
    Returns:
        list: List of stock symbols that meet the conditions
    """
    symbol_list = _stk_group.select(dceil=dceil,filter=filter)
    return symbol_list


#-- AI functions have been moved to ai_analysis.py module
#-- All AI-related functionality is now handled by the imported ai_analysis module


def build_page():
    """Build Streamlit application page, including controls, tables, and chart displays
    
    Features include:
    - Provide various filtering controls for user selection
    - Display stock data table
    - Draw stock charts based on user selection
    - Generate and display AI analysis reports
    - Play notification audio
    """

    # --- Controls ---
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    with col2:
        selected_type = st.selectbox('Type', BullTableSettings.stock_types)
    with col5:
        selected_interval = st.selectbox('Interval', BullTableSettings.intervals)
    with col1:
        # Add AI Provider selection
        ai_provider = st.selectbox('AI Provider',  ['alibabacloud','gemini', ] if MySetts.use_proxy else ['gemini','alibabacloud'])
    with col3:
        selected_height = st.number_input('Height', value=BullTableSettings.default_height)
    with col4:
        d_ceiling = st.number_input('d <=', value=BullTableSettings.default_d_ceiling)
    with col7:
        selected_y2 = st.selectbox('Indicator', BullTableSettings.indicators)
        selected_whole_view = selected_y2 == 'none'
    with col6:
        # Any length will be acceptable, since df[-length] will make it right
        selected_length = st.selectbox('Chart Bars', BullTableSettings.display_lengths)
    with col8:
        selected_filter = st.selectbox('Filter', BullTableSettings.filters)
    # with col9:
    #     """
    #     """

    symbols = set_symbols(type=selected_type)
    pe_limit = BullTableSettings.default_pe_limit if selected_type == 'Stocks' else None
    stk_group = prepare_group(symbols, interval=selected_interval, pe_limit=pe_limit)

    # This needs to be done *before* the selectbox for selected_symbol is rendered
    symbol_list = refine_list(stk_group,dceil=d_ceiling,filter=selected_filter)
    
    # Only set default value on first page load or when no stock is selected, to avoid overriding user selection
    if 'selected_symbol' not in st.session_state or st.session_state.selected_symbol is None:
        st.session_state.selected_symbol = symbol_list[0] if symbol_list else None
    # Ensure the selected stock is still in the current list
    elif st.session_state.selected_symbol not in symbol_list:
        st.session_state.selected_symbol = symbol_list[0] if symbol_list else None
    
    # Commented out - this line would reset the selected stock on every page run
    # st.session_state.selected_symbol = symbol_list[0] if symbol_list else None

    # --- Charting area --- (Now above the table)
    len_all_intervals = len(stk_group.all_intervals)
    if st.session_state.selected_symbol:
        # Always display the chart with the current selected symbol from session state
        symbol = st.session_state.selected_symbol
        symbol_info = stk_group.get_longName(symbol)
        interval = selected_interval
        q = stk_group.full_dict[symbol].quotes[interval]
        q.plot_raw_data(
            symbol, selected_whole_view, selected_y2,
            length=selected_length,
            height=selected_height // len_all_intervals - 10,
            symbol_info=symbol_info
        )
    else:
        st.write('No symbol selected')

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
    selected_rows_data = None
    
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

        # sort by cnstvelo
        df.sort_values('cnstvelo', ascending=False, inplace=True, na_position='last')

        # --- AG Grid Table Implementation ---

        # Get screen height to make the grid responsive
        screen_height = streamlit_js_eval(js_expressions='screen.height', want_output=True, key='SCR_H')

        # Set a default screen height if the JS evaluation fails
        if screen_height is None:
            screen_height = 800  # A reasonable default

        # Calculate x% of the screen height as the maximum height
        grid_height = screen_height * 0.2

        # Configure the grid options
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection(
            'single',
            use_checkbox=False,
            # Pre-select the row that matches the current selected_symbol
            pre_selected_rows= [i for i, sym in enumerate(df['symbol']) if sym == st.session_state.selected_symbol] 
        )
        # Configure default columns with width constraints
        gb.configure_default_column(
            maxWidth=60,  # Limit maximum column width to 200px
            minWidth=40,   # Set minimum column width to 40px
            width=55,       # Default column width of 55px
            sortable=True, 
            resizable=True, 
            filterable=True,
        )

        gridOptions = gb.build()

        # Display the grid
        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            height=grid_height,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.AS_INPUT,
            width='100%',
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            key='stock_grid'
        )

        # Store selected rows data for later use
        selected_rows_data = grid_response['selected_rows']

    elif symbol_list:
        st.write(symbol_list)
    else:
        st.write("No stocks found matching the criteria.")

    # Update session state with selected symbol from grid
    if selected_rows_data is not None and not selected_rows_data.empty:
        selected_symbol_from_grid = selected_rows_data.iloc[0]['symbol']
        if selected_symbol_from_grid != st.session_state.selected_symbol:
            st.session_state.selected_symbol = selected_symbol_from_grid
            # Force rerun to update chart with new selection using Streamlit's proper mechanism
            st.rerun()

    # --- AI analysis area ---
    if st.session_state.selected_symbol:
        symbol = st.session_state.selected_symbol
        info = stk_group.get_info(symbol)
        st_ai_analysis_area(symbol,info,ai_provider, session_state=st.session_state)

    
    play_audio()
build_page()

