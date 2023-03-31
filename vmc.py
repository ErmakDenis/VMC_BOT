from ta import trend
import warnings
warnings.filterwarnings('ignore')


def VuManChu(df):
    shape = df.shape
    size = shape[0]
    n1 = 9
    n2 = 12
    df['ap']=0
    for i in range(0,size):
        df['ap'][i]=(df['high'][i]+df['low'][i]+df['close'][i])/3
    df['esa'] = trend.ema_indicator(close=df['ap'],window=n1)
    df['d_prep'] = 0
    for i in range(20, size):
        df['d_prep'][i] = abs(df['ap'][i]-df['esa'][i])
    df['d'] = trend.ema_indicator(df['d_prep'],window=n1)
    df['ci'] = 0
    df['ValorCandle']=0
    for i in range(20, size):
        df['ci'][i] = (df['ap'][i] - df['esa'][i])/(0.015 * df['d'][i])
        df['ValorCandle'][i] = (df['close'][i] - df['open'][i]) / (df['high'][i] - df['low'][i]) * 150 - 2.5
    df['wt1'] = trend.ema_indicator( df['ci'],window=n2)
    df['wt2'] = trend.sma_indicator(df['wt1'],3)
    df['MVC'] = trend.sma_indicator(df['ValorCandle'],window=60)
    df['ema50'] = trend.ema_indicator(df['close'],window=50)
    df['ema200'] = trend.ema_indicator(df['close'], window=200)
    # df['vmc_sig'] = ''
    df['vmc_sig2'] = ''
    df['signal'] = ''
    # for i in range(200,size):
    #     if df['wt1'][i] > df['wt2'][i]:
    #         df['vmc_sig'][i] = 'GREEN'
    #     else:
    #         df['vmc_sig'][i] = 'RED'

    for i in range(200,size):
        if df['wt2'][i] < df['wt1'][i] < 0 and df['wt2'][i - 1] > df['wt1'][i - 1]:
            df['vmc_sig2'][i] = 'GREEN'
        elif df['wt2'][i] > df['wt1'][i] > 0 and df['wt2'][i - 1] < df['wt1'][i - 1]:
            df['vmc_sig2'][i] = 'RED'
    for i in range(200, size):
        signal = ''
        if df['ema50'][i] > df['ema200'][i]:
            if df['vmc_sig2'][i] == 'GREEN' and df['wt2'][i] < -60:
                signal = 'BUY'
            if df['vmc_sig2'][i] == 'RED' and df['wt2'][i] > 100:
                signal = 'FORCE_SELL'
        elif df['ema50'][i] < df['ema200'][i]:
            if df['vmc_sig2'][i] == 'RED' and df['wt2'][i] > 60:
                signal = 'SELL'
            if df['vmc_sig2'][i] == 'GREEN' and df['wt2'][i] < -100:
                signal = 'FORCE_BUY'
        df['signal'][i] = signal
    return df

