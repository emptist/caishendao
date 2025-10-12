import pandas as pd

# import numpy as np # Unused

# import mplfinance as mpf # Unused
# import math # Unused
# from matplotlib import pyplot as plt # Unused
# import hvplot.pandas  # noqa # Unused
from bokeh.plotting import figure, show  # output_file
from bokeh.models import (
    Label,
    LinearAxis,
    Range1d,
    ColumnDataSource,
    CrosshairTool,
    HoverTool,
)  # , ResetTool, PanTool, WheelZoomTool # Unused ones removed

from settings import MySetts

# https://coderzcolumn.com/tutorials/data-science/candlestick-chart-in-python-mplfinance-plotly-bokeh
# https://github.com/matplotlib/mplfinance/blob/master/examples/addplot.ipynb

# Functions moved to extra/illustration_extra.py:
# illustrate, preset, preverse, present, draw_nb, mf_draw

# bokeh_draw remains as it's used by streamlit pages.


# this costs me a lot of time to solve the gaps between weekend days searching the web
# to save time always consult the latest guide first:
# https://docs.bokeh.org/en/latest/docs/user_guide/topics/timeseries.html


def bokeh_draw(
    symbol,
    df,
    just_data=False,
    whole_view=False,
    in_y2="kdj",
    width=None,  # for back compatibility, not used in current version
    height=500,
    interval=None,
    symbol_info=None,
):
    """
    Usage:
        - for apps such as streamlit call directly
        - for notebook, call directly or through draw_nb and other tool functions
    Params:
        - df: is cut before calling
        - just_data: without support for backtesting lib
        - whole_view: without second chart(kdj, etc.) in log y_axis_type
    """
    if just_data:
        # eb,es ='sput','scall'
        eb, es = "buy", "sell"
    else:
        eb, es = "eb", "es"

    if MySetts.hourly:
        w = 0.5  # 30*60*1000 # half an hour in ms
    else:
        w = 0.5  # 12*60*60*1000 # half day in ms

    df["date"] = pd.to_datetime(df.index)
    # df.reset_index(inplace=True)
    df["idx"] = df.reset_index().index  # df.index #df.reset_index().index
    # date_str = df['date'].dt.strftime('%Y-%m-%d %H:%S')

    source = ColumnDataSource(data=df)

    # TOOLS = "pan,wheel_zoom,box_zoom,reset,save"

    TOOLS = [
        CrosshairTool(),
        "pan",
        "wheel_zoom",
        "box_zoom",
        "reset",
        "save",
    ]  # ,'hover'

    # lo = min(df.bbm.min()*0.9,df.low.min()) #min(df.bbl.min(),df.low.min())
    # hi = max(df.bbu.max(),df.high.max())
    lo = df.low.min()
    hi = df.high.max()
    hi_lo = hi - lo

    extra_info = "" if symbol_info is None else symbol_info
    cma_rbl = round(df.cma_rbl.iloc[-1], 3) if ("cma_rbl" in df.columns) else "-"
    ratio = (
        round((100 * df.close.iloc[-1] / df.close.iloc[-2] - 100), 2)
        if (len(df) > 1)
        else 0
    )
    if ('bias' in df.columns):
        bias = round(df.bias.iloc[-1], 2) 
    else: 
        bias = 0
        print(f'DEBUG BIAS: missing in {symbol} {interval}')

    cnst = round(df.cnst7.iloc[-1], 2) if ('cnst7' in df.columns) else -1
    cnsvel = round(df.cnsvel7.iloc[-1], 2) if ('cnsvel7' in df.columns) else -1
    velo = round(df.velo7.iloc[-1], 2) if ('velo7' in df.columns) else -1
    cnstvelo = cnsvel

    j = round(df.j.iloc[-1], 2)
    d = round(df.d.iloc[-1], 2)
    if whole_view:
        y1_range = Range1d(start=lo * 0.95, end=hi * 1.05)
        p = figure(
            tools=TOOLS,
            sizing_mode="stretch_width",
            height=height,
            y_range=y1_range,
            output_backend="webgl",
            y_axis_type="log",  # tooltips=TOOLTIPS,
            title=f"{symbol}[{interval}] {round(df.close.iloc[-1],5)} ({ratio}% c:{cnst} v:{velo} cv:{cnstvelo} {j}/{d}) <{cma_rbl}> {extra_info}",
        )

    else:
        y1_range = Range1d(start=lo - (hi_lo) * 0.6, end=hi * 1.05)
        y2_range = Range1d(start=-60, end=500)
        p = figure(
            tools=TOOLS,
            sizing_mode="stretch_width",
            height=height,
            y_range=y1_range,
            output_backend="webgl",
            # y_axis_type='log', #tooltips=TOOLTIPS,
            title=f"{symbol}[{interval}] {round(df.close.iloc[-1],5)} ({ratio}% c:{cnst} v:{velo} cv:{cnstvelo} {j}/{d}) <{cma_rbl}> {extra_info}",
        )
        # extra y axis
        p.extra_y_ranges = {"y2": y2_range}
        p.add_layout(LinearAxis(y_range_name="y2"), "right")

    # p.xaxis.major_label_orientation = pi/4
    # p.x_range.range_padding = 0.05
    p.grid.grid_line_alpha = 0.5
    # one tick per week (5 weekdays)
    # p.xaxis.ticker = list(range(df.idx[0], df.idx[-1], 5))

    
    # Add conditional background based on 'somecondition'
    # for _, row in df.iterrows():
    #    if row.smas_up:
    #        idx = row.idx
    #        box = BoxAnnotation(left=idx-w, right=idx+w, fill_alpha=0.1, fill_color='blue')
    #        p.add_layout(box)

    # if df.smas_up.iloc[-1]:
    last_ma_bullish = df.smas_up.iloc[-1] & df.cmas_up.iloc[-1]
    if last_ma_bullish:
        # if df.sput.iloc[-1]:
        p.background_fill_color = "#f2693d"  #'#f7dcd2' #'#f39726' #'#e2dafc' #'#d3c7f8'
        p.background_fill_alpha = 0.2

    inc = df.close > df.open
    dec = df.open >= df.close
    # try:
    if False: #interval in ["1h", "1d", "1wk", "1mo"]:
        
        inc1 = inc & df.avrgs_bull
        inc2 = inc & ~df.avrgs_bull
        dec1 = dec & df.avrgs_bull
        dec2 = dec & ~df.avrgs_bull
    else:
        inc1 = inc & df.smas_up
        inc2 = inc & ~df.smas_up
        dec1 = dec & df.smas_up
        dec2 = dec & ~df.smas_up

    # candle sticks
    p.segment(
        "idx", "high", "idx", "low", source=source, hover_alpha=0.9, color="black"
    )
    p.vbar(
        df.idx[inc1],
        w,
        df.open[inc1],
        df.close[inc1],
        fill_color="red",
        line_color="red",
    )
    p.vbar(
        df.idx[dec1],
        w,
        df.open[dec1],
        df.close[dec1],
        fill_color="blue",
        line_color="blue",
    )  # "magenta")
    p.vbar(
        df.idx[inc2],
        w,
        df.open[inc2],
        df.close[inc2],
        fill_color="lightgrey",
        line_color="grey",
    )  # fill_color="#D5E1DD"
    p.vbar(
        df.idx[dec2],
        w,
        df.open[dec2],
        df.close[dec2],
        fill_color="black",
        line_color="black",
    )  # fill_color="#F2583E"

    # sma
    # p.line('idx','sma30',line_width=0.5,source=source,hover_alpha=0.9,line_color='orange')
    # p.line('idx','sma14',line_width=0.5,source=source,hover_alpha=0.9,line_color='green')

    # key indicators: lcmah7, lcmahbbm
    indic7 = "lcmah7"  #'sma7'
    p.line(
        "idx",
        'sma7',
        source=source,
        hover_alpha=0.9,
        line_color="darkorange",
        line_width=1.2,
    )  # line_color='magenta',line_width=0.5)
    p.line(
        "idx",
        "lcmah7",
        source=source,
        hover_alpha=0.9,
        line_color="darkviolet",
        line_width=1.9,
    )

    # p.line('idx','sma60',line_width=0.5,source=source,hover_alpha=0.9,line_color='darkred')

    p.line(
        "idx", "bbm", source=source, hover_alpha=0.9, line_color="red", line_width=0.5
    )  # line_width=1.1)
    for iname in [
        #"sma140",
        # 'sma300','sma500',
        "bbu",
        "bb6u",
        "bb4u",
        "bb4l",
        "bb6l",
        "bbl",
    ]:  # ,'bbum','bblm']:
        # p.line(df.idx,df[iname],line_width=0.5)
        p.line("idx", iname, source=source, hover_alpha=0.9, line_width=0.5)

    # cmah/l
    # p.line('idx','cmah',source=source,hover_alpha=0.9,line_color='darkblue',line_width=0.7)
    # p.line('idx','cmam',source=source,hover_alpha=0.9,line_color='magenta',line_width=0.7) #cyan
    # p.line('idx','cmal',source=source,hover_alpha=0.9,line_color='brown',line_width=0.7)
    # p.line('idx','lcmah',source=source,hover_alpha=0.9,line_color='navy',line_width=0.7)

    if interval in ["1d", "1h", "1wk", "1mo"]:
    #     p.line(
    #         "idx",
    #         "lcmahbbm",
    #         source=source,
    #         hover_alpha=0.9,
    #         line_color="navy",
    #         line_width=0.5,
    #     )
        p.line(
            "idx",
            "cmal7",
            source=source,
            hover_alpha=0.9,
            line_color="red",
            line_width=1.2,
        )

    klsig = 0.99
    khsig = 1.02
    wopt = 1 / hi_lo  # 1.1
    wstk = 3 / hi_lo  # 3

    mark_k = True
    if mark_k:
        # sput/scall sigs
        if just_data:
            p.scatter(
                df.idx[df["sput"]],
                df.low[df["sput"]] * klsig,
                line_color="red",
                line_width=wopt,
            )
            p.scatter(
                df.idx[df["scall"]],
                df.high[df["scall"]] * khsig,
                line_color="green",
                line_width=wopt,
            )

        # buy/sell sigs
        p.triangle(
            df.idx[df[eb]], df.low[df[eb]] * klsig, fill_color="red", line_color="red", line_width=wstk
        )
        p.inverted_triangle(
            df.idx[df[es]], df.high[df[es]] * khsig, fill_color="blue", line_color="blue", line_width=wopt
        )

    if not whole_view:
        if in_y2 in ["both","consis"]:
            for iname in [
                "cnst7", 
                "cnsvel7",
            ]:
                if iname in df.columns:
                    p.line(
                        "idx",
                        iname,
                        source=source,
                        hover_alpha=0.9,
                        line_width=0.9,
                        y_range_name="y2",
                    )
        if in_y2 in ["bbbp"]:
            for iname in ["bbb", "bbp"]:
                p.line(
                    "idx",
                    iname,
                    source=source,
                    hover_alpha=0.9,
                    line_color="darkblue",
                    line_width=0.4,
                    y_range_name="y2",
                )
        if in_y2 in [
            #"both", 
            "bias"
        ]:
            # p.extra_y_ranges['y2'] = Range1d(start=-10, end=10)
            # p.add_layout(LinearAxis(y_range_name='y2',axis_label='Bias %'), 'right')
            p.line(
                "idx",
                "bias",
                source=source,
                hover_alpha=0.9,
                line_color="black",
                line_width=0.9,
                y_range_name="y2",
            )
        if in_y2 in ["both", "kdj"]:
            for iname in [
                "m",
                "k",
                #'pdh_l','pdl_u',
            ]:
                p.line(
                    "idx",
                    iname,
                    source=source,
                    hover_alpha=0.9,
                    line_width=0.6,
                    y_range_name="y2",
                )

            p.line(
                "idx",
                "d",
                source=source,
                hover_alpha=0.9,
                line_color="green",
                line_width=0.9,
                y_range_name="y2",
            )
            p.line(
                "idx",
                "j",
                source=source,
                hover_alpha=0.9,
                line_color="red",
                line_width=0.7,
                y_range_name="y2",
            )

            # buy/sell sigs
            # on kdj
            if just_data:  # False and
                p.scatter(
                    df.idx[df["sput"]],
                    df.m[df["sput"]] * klsig * klsig,
                    line_color="red",
                    line_width=wopt,
                    y_range_name="y2",
                )
                p.scatter(
                    df.idx[df["scall"]],
                    df.d[df["scall"]] * khsig * khsig,
                    line_color="green",
                    line_width=wopt,
                    y_range_name="y2",
                )

            p.triangle(
                df.idx[df[eb]],
                df.m[df[eb]] * klsig * klsig,
                fill_color="red",
                line_color="red",
                line_width=wstk,
                y_range_name="y2",
            )
            p.inverted_triangle(
                df.idx[df[es]],
                df.d[df[es]] * khsig * khsig,
                fill_color="blue",
                line_color="blue",
                line_width=wstk,
                y_range_name="y2",
            )

    # map dataframe indices to date strings and use as label overrides
    p.xaxis.major_label_overrides = {
        i: date.strftime("%b %d / %y") for i, date in zip(df.idx, df["date"])
    }

    hover = HoverTool(
        tooltips=[
            ("date", "@date{%Y-%m-%d %H:%M:%S}"),
            ("close", "@close"),
            ("cnst", "@cnst7"),
            ("cnsvel", "@cnsvel7"),
            ("velo", "@velo7"),
            ("lcmah", "@lcmah"),
            ("cmah", "@cmah"),
            ("cmam", "@cmam"),
            ("cmal", "@cmal"),
            ("bbu", "@bbu"),
            # ('bb6u','@bb6u'),
            # ('bb4u','@bb4u'),
            ("bbm", "@bbm"),
            # ('bb4l','@bb4l'),
            # ('bb6l','@bb6l'),
            ("bbl", "@bbl"),
            # ('hrows','@hrows'),
            # ('lhrows','@lhrows'),
            # ('lrows','@lrows'),
            # ('pdh_l','@pdh_l'),
            ("j", "@j"),
            ("k", "@k"),
            ("d", "@d"),
            ("m", "@m"),
            # ('pdl_u','@pdl_u'),
            # ('bbb','@bbb'),
            # ('bbp','@bbp'),
            ("buy", "@buy"),
            ("sell", "@sell"),
            ("sput", "@sput"),
            ("scall", "@scall"),
        ],
        formatters={
            "@date": "datetime",
            #'@buy':'boolean',
            #'@sput': 'boolean',
        },
        mode="mouse",
    )
    p.add_tools(hover)

    if df.sell.iloc[-1] | df.scall.iloc[-1]:
        l_text = 'SELL'
        l_text_color = 'red'
        l_text_y_offset = -30
    elif df.buy.iloc[-1] | df.sput.iloc[-1]:
        l_text = 'BUY'
        l_text_color = 'green'
        l_text_y_offset = 30
    elif last_ma_bullish:
        l_text = 'BULL'
        l_text_color = 'darkorange'
        l_text_y_offset = -30
    elif ~df.smas_up.iloc[-1] & ~df.cmas_up.iloc[-1]:
        l_text = 'BEAR'
        l_text_color = 'blue'
        l_text_y_offset = 30
    else:
        l_text = 'DUBIOUS'
        l_text_color = 'gray'
        l_text_y_offset = 0
    
    
    label = Label(
        x=df.idx.iloc[1], 
        y=df.close.iloc[-1],  
        x_offset=10, 
        y_offset=l_text_y_offset,
        text=l_text,
        # most important font family
        text_font= 'courier', #'sans-serif',
        text_font_size='28pt',
        text_font_style='bold italic',
        text_color=l_text_color,
        #border_line_color='#c3c99a',
        #background_fill_color='#c3c99a'
    )

    p.add_layout(label)

    return p
    show(p)


def mf_draw(df, just_data=False):
    pass  # see mf.py
