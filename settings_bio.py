#settings_bio.py

# import pandas as pd

# df = pd.read_csv('bio.csv', sep='\t', encoding='utf-16')

# # Now you can work with your dataframe
# df['ratio'] = df.ratio.str.rstrip('%')
# df['ratio'] = pd.to_numeric(df.ratio,errors='coerce')
# #print(df.ratio.head())

# list = df[(df.ratio > 4.99)]['Symbol'].to_list()
# # Access a specific column
# #print(set(list))

bios = {
    'IONS', 'ONC', 'IFRX', 'NRXP', 'YDES', 
    'PLX', 'APLM', 'CYTK', 'IVVD', 'FBIO', 
    'LXRX', 'BRNS', 'ATYR', 'ALLR', 'VTGN', 
    'CARM', 'LRMR', 'CALC', 'IRD', 'PGEN', 
    'BIVI', 'ARWR', 'LIMN', 'REPL', 'IBRX', 
    'OTLK', 'MENS', 'ANL', 'ACTU', 'RLMD', 
    'INSM', 'ZBIO', 'IMTX', 'PMCB', 'ABUS', 
    'ALEC', 'VYGR', 'CVM', 'LCTX', 'KALA', 
    'OSRH', 'VTVT', 'GOSS', 'ACRS', 'RAPT', 
    'MAZE', 'RNXT', 'NBY', 'ZNTL', 'TERN', 
    'STRO', 'IMRX', 'HOTH', 'TIL', 'MNKD', 'MLYS'
}