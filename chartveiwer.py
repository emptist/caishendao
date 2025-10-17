import streamlit as st
import streamlit.components.v1 as components
from bokeh.embed import file_html
from illustration import bokeh_draw as draw
from settings import MySetts
from toolfuncs import get_any_df
from ai_analysis import st_ai_analysis_area
from st_utils import set_page_background_color, play_audio



# Initialize a session state variable that tracks the sidebar state (either 'expanded' or 'collapsed').
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

# Streamlit set_page_config method has a 'initial_sidebar_state' argument that controls sidebar state.
#st.set_page_config(initial_sidebar_state=st.session_state.sidebar_state)
st.set_page_config(page_title='Trader',layout="wide",initial_sidebar_state=st.session_state.sidebar_state)

#st.set_page_config(page_title='view chart',layout="wide")
st.sidebar.header('View Chart')



#st.title('St')

#START = '2015-01-01'
#TODAY = date.today().strftime('%Y-%m-%d')
intervals = ['1d', '1h', '30m', '15m', '5m', '1wk', '1mo', '3mo',] # '1m', '2m', '60m', '5d', ] #, '90m'
col1, col2, col3, col4, col5, col6= st.columns(6)

# with col1:
#     selected_width = st.number_input('Width', value=1150) #=2500 if selected_whole_view else 1200)
with col2:
    selected_height = st.number_input('Height', value=500) #400 if selected_stock in ['SPY','QQQ'] else 500)
with col5:
    selected_y2 = st.selectbox('Indicator',['none','consis','kdj','both','bias',]) # 'bbbp',
    selected_whole_view = selected_y2 == 'none' 
with col3:
    interval = st.selectbox('Interval', intervals)
with col4:
    # Any length will be acceptable, since df[-length] will make it right
    #selected_length = st.number_input('Chart Bars', value=300)
    #selected_stock = st.selectbox('Symbol', get_symbols())
    selected_length = st.selectbox('Chart Bars',[150,300,600,1200,2400,4800,9600,])#st.number_input('Chart Bars', value=1000) #9000 if selected_whole_view else 900)
with col1:
    # Add AI Provider selection
    ai_provider = st.selectbox('AI Provider',  ['alibabacloud','gemini', ] if MySetts.use_proxy else ['gemini','alibabacloud'])
with col6:
    symbol = st.session_state.get('selected_symbol','SHLD')
    symbol = 'SHLD' if symbol.isspace() or symbol == '' else symbol
    selected_stock = st.text_input('Symbol',symbol).upper()

@st.cache_data  
def load_data(symbol,interval,period,fully=True):
    left_df, info = get_any_df(
        symbol,
        fully=fully,
        period=period,
        interval=interval,
        withInfo=True
    )
    right_df = left_df
    return info, left_df, right_df

#data_load_state = st.text('loading ...')
period=MySetts.get_period(interval) #interval
info, left_df, right_df = load_data(selected_stock,interval=interval,period=period,fully=True)
#data_load_state.text('Data loading ... down')

def plot_raw_data(df,interval,whole_view):
    #print(df.shape)
    if len(df) > 1 and hasattr(df, 'j'):
        try:
            longName = info['longName']
        except Exception as e:
            longName = selected_stock
        #min(selected_length,len(df)-1)
        #height= selected_height//2
        height= selected_height
        p = draw(
            symbol=selected_stock,
            df=df[-selected_length:],
            just_data=True,
            whole_view=whole_view,
            in_y2=selected_y2,
            height=height,
            interval=interval,
            symbol_info= longName
        )
        components.html(file_html(p, 'cdn', ), width=None,height=height)    
        #st.bokeh_chart(p,use_container_width=True)
        set_page_background_color(df)

if True:
#chart1,chart2=st.columns(2)
#with chart1:
    plot_raw_data(left_df,interval,selected_whole_view)
#with chart2:
    #plot_raw_data(right_df,right_interval,selected_whole_view)

df = left_df
        
close_start = round(df.close.iloc[0],2)
close_end = round(df.close.iloc[-1],2)
times_incr = close_end/close_start
bars = len(df)
velocity = 100 * (times_incr**(1/bars)) - 100
velo = df.velo7.iloc[-1]
cnstvelo = df.cnsvel7.iloc[-1]

st.write(f'**{selected_stock} data from {len(df)} bars, {close_start} -> {close_end}, price velocity: {velocity:.2f}%, velo: {velo:.2f}%, cnst*velo: {cnstvelo:.2f}**')

st_ai_analysis_area(selected_stock,info,ai_provider, session_state=st.session_state)

#st.subheader(f'{selected_stock} option spread')
# if selected_stock in ['SPY','QQQ']:
#     coll1,coll2,coll3 = st.columns([1,1,1])
#     with coll1:
#         df_value = max(df.lhsf7.iloc[-1], df.hsf7.iloc[-1]) if df.sell.iloc[-1] else min(df.lsf7.iloc[-1],df.bbl.iloc[-1])
#         sell_opt_strike = st.number_input('Sell opt strike', value=round(df_value))
#     with coll2:
#         df_value = max(df.bbu7.iloc[-1],df.hsf7.iloc[-1],df.lhsf7.iloc[-1])*1.1 if df.sell.iloc[-1] else min(df.lsf7.iloc[-1],df.bbl.iloc[-1])*0.9
#         buy_opt_strike = st.number_input('Buy opt strike', value=round(df_value))
#     with coll3:
#         min_gain_risk_ratio = st.selectbox('Min gain ratio', ['3/8','1/3','5/12','11/24'])

    #selected_height = int(selected_height*0.8)
    #plot_raw_data()
    #st.text(f'Buy spread at price: -{CreditOptionSpread.min_gain_to_strikes(sell_opt_strike,buy_opt_strike,min_gain_risk_ratio=float(Fraction(min_gain_risk_ratio)))}')

#st.text(f'{selected_stock} data from {len(df)} bars, {round(df.close.iloc[0],2)} -> {round(df.close.iloc[-1],2)}')
st.write(df.tail())
#st.write(df.columns.sort_values())


play_audio()

if st.button("Show/Hide Raw Info"):
    st.session_state.show_info = not st.session_state.get('show_info', False)
if st.session_state.get('show_info', False):
    st.write(info)

