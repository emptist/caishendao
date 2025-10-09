# tickers = alldata.tickers #.to_list()
# info = tickers[symbol].info
# #print(info)
# legalType = info['legalType'] if 'legalType' in info else None
# # should be case insensitive
# if legalType != 'Exchange Traded Fund':
#     print(f'{symbol} is not Exchange Traded Fund {legalType}')
#     continue

# get the symbols from the csv file
import pandas as pd
from toolfuncs import elevate_yf_df, dfs_for_interval

def filter_func(symbols,interval='1d',v_limit=0.01,cr_limit=20,c_limit=40):  
    #dfs, alldata = dfs_for_interval(interval,symbols,withInfo=True)
    dfs, _ = dfs_for_interval(interval,symbols,withInfo=False)
    result = []
    for symbol in symbols: #list(symbols):
        # category is not bond 
        df = elevate_yf_df(dfs[symbol],interval)
        if (df is None) or len(df) < 1:
            continue

        v = df.velo7.iloc[-1]
        c = df.cnst7.iloc[-1]
        cr = df.cnst7r.iloc[-1]

        #if symbol in ['GLD','SLV','GDX','GDXU']:
        #    print(f'{symbol} is gold or silver, cr: {round(cr,2)} c: {round(c,2)} velo: {round(v,2)}')
        if df.close.iloc[-1] < df.close.iloc[-min(8,len(df))]:
            continue
        if df.close.iloc[-1] < df.close.iloc[-min(140,len(df))]:
            continue
        if cr_limit is not None and cr < cr_limit:
            continue
        if c_limit is not None and c < c_limit:
            continue
        if v_limit is not None and v < v_limit:
            continue
        result.append(symbol)
        #print(f'{symbol} \t c: {c:.2f}% \t cr: {cr:.2f}% \t velo: {v:.2f}% \t cnst*velo: {(c*v):.2f}')
    return set(result)


def get_symbols(csv_file='etf.csv',sep='\t',encoding='utf-16'):
    #Get the symbols from the csv file
    df = pd.read_csv(csv_file, sep=sep, encoding=encoding)
    # print if there are EtfName in ['GLD','SLV','GDX','GDXU']
    # print(df[df['EtfName'].str.contains('GLD|SLV|GDX|GDXU', na=False, case=False)])
    # we have to filter out the rows with no 'B', 'M', or 'K'
    df = df[df['Amount'].str.contains('B|M|K', na=False)]
    # in the EtfName column
    strng = '兩倍|2倍|1倍|一倍|1.5倍|1.5x|2x|1.5X|2X|income|hedge|trust|收益|債|bond|債券'
    #strng = 'income|hedge|bond|兩倍|2倍||1倍|1.5倍|收益|1.5x|2x|債'
    df = df[df['EtfName'].str.contains(strng, na=False, case=False) == False]
    #print(f'filter out the rows with {strng}, len(df))

    df['amount'] = df["Amount"].str.replace('B', '*100000')
    df['amount'] = df['amount'].str.replace('M', '*100')
    df['amount'] = df['amount'].str.replace('K', '*0.1')
    df['amount'] = df['amount'].apply(lambda x: eval(x))
    #print(df['amount'].head())
    list = df[(df.amount > 5000)]['EtfSymbol'].to_list()
    #print(len(list), list)
    return set(list)

def main():
    known = get_symbols() 
    #known = {'BITB', 'ARKB', 'SHLD', 'FBTC', 'GRNY', 'BAI', 'TQQQ', 'SPXL', 'IBIT'}
    result = filter_func(known,c_limit=40,cr_limit=1,v_limit=0.03)
    print(f'indices={result}')


def resarch():
    known = get_symbols() 
    known = {'BITB', 'ARKB', 'SHLD', 'FBTC', 'GRNY', 'BAI', 'TQQQ', 'SPXL', 'IBIT'}
    print(f'filtered by long name: {len(known)}')

    result = known
    result = filter_func(known,c_limit=46,cr_limit=10,v_limit=0.09)
    print(f'filtered by consistency and velocity: {len(result)}')
    print(result,len(result))

    #current = result
    #current = filter_func(result,cr_limit=35)
    #print(f'filtered by recent consistency and velocity: {len(current)}')
    #print(current,len(current))

    # ['XLI', 'IWF', 'VUG', 'SPYG', 'IVW', 'ITA', 'VFH', 'BAI', 'SHLD', 'GRNY', 'IUSG']


if __name__ == '__main__':
    main()