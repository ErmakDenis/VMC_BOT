from load_data import load_df
from vmc import VuManChu
import pandas as pd
from binance.spot import Spot
from tele import telegram_bot
import time as t
from datetime import datetime
import warnings
from math import floor
from myAPI import api_key,secret_key,token

warnings.filterwarnings('ignore')


symbol = "BTCUSDT"


def send_report(text):
    try:
        telegram_bot(token, text=text)
    except:
        print('error 21')


def data_preprocessing(count=1):
    data1 = load_df(count=count, Crypto=symbol, tf='5m', tf_int=5)
    data1.to_csv('tmp.csv')
    data1 = pd.read_csv('tmp.csv')
    out = VuManChu(data1)
    # out.to_csv('out.csv')
    return out


try:
    client = Spot(key=api_key, secret=secret_key)
except:
    t.sleep(0.5)
    telegram_bot(token, f'ошибка подключения ')
    client = Spot(key=api_key, secret=secret_key)


def wait_for_five():
    check = 0
    while check == 0:
        w_time = datetime.now().strftime('%M')
        w_time = int(w_time)
        # Программа ждет пока время не будет кратно 5 минутам
        w_time = w_time % 5
        if w_time == 0:
            check = 1


def round_down(x, n=0):
    if n == 0:
        x = x + 0.0000000001  # без этого добавления округление в нижнюю сторону сьедало 1 от последнего числа
        a = floor(x)
    else:
        x = x + 0.0000000001
        a = x
        for i in range(n):
            a = a * 10
        a = floor(a)
        for i in range(n):
            a = a / 10
    a = round(a, n)
    return a


def get_deposit(symbol):
    asset = client.isolated_margin_account(symbols=symbol)
    free_asset = asset['assets'][0]['quoteAsset']['free']
    return free_asset


def check_if_in_trade():
    orders = client.margin_open_orders(symbol=symbol, isIsolated=True)
    count = 0
    st = 'EMPTY'
    for i in orders:
        count = count + 1
        st = i['side']
    if st == 'BUY':
        st = 'SELL'
    elif st == 'SELL':
        st = 'BUY'
    if count == 3:
        return 'FULL_ORDER', st
    if count == 1:
        return 'TRAILING_ORDER', st
    if count == 0:
        return 'EMPTY', st
    return st, st


def repay():
    asset = client.isolated_margin_account(symbols='BTCUSDT')
    borrowed_USD = float(asset['assets'][0]['quoteAsset']['borrowed'])
    borrowed_BTC = float(asset['assets'][0]['baseAsset']['borrowed'])
    BTC = float(asset['assets'][0]['baseAsset']['free'])
    USD = float(asset['assets'][0]['quoteAsset']['free'])
    if borrowed_USD > 0:  # И если есть занятые средатсва
        if borrowed_USD < USD:
            client.margin_repay(asset='USDT', amount=borrowed_USD, isIsolated=True, symbol=symbol)
        else:
            client.margin_repay(asset='USDT', amount=USD, isIsolated=True, symbol=symbol)
    if borrowed_BTC > 0:  # Если занимал BTC
        if BTC > 0:  # И есть свободные BTC
            if BTC <= borrowed_BTC:
                client.margin_repay(asset='BTC', amount=BTC, isIsolated=True, symbol=symbol)
            else:
                client.margin_repay(asset='BTC', amount=borrowed_BTC, isIsolated=True, symbol=symbol)


def close_and_repay(price):
    client.margin_open_orders_cancellation(symbol=symbol, isIsolated=True)
    asset = client.isolated_margin_account(symbols=symbol)
    borrowed_BUS = float(asset['assets'][0]['quoteAsset']['borrowed'])
    borrowed_BTC = float(asset['assets'][0]['baseAsset']['borrowed'])
    BTC = float(asset['assets'][0]['baseAsset']['free'])
    if borrowed_BTC <= BTC and borrowed_BTC > 0:
        try:
            client.margin_repay(asset='BTC', amount=borrowed_BTC, isIsolated=True, symbol=symbol)
        except:
            print('error 1')
            send_report('error 1')
            pass

        if (BTC - borrowed_BTC) * price > 10.5:
            dif = BTC - borrowed_BTC
            dif = round_down(dif, 5)
            try:
                client.new_margin_order(symbol=symbol, side='SELL', type='MARKET', quantity=dif, isIsolated=True)
            except:
                print('error 2')
                send_report('error 2')

    elif borrowed_BTC > BTC:
        dif = borrowed_BTC - BTC + 0.00005
        dif = round_down(dif, 5)
        if dif * price > 10:
            try:
                client.new_margin_order(symbol=symbol, side='BUY', type='MARKET', quantity=dif, isIsolated=True)
            except:
                print('error 3')
                send_report('error 3')

        else:
            try:
                client.new_margin_order(symbol=symbol, side='BUY', type='MARKET', quoteOrderQty=11, isIsolated=True)
            except:
                print('error 4')
                send_report('error 4')
        borrowed_BTC = round_down(borrowed_BTC,7)
        try:
            client.margin_repay(asset='BTC', amount=borrowed_BTC, isIsolated=True, symbol=symbol)
        except:
            print('error 5')
            send_report('error 5')

    # Биток вернули

    # TODO Прописать блок возврата USDT
    try:
        asset = client.isolated_margin_account(symbols=symbol)
    except:
        print('error 6')
        send_report('error 6')

    BTC = float(asset['assets'][0]['baseAsset']['free'])
    BTC = round_down(BTC, 5)
    try:
        client.new_margin_order(symbol=symbol, side='SELL', type='MARKET', quantity=BTC, isIsolated=True)
    except:
        print('error 7')
        send_report('error 7')

    try:
        client.margin_repay(asset='USDT', amount=borrowed_BUS, isIsolated=True, symbol=symbol)
    except:
        print('error 8')
        send_report('error 8')

def get_prev_price():
    orders = client.margin_all_orders(symbol=symbol, isIsolated=True)
    lens = len(orders)
    st = 0
    if lens > 5:
        st = lens - 5
    pri = 0
    for i in range(st, lens):

        if orders[i]['type'] == 'MARKET':
            btcc = float(orders[i]['executedQty'])
            usdt = float(orders[i]['cummulativeQuoteQty'])
            pri = round_down(usdt / btcc)
    return pri


def get_order_price():
    orders = client.margin_open_orders(symbol=symbol, isIsolated=True)
    for i in orders:
        price1 = i['price']
        btc = i['origQty']
        side1 = i['side']
    return price1, btc, side1



# ---------------------------------------------------------
# Рабочая часть
# ---------------------------------------------------------
deposit = float(get_deposit(symbol))
start_deposit = deposit
print(f'deposit: {deposit}')
telegram_bot(token, f'Работаем!\nDeposit: {deposit}')
prev_price = 0

while True:
    check = 0
    wait_for_five()
    t.sleep(0.5)
    print('Анализирую...')
    status = ''
    try:
        stat = check_if_in_trade()
    except:
        try:
            t.sleep(0.1)
            stat = check_if_in_trade()
        except:
            try:
                t.sleep(0.5)
                stat = check_if_in_trade()
            except:
                print(f'error 22 status: {stat}')
                send_report('error 22')

    try:
        df = data_preprocessing()
    except:
        try:
            df = data_preprocessing()
        except:
            try:
                df = data_preprocessing()
            except:
                print('error 9')
                send_report('error 9')
                check = 1
    shape = df.shape
    size = shape[0]
    signal = df['signal'][size - 1]
    status = stat[0]
    prev_side = stat[1]

    # Проверка на покупку
    if signal == 'BUY' or signal == 'FORCE_BUY':

        if prev_side == 'SELL' or status == 'TRAILING_ORDER':
            price = df['close'][size - 1]
            try:
                close_and_repay(price)
            except:
                print('error close and repay 1')
                send_report('error close and repay 1')

        if prev_side == 'SELL' or status == 'TRAILING_ORDER' or status == 'EMPTY':
            try:
                deposit = float(get_deposit(symbol))
            except:
                print('error 10')
                send_report('error 10')

            # то можно занимать и открывать ордера
            # ---------------------------------------------------------------------
            # БЛОК ПОКУПКИ
            # ---------------------------------------------------------------------
            bet = deposit * 8.5
            price = df['close'][size - 1]
            stop_loss = price * 0.997
            take_profit = price * 1.006
            take_profit = round_down(take_profit)
            stop_loss = round_down(stop_loss)
            stop_loss2 = round_down(stop_loss - 10)
            USD = round_down(bet)
            prev_price = round_down(price)
            check = 0
            try:
                if check == 0:
                    # занимаю USDT
                    client.margin_borrow(asset='USDT', amount=USD, isIsolated=True, symbol=symbol)
                    # Определяю сколько купить BTC
                    BTC = round_down(USD / price, 5)
            except:
                print(f'error 11 - {USD}')
                send_report('error 11')
                check = 1
            try:
                # Покупаю BTC по рынку
                if check == 0:
                    client.new_margin_order(symbol=symbol, side='BUY', type='MARKET', quantity=BTC, isIsolated=True)
            except:
                print('error 12')
                send_report('error 12')
                check = 1

            try:
                if check == 0:
                    # Узнаем сколько BTC купили
                    last_trade = client.margin_all_orders(symbol=symbol, isIsolated=True)
                    BTC_bought = float(last_trade[-1]['executedQty'])
            except:
                print('error 13')
                send_report('error 13')
                check = 1

            # # Делю на обычный и trailing
            # BTC = round_down(BTC_bought / 2, 5)
            # Делю на большой и маленький ордер

            BTC_first = round_down(15 / price, 5)
            BTC_second = round_down(BTC - BTC_first, 5)

            try:
                if check == 0:
                    # Выставляю OCO ордер
                    client.new_margin_oco_order(symbol=symbol, isIsolated=True, side='SELL', quantity=BTC_first,
                                                price=take_profit, stopPrice=stop_loss, stopLimitPrice=stop_loss2,
                                                stopLimitTimeInForce='GTC')
            except:
                print(f'error 14 - {BTC_first}, {take_profit} , {stop_loss} , {stop_loss2}')
                send_report('error 14')
                check = 1
            try:
                if check == 0:
                    # Выставляю stop_loss для trailing
                    client.new_margin_order(symbol=symbol, side='SELL', type='STOP_LOSS_LIMIT', quantity=BTC_second,
                                            isIsolated=True, Price=stop_loss2, stopPrice=stop_loss, timeInForce='GTC')
            except:
                print(f'error 15 - {BTC_second}  , {take_profit} , {stop_loss} , {stop_loss2}')
                send_report('error 15')
                check = 1

            if check == 0:
                text1 = f'Открыл сделки по сигналу BUY\n Ордер SELL \ntake_profit:{take_profit}\nstop_loss:{stop_loss}\nstop_loss2:{stop_loss2} '
                try:
                    telegram_bot(token, text=text1)
                except:
                    print('error 20')
                    send_report('error 20')

    # Проверка на продажу
    elif signal == 'SELL' or signal == 'FORCE_SELL':
        if prev_side == 'BUY' or status == 'TRAILING_ORDER':
            price = df['close'][size - 1]
            try:
                close_and_repay(price)
            except:
                print('error close and repay 2')
                send_report('error close and repay 2')

        if prev_side == 'BUY' or status == 'TRAILING_ORDER' or status == 'EMPTY':
            try:
                deposit = float(get_deposit(symbol))
            except:
                print('error 15')
                send_report('error 15')
            # то можжно занимать и открывать ордера
            # ---------------------------------------------------------------------
            # БЛОК ПРОДАЖИ
            # ---------------------------------------------------------------------
            bet = deposit * 8.5
            price = df['close'][size - 1]
            stop_loss = price * 1.003
            prev_price = round_down(price)
            take_profit = price * 0.994
            take_profit = round_down(take_profit)
            stop_loss = round_down(stop_loss)
            stop_loss2 = round_down(stop_loss + 10)
            BTC_to_borrow = round_down(bet / price, 5)
            try:
                if check == 0:
                    # Занимаю BTC
                    client.margin_borrow(asset='BTC', amount=BTC_to_borrow, isIsolated=True, symbol=symbol)
            except:
                print(f'error 16 - {BTC_to_borrow}')
                send_report('error 16')
                check = 1
            try:
                if check == 0:
                    # Продаю BTC по рынку
                    client.new_margin_order(symbol=symbol, side='SELL', type='MARKET', quantity=BTC_to_borrow,
                                            isIsolated=True)
            except:
                print(f'error 17 - {BTC_to_borrow}')
                send_report('error 17')
                check = 1

            # # Делю на обычный и trailing
            # BTC = round_down(BTC_to_borrow / 2, 5)

            # Делю на большой и маленький ордер

            BTC_first = round_down(15 / price, 5)
            BTC_second = round_down(BTC - BTC_first, 5)

            try:
                if check == 0:
                    # Выставляю OCO ордер на покупку
                    client.new_margin_oco_order(symbol=symbol, isIsolated=True, side='BUY', quantity=BTC_first,
                                                price=take_profit, stopPrice=stop_loss, stopLimitPrice=stop_loss2,
                                                stopLimitTimeInForce='GTC')
            except:
                print(f'error 18 - {BTC_first} , {take_profit} , {stop_loss} , {stop_loss2}')
                send_report('error 18')
                check = 1
            try:
                if check == 0:
                    # Выставляю stop_loss для trailing
                    client.new_margin_order(symbol=symbol, side='BUY', type='STOP_LOSS_LIMIT', quantity=BTC_second,
                                            isIsolated=True, Price=stop_loss2, stopPrice=stop_loss, timeInForce='GTC')
            except:
                print(f'error 19 - {BTC_second} , {take_profit} , {stop_loss} , {stop_loss2}')
                send_report('error 19')
                check = 1

            if check == 0:
                text1 = f'Открыл сделки по сигналу SELL\n Ордер BUY \ntake_profit:{take_profit}\nstop_loss:{stop_loss}\nstop_loss2:{stop_loss2} '
                try:
                    telegram_bot(token, text=text1)
                except:
                    print('error 21')

    # Закрытие trailing order
    elif status == 'TRAILING_ORDER':
        check_close = False
        if prev_side == 'BUY':
            if df['vmc_sig2'][size - 1] == 'RED' and df['wt2'][size - 1] > 60:
                price = df['close'][size - 1]
                try:
                    close_and_repay(price)
                    check_close = True
                except:
                    print('error close and repay 3')
                    send_report('error close and repay 3')
        elif prev_side == 'SELL':
            if df['vmc_sig2'][size - 1] == 'GREEN' and df['wt2'][size - 1] < -60:
                price = df['close'][size - 1]
                try:
                    close_and_repay(price)
                    check_close = True
                except:
                    print('error close and repay 4')
                    send_report('error close and repay 4')

        if not check_close:
            side = ''
            order_price = 0
            BTC = 0
            # TODO Изменение стоп лоса для Trailing order
            try:
                info = get_order_price()
                order_price = float(info[0])
                BTC = float(info[1])
                side = info[2]
            except:
                print('error get order price')
                send_report('error get order price')

            if side == 'BUY' and prev_price != order_price and prev_price != 0:
                sl2 = round_down(prev_price + 10)
                # отменяем ордер
                try:
                    client.margin_open_orders_cancellation(symbol=symbol, isIsolated=True)
                except:
                    print('error 24')
                    send_report('error 24')
                # создаем новый
                try:
                    client.new_margin_order(symbol=symbol, side='BUY', type='STOP_LOSS_LIMIT', quantity=BTC,
                                            isIsolated=True, Price=sl2, stopPrice=prev_price, timeInForce='GTC')
                except:
                    print('error 25')
                    send_report('error 25')

            elif side == 'SELL' and prev_price != order_price and prev_price != 0:
                sl2 = round_down(prev_price - 10)
                # отменяем ордер
                try:
                    client.margin_open_orders_cancellation(symbol=symbol, isIsolated=True)
                except:
                    print('error 26')
                    send_report('error 26')
                # создаем новый
                try:
                    client.new_margin_order(symbol=symbol, side='SELL', type='STOP_LOSS_LIMIT', quantity=BTC,
                                            isIsolated=True, Price=sl2, stopPrice=prev_price, timeInForce='GTC')
                except:
                    print('error 27')
                    send_report('error 27')

    # ----------------------------------------------------------
    #   Проверка на возврат депозита
    # ----------------------------------------------------------
    try:
        repay()
    except:
        # print('error 23')
        # send_report('error 23')
        pass
    if prev_price == 0:
        try:
            prev_price = get_prev_price()
        except:
            print('error get prev price')

    time = datetime.now()
    time2 = df['date'][size - 1]
    if signal == '':
        signal = 'wait'
    print(f'Время: {time} {signal} Время для сверки: {time2} status: {status}')
    t.sleep(60)
