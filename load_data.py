import requests
import pandas as pd
import numpy as np

api_key = 'Uo9m2CCZex2rB5nxgVrGDDymyk7oeU20I3Rj4s6X5CcUPItFYVT0iu0Cje8oKHn5'
secret_key = 'VWnGJgq31fly20aJI6qTqYTWuQXlgKNTSM9XpD3pI8yOEGCv7qeQKo1M0VI4v5FI'


def kLines(symbol, tf,st):#, st
    url = 'https://api3.binance.com/api/v3/klines'
    param = {'symbol': symbol, 'interval': tf,'startTime':st ,'limit': 1000}  # ,'startTime':st,'endTime':ed
    r = requests.get(url, params=param)
    if r.status_code == 200:
        df = pd.DataFrame(r.json())
        m = pd.DataFrame()
        m['date'] = df.iloc[:, 0]
        m['date'] = pd.to_datetime(m['date'], unit='ms')
        m['open'] = df.iloc[:, 1]
        m['high'] = df.iloc[:, 2]
        m['low'] = df.iloc[:, 3]
        m['close'] = df.iloc[:, 4]


        return m
    else:
        return print('Проверте данные')


def lastMin(symbol, tf):
    url = 'https://api3.binance.com/api/v3/klines'
    param = {'symbol': symbol, 'interval': tf, 'limit': 1}
    r = requests.get(url, params=param)
    if r.status_code == 200:
        df = pd.DataFrame(r.json())
        m = pd.DataFrame()
        m['date'] = df.iloc[:, 0]
        m['date2'] = pd.to_datetime(m['date'], unit='ms')
        # print(m['date'])
        # print(m['date2'])
        return m.loc[0, 'date']


    else:
        return print('Проверте данные')

def load_df(Crypto = 'BTCUSDT', tf = '1m',count=10,tf_int=1):

    st = lastMin(Crypto, tf)
    st = st - tf_int * 60000 * 1000 * count

    # Качаем 1000 последних дней
    check = 0
    for i in range(count):
        k = kLines(Crypto, tf, st)
        st = st + tf_int * 60000 * 1000
        if check == 0:
            out = k
            check = 1
        else:
            out = out.append(k)
    return out