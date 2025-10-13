import streamlit as st
import streamlit.components.v1 as components
from bokeh.embed import file_html
#from datetime import date # Unused

# Import background utility
from st_utils import set_page_background_color

#import yfinance as yf # Unused
#from bokeh.plotting import figure # Unused
from illustration import bokeh_draw as draw
#from fractions import Fraction # Unused
from settings import MySetts
from toolfuncs import get_any_df
#from spreads import CreditOptionSpread # Unused

st.set_page_config(layout="wide")

#st.title('St')

#START = '2015-01-01'
#TODAY = date.today().strftime('%Y-%m-%d')
intervals = ['1d', '1h', '15m', '1wk', '1mo', '1m', '2m', '5m', '30m', '60m', '5d', '3mo'] #, '90m'
pairs = [
    ['BOIL','KOLD'],
    ['GDXU','GDXD'],
    ['SOXL','SOXS'],
    ['SVIX','UVIX'],
    #['TQQQ','SQQQ'],
    ['LABU','LABD'],
]
tab1,tab2,tab3,tab4 = st.tabs([
    'BOIL',
    'GDX',
    'SOX',
    'VIX',
    #'LAB',
])
col2, col3, col4, col5, col6, col7, col8 = st.columns(7)

#with col1:
#    #selected_stock = st.text_input('Symbol', 'QQQ').upper()
#    selected_whole_view = st.selectbox('Whole view', [False, True])
with col2:
    selected_y2 = st.selectbox('Indicator',['both','kdj','bias','none']) # 'bbbp',
    selected_whole_view = selected_y2 == 'none'
with col3:
    #selected_interval = st.selectbox('Interval', intervals)
    selected_width = st.number_input('Width', value=560) #=2500 if selected_whole_view else 1200)
with col4:
    selected_height = st.number_input('Height', value=250) #if selected_stock in ['SPY','QQQ'] else 500
with col5:
    # Any length will be acceptable, since df[-length] will make it right
    selected_length = st.number_input('Bars to Display', value=900 if selected_whole_view else 90)






def tab_view(pair):
    df = None
    #@st.cache_data
    def load_data(symbol,fully=True,period=None,interval=None):
        df = get_any_df(symbol,fully=fully,period=period,interval=interval)
        #data = yf.download(symbol,START,TODAY)
        #data.reset_index(inplace=True)
        #return df[-round(2*max(300,df.hrows.iloc[-1]))-100:]
        return df

    #def plot_raw_data(symbol,df,whole_view):
    def plot_raw_data(symbol,whole_view,interval):
        #min(selected_length,len(df)-1)
        
        # 设置页面背景颜色
        set_page_background_color(df)
        
        p = draw(symbol,df=df[-selected_length:],just_data=True,whole_view=whole_view,\
            in_y2=selected_y2,width=selected_width,height=selected_height,interval=selected_interval)
        components.html(file_html(p, 'cdn', ), width=selected_width,height=selected_height)    
        #st.bokeh_chart(p,use_container_width=True)


    selected_interval = '1h' #'15m'
    chrt01,chrt02 = st.columns([1,1])
    with chrt01:
        symbol = pair[0]
        #data_load_state = st.text('loading ...')
        df = load_data(symbol=symbol,fully=True,interval=selected_interval,\
            period=MySetts.get_period(selected_interval))
        #data_load_state.text('Data loading ... down')

        plot_raw_data(symbol,selected_whole_view,selected_interval)


    with chrt02:
        symbol = pair[1]
        #data_load_state = st.text('loading ...')
        df = load_data(symbol=symbol,fully=True,interval=selected_interval,\
            period=MySetts.get_period(selected_interval))
        #data_load_state.text('Data loading ... down')

        plot_raw_data(symbol,selected_whole_view,selected_interval)

    selected_interval = '1d' #'1h' #
    chrt11,chrt12 = st.columns([1,1])
    with chrt11:
        symbol = pair[0]
        #data_load_state = st.text('loading ...')
        df = load_data(symbol=symbol,fully=True,interval=selected_interval,\
            period=MySetts.get_period(selected_interval))
        #data_load_state.text('Data loading ... down')

        plot_raw_data(symbol,selected_whole_view,selected_interval)


    with chrt12:
        symbol = pair[1]
        #data_load_state = st.text('loading ...')
        df = load_data(symbol=symbol,fully=True,interval=selected_interval,\
            period=MySetts.get_period(selected_interval))
        #data_load_state.text('Data loading ... down')

        plot_raw_data(symbol,selected_whole_view,selected_interval)


with tab1:
    tab_view(pairs[0])
with tab2:
    tab_view(pairs[1])
with tab3:
    tab_view(pairs[2])
with tab4:
    tab_view(pairs[3])
#with tab5:
#    tab_view(pairs[4])
#with tab6:
#    tab_view(pairs[5])
