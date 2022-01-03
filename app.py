from flask import Flask, render_template, request
import alpaca_trade_api as tradeapi
import config, json, requests
import datetime
import re
import time
import dropbox

app = Flask(__name__)

api = tradeapi.REST(config.API_KEY, config.API_SECRET, base_url='https://paper-api.alpaca.markets')

slippage_factor = 1.0006
sell_slippage_factor = 0.9994
live_trade_start_time = '14:30:00'
live_trade_end_time = '20:58:00'

@app.route('/')
def dashboard():
    orders = api.list_orders()
    
    return render_template('dashboard.html', alpaca_orders=orders)


def get_open_orders():
    return api.list_orders(status='open')

def check_runaway_open_order(order_side, order_price):
    _order=None
    if get_open_orders() is not None:
        if len(get_open_orders())>0:
            _order = get_open_orders()[0]
            
            if _order.side=="buy" and order_side=="buy":
                #if new price is higher than old price
                if _order.limit_price < order_price:
                    return True
                else:
                    return False
                
            elif _order.side=="sell" and order_side=="sell":
                #if new price is lower than old price
                if _order.limit_price > order_price:
                    return True
                else:
                    return False
            
    return False
def get_position(symbol='TQQQ'):

    try:
        qty = int(api.get_position(symbol).qty)
        position = api.get_position(symbol)
    except:
        # No position exists
        qty = 0
        position=None
    
    return qty, position


def check_status(mystatus, id):
    #order = api.get_order(id)._raw
    my_order = api.get_order_by_client_order_id(id)
    print('my_order.status', my_order.status)
    print('check for ', mystatus)
    return True if my_order.status == mystatus else False

def wait_until(status, order_id, api=None, max_wait=59):
    
    count = 0
    while not check_status(status, order_id):
        time.sleep(1)
        count += 1
        if count >= max_wait:
            
            print(order_id)
            return False
    return True
#wait_until_filled = wait_until("filled")
def cancel_current_orders():
    if get_open_orders() is not None:
        if len(get_open_orders())>0:

            current_order=get_open_orders()[0]
            if current_order is not None:
                api.cancel_order(current_order.id)

    return
def send_order(target_qty, last_price, symbol):
    position, client_order_id= None, None 
    # We don't want to have two orders open at once
    sell_side="sell"
    buy_side = "buy"
    
    position, position_obj = get_position()
    print('position', position)

    if not ((datetime.datetime.now().time() >= datetime.datetime.strptime(live_trade_start_time, ("%H:%M:%S")).time()) &
        (datetime.datetime.now().time() <= datetime.datetime.strptime(live_trade_end_time,("%H:%M:%S")).time())):
        print('outside live trading hours')
        #return
    
    delta = int(target_qty) - position

    if delta == 0:
        cancel_current_orders()
        return
    
    print(f'Ordering towards {target_qty}...')
    try:
        if delta > 0:
            if position < 0 and target_qty > 0: #e.g. position is -1 and target is 2
                print('position', position)
                #get flat
                buy_qty = min(abs(position), delta)
                print(f'Close Position: Buying {buy_qty} shares.')
                client_order_id = 'close_short_'+re.sub('[^A-Za-z0-9]+', '', str(datetime.datetime.now()))
                cancel_current_orders()
                current_order = api.submit_order(
                    symbol, buy_qty, buy_side,
                    'limit', 'day', last_price, client_order_id=client_order_id
                )
                # Get our order using its Client Order ID.
                my_order = api.get_order_by_client_order_id(client_order_id)
                print('Got order ', my_order.client_order_id, my_order.status)
                wait_until("filled", client_order_id)
                #check_fill = _thread.start_new_thread(check_order_fill, tuple(client_order_id))
                #_thread.current_thread.join(check_fill)
                #go long
                print(f'Buying ', target_qty,' shares at ', last_price)
                client_order_id = 'Buying_' + \
                    re.sub('[^A-Za-z0-9]+', '', str(datetime.datetime.now()))
                
                if False:#check_runaway_open_order(buy_side, last_price):#False:#
                    pass
                else:
                    # Get our order using its Client Order ID.
                    current_order = api.submit_order(
                        symbol, int(target_qty), buy_side,
                        'limit', 'day', last_price*slippage_factor, client_order_id=client_order_id
                )
                #wait_until("filled", client_order_id)
            elif position < 0 and target_qty == 0:  # e.g. position is -1 and target is 0
                print('position', position)
                #get flat
                buy_qty = min(abs(position), delta)
                print(f'Close Position: Buying {buy_qty} shares.')
                client_order_id='close_short_' + re.sub('[^A-Za-z0-9]+', '', str(datetime.datetime.now()))
                cancel_current_orders()
                current_order = api.submit_order(
                    symbol, buy_qty, buy_side,
                    'limit', 'day', last_price, client_order_id=client_order_id
                )
                my_order = api.get_order_by_client_order_id(client_order_id)

                # check_fill = _thread.start_new_thread(check_order_fill, tuple(client_order_id))
                #wait_until("filled", client_order_id)
                print('Got order ', my_order.client_order_id, my_order.status)
            elif (position < 0 and target_qty < 0) or (position == 0 and target_qty > 0):  # position is -2 and target is -1
                buy_qty = delta
                client_order_id = 'Buying_' + \
                    re.sub('[^A-Za-z0-9]+', '', str(datetime.datetime.now()))

                print('position', position)
                print(f'Buying {buy_qty} shares at ', last_price)

                if False:#check_runaway_open_order(buy_side, last_price):#False:#
                    pass
                else:
                    cancel_current_orders()
                    current_order = api.submit_order(
                        symbol, buy_qty, buy_side,
                        'limit', 'day', last_price*slippage_factor, client_order_id=client_order_id)

                # check_fill = _thread.start_new_thread(check_order_fill, tuple(client_order_id))
                #wait_until("filled", client_order_id)
        elif delta < 0:
            
            if position > 0 and target_qty < 0:  # e.g. position is 1 and target is -2
                print('position', position)
                sell_qty = min(abs(position), abs(delta))
                print(f'Close Position: Selling {sell_qty} shares.' )
                client_order_id='close_long_' + \
                    re.sub('[^A-Za-z0-9]+', '', str(datetime.datetime.now()))
                cancel_current_orders()
                current_order = api.submit_order(
                    symbol, sell_qty, sell_side,
                    'limit', 'day', last_price, client_order_id=client_order_id
                )
                my_order = api.get_order_by_client_order_id(client_order_id)
                print('Got order ', my_order.client_order_id, my_order.status)
                # check_fill = _thread.start_new_thread(check_order_fill, tuple(client_order_id))  # _thread.current_thread.join(check_fill)
                wait_until("filled", client_order_id)

                print(f'Selling ', abs(target_qty), ' shares at ', last_price)
                client_order_id = 'Selling_' + \
                    re.sub('[^A-Za-z0-9]+', '', str(datetime.datetime.now()))


                if False:#check_runaway_open_order(buy_side, last_price):#False:#
                    pass
                else:
                    current_order = api.submit_order(
                        symbol, int(abs(target_qty)), sell_side,
                        'limit', 'day', last_price*sell_slippage_factor, client_order_id=client_order_id
                    )  # position = get_position()
                #wait_until("filled", client_order_id)
            elif position > 0 and target_qty == 0:  # e.g. position is 1 and target is 0
                print('position', position)
                sell_qty = min(abs(position), abs(delta))
                print(f'Close Position: Selling {sell_qty} shares.')
                cancel_current_orders()
                client_order_id = 'close_long_'+re.sub('[^A-Za-z0-9]+', '', str(datetime.datetime.now()))


                cancel_current_orders()
                current_order = api.submit_order(
                    symbol, sell_qty, sell_side,
                    'limit', 'day', last_price, client_order_id=client_order_id
                )
                my_order = api.get_order_by_client_order_id(client_order_id)
                print('Got order ', my_order.client_order_id, my_order.status)
                # check_fill = _thread.start_new_thread(check_order_fill, tuple(client_order_id))
                #wait_until("filled", client_order_id)

            elif(position > 0 and target_qty > 0) or (position == 0 and target_qty < 0 ):  # position is 2 and target is 1
                sell_qty = abs(delta)
                #delta = int(target_qty) - position
                print(f'Selling {sell_qty} shares at ', last_price)
                client_order_id = 'Selling_' + \
                    re.sub('[^A-Za-z0-9]+', '', str(datetime.datetime.now()))

                if False:#check_runaway_open_order(buy_side, last_price):#False:#
                    pass
                else:
                    cancel_current_orders()
                    current_order = api.submit_order(
                    symbol, sell_qty, sell_side,
                    'limit', 'day', last_price*sell_slippage_factor, client_order_id=client_order_id
                )
                # check_fill = _thread.start_new_thread(check_order_fill, tuple(client_order_id))
                #wait_until("filled", client_order_id)

    except Exception as e:
        print(e)


@app.route('/webhook', methods=['POST'])
def webhook():
    webhook_message = json.loads(request.data)

    if webhook_message['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            'code': 'error',
            'message': 'nice try buddy'
        }
    
    price = webhook_message['strategy']['order_price']
    quantity = webhook_message['strategy']['position_size']
    symbol = webhook_message['ticker']
    side = webhook_message['strategy']['order_action']
    
    #order = api.submit_order(symbol, quantity, side, 'limit', 'gtc', limit_price=price)
    send_order( quantity, price, symbol)
    # if a DISCORD URL is set in the config file, we will post to the discord webhook
    if config.DISCORD_WEBHOOK_URL:
        chat_message = {
            "username": "strategyalert",
            "avatar_url": "https://i.imgur.com/4M34hi2.png",
            "content": f"tradingview strategy alert triggered: {quantity} {symbol} @ {price}"
        }

        requests.post(config.DISCORD_WEBHOOK_URL, json=chat_message)

    return webhook_message

def write_dropbox_message( quantity, price, symbol):
    try:
            
        dbx = dropbox.Dropbox(config.DB_App1_ACCESS_TOKEN,
                            app_key=config.db_app_key, app_secret=config.db_app_secret)
        filename = r'/herokusync/NQ1H_KNN.csv'
        f, r = dbx.files_download(filename)
        data = str(r.content, encoding='utf-8')
        
        data+= str(datetime.datetime.now()) +','+ quantity+',' + price +',' + symbol +',' +"\r\n"
        dbx.files_upload(bytes(data, encoding='utf-8'), filename, mute=True, mode=dropbox.files.WriteMode.overwrite)
    except Exception as e:
        print(e)
        return False
    return True


@app.route('/webhooknq1h', methods=['POST'])
def webhooknq1h():
    webhook_message = json.loads(request.data)

    if webhook_message['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            'code': 'error',
            'message': 'nice try buddy'
        }
    
    price = webhook_message['strategy']['order_price']
    quantity = webhook_message['strategy']['position_size']
    symbol = webhook_message['ticker']
    side = webhook_message['strategy']['order_action']
    
    #order = api.submit_order(symbol, quantity, side, 'limit', 'gtc', limit_price=price)
    result = write_dropbox_message( quantity, price, symbol)
    # if a DISCORD URL is set in the config file, we will post to the discord webhook
    if config.DISCORD_WEBHOOK_URL:
        chat_message = {
            "username": "strategyalert",
            "avatar_url": "https://i.imgur.com/4M34hi2.png",
            "content": f"tradingview strategy alert triggered: {quantity} {symbol} @ {price}"
        }

        requests.post(config.DISCORD_WEBHOOK_URL, json=chat_message)

    return webhook_message, result