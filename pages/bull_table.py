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


# bull_table应用专用配置
class BullTableSettings:
    #stock_types = ['Indices','Gists','Bios','Simple','Favors','NS100','Top_SP','SP500','Pairs','Rally']
    stock_types = ['Indices','Bios','Gists','Simple']
    intervals = ['1h','30m','15m','1d','1wk','1mo']
    filters = ['All','Foot','Fork','Leap','Potential','sput','buy','sell','scall','cmas_up','breakm','watch','maGood','<BBM','>=BBM','<bb4l','<bb6l','<bbl','<cmal', '<7', '>=7', 'DonJ', 'JonD']
    indicators = ['none','consis','both','kdj','bias']
    display_lengths = [150,300,600,1200,2400,4800,9600]
    
    default_width = 1150
    default_height = 500
    default_d_ceiling = 105
    default_pe_limit = 30


class StQuote(Quote):
    # never add: async 
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
    clsStockData = StStockData


@st.cache_data(ttl=600)
def set_symbols(type):
    
    if type == 'Indices':
        symbols = MyFavorites.indices
    elif type == 'Bios':
        symbols = MyFavorites.bios
    elif type == 'Gists':
        symbols = MyFavorites.gists
    elif type == 'Simple':
        symbols = MyFavorites.pick_ups

    # elif type == 'Pairs':
    #     symbols = MyFavorites.pairs
    # elif type == 'NS100':
    #     symbols = MyFavorites.ns100
    # elif type == 'SP500':
    #     symbols = MyFavorites.spy500stks
    # elif type == 'Favors':
    #     symbols = MyFavorites.favors
    # elif type == 'Rally':
    #     symbols = MyFavorites.now_down
    # elif type == 'Pool':
    #     symbols = MyFavorites.bull_pool
    # elif type == 'Top_SP':
    #     #symbols = MyFavorites.bull_sp
    #     symbols = MyFavorites.top_sp
    # elif type == 'ETF':
    #     actives = get_symbols('active etfs')
    #     print(len(actives),actives)
    #     trends = get_symbols('trending etfs')
    #     symbols = set(actives+trends)
    # elif type == 'Stock':
    #     actives = get_symbols('active stocks')
    #     print(len(actives),actives)
    #     trends = get_symbols('trending stocks')
    #     symbols = set(actives+trends)
    return symbols




@st.cache_resource(ttl=600)
def prepare_group(symbols_set, interval, pe_limit):
    
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
    symbol_list = _stk_group.select(dceil=dceil,filter=filter)
    return symbol_list



def build_page():
   
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
    
    # NOTE: The first symbol in the list should be selected each time the page is reloaded
    # st.session_state.selected_symbol = symbol_list[0] if symbol_list else None
    #print('selected_symbol: ', st.session_state.selected_symbol, symbol_list)

    # Initialize or get the selected symbol from session state
    # # Ensure the selected symbol is still in the current list
    # the if condition is added by jules suggestion, remove if anything unsucessful
    if 'selected_symbol' not in st.session_state or st.session_state.selected_symbol not in symbol_list:
        st.session_state.selected_symbol = symbol_list[0] if symbol_list else None

        # added by jules suggestion, remove if anything unsucessful
        if 'show_ai_analysis' not in st.session_state:
            st.session_state.show_ai_analysis = {}

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
            pre_selected_rows= [i for i, sym in enumerate(df['symbol']) if sym == st.session_state.selected_symbol] # Pre-select the row
        )
        # Configure default columns with width constraints
        gb.configure_default_column(
            maxWidth=60,  # Limit maximum column width to 200px
            minWidth=40,   # Set minimum column width to 40px
            width=55,       # Default column width of 55px
            sortable=True, 
            resizable=True, 
            filterable=False,
            #domLayout=['autoHeight','autoSize'],
            suppressColumnMenu=True,
        )

        gridOptions = gb.build()
        # Disable filtering and menus at grid level
        gridOptions['enableFilter'] = False
        gridOptions['enableMenu'] = False
        gridOptions['suppressContextMenu'] = True
        
        # Add multiple suppression properties to all columns to ensure menu icons are hidden
        if 'columnDefs' in gridOptions:
            for colDef in gridOptions['columnDefs']:
                colDef['suppressMenu'] = True
                colDef['suppressColumnMenu'] = True
                colDef['menuTabs'] = []  # Remove all menu tabs
                colDef['filter'] = False  # Explicitly disable filter for each column

        # Removed autoSizeStrategy to use fixed widths for better control
        # gridOptions['autoSizeStrategy'] = {'type': 'fitCellContents'}

        # Display the grid
        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            height=grid_height,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.AS_INPUT,
            width='100%',
            allow_unsafe_jscode=True,  # Set it to True to allow jsfunction to be injected
            enable_enterprise_modules=False,
            key='stock_grid', # Add a key to avoid recreation issues
            show_search=False,
            #callback=lambda x: st.write(x) # don't forget we can use callback
        )

        # If a new row is selected in the grid, update the selected_symbol
        # and rerun the script to update the chart
        selected_rows = grid_response['selected_rows']
        if selected_rows is not None:
            if not selected_rows.empty and selected_rows.iloc[0]['symbol'] != st.session_state.selected_symbol:
                st.session_state.selected_symbol = selected_rows.iloc[0]['symbol']
                
                # added by suggestion of jules, remove if anything unsucessful
                if 'show_ai_analysis' in st.session_state:
                    #st.session_state.show_ai_analysis[st.session_state.selected_symbol] = False
                    st.session_state.show_ai_analysis = {}

                # added by suggestion of jules, remove if anything unsucessful
                st.rerun()

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
            length=selected_length,
            height=selected_height // len_all_intervals - 10,
            symbol_info=symbol_info
        )
        # --- AI analysis area ---
        info = stk_group.get_info(symbol)
        st_ai_analysis_area(symbol,info,ai_provider, session_state=st.session_state)

    else:
        st.write('No symbol selected')
    
    play_audio()
build_page()

