from ibapi.tag_value import TagValue
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.client import Contract, Order
from ibapi.execution import Execution
from ibapi.order import Order
from decimal import Decimal
import queue
import time
import datetime
from threading import Thread
import pandas as pd
from lightweight_charts import Chart

#ESTA FUNCIONANDO - VERIFICAR CALCULOS Y LATENCIA 

# create a queue for data coming from Interactive Brokers API
# Add global variables to store data separately for graphing and calculation
graph_data_queue = queue.Queue()
calc_data_queue = queue.Queue()

# a list for keeping track of any indicator lines
current_lines = []

# initial chart symbol to show
INITIAL_SYMBOL = "NVDA"
INITIAL_POSITION = "BUY"
END_POSITION = "SELL"
# settings for live trading vs. paper trading mode
LIVE_TRADING = False
LIVE_TRADING_PORT = 7496
PAPER_TRADING_PORT = 7497
TRADING_PORT = PAPER_TRADING_PORT
if LIVE_TRADING:
    TRADING_PORT = LIVE_TRADING_PORT

# these defaults are fine
DEFAULT_HOST = '127.0.0.1'
DEFAULT_CLIENT_ID = 1

# Client for connecting to Interactive Brokers
class PTLClient(EWrapper, EClient):
     
    def __init__(self, host, port, client_id):
        EClient.__init__(self, self) 
        self.data = [] 
        self.datalow=[]
        self.atr_data = None  # Store ATR data
        self.prev_low_val = None
        self.connect(host, port, client_id)

        # create a new Thread
        thread = Thread(target=self.run)
        thread.start()


    def error(self, req_id, code, msg, misc):
        if code in [2104, 2106, 2158]:
            print(msg)
        else:
            print('Error {}: {}'.format(code, msg))

# callback when historical data is received from Interactive Brokers
    def historicalData(self, req_id, bar):
        t = datetime.datetime.fromtimestamp(int(bar.date))

        # Create a dictionary for each bar received
        data = {
            'date': t,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': int(bar.volume)
        }

        # Route data to the appropriate queue based on req_id
        if req_id == 1:  # Graph data
            graph_data_queue.put(data)
        elif req_id == 2:  # Calculation data
            calc_data_queue.put(data)


    def historicalDataEnd(self, reqId, start, end):
        print(f"end of data {start} {end}")
        if reqId == 1:  # Graph data
            print("Graph data received. Updating chart.")
            update_chart()
        elif reqId == 2:  # Calculation data
            print("Calculation data received. Performing calculations.")
            self.collect_data_from_queue()
            atr_values = self.calculate_atr(14)
            print("ATR 14 Values:\n", atr_values.iloc[-1]['ATR'])
            self.atr_data = atr_values.iloc[-1]['ATR']
            
            if self.atr_data is not None and self.prev_low_val is not None:
                self.place_order_if_ready()
            else:
                print("ATR or Previous Low not calculated. Order will not be placed.")


    def calculate_atr(self, period):
        """
        Calculates the ATR (Average True Range) for the given period.
        :param period: The number of periods to use for the ATR calculation (e.g., 14).
        :return: A pandas Series with the ATR values.
        """
        # Ensure valid data exists
        if not self.data:
            return pd.DataFrame()  # return empty if no data

        # Create a DataFrame from the collected data
        df = pd.DataFrame(self.data)
        print(df.head(5))

        # Ensure that the 'date' column is properly sorted and valid
        #df['date'] = pd.to_datetime(df['date'])  # Convert to datetime if necessary

        # Calculate True Range (TR)
        df['prev_close'] = df['close'].shift(1)
        df['TR'] = df[['high', 'prev_close']].max(axis=1) - df[['low', 'prev_close']].min(axis=1)
        # Calculate ATR using a rolling window
        df['ATR'] = df['TR'].rolling(window=period).mean()

        return df[['date', 'ATR']].dropna()
    
    def get_previous_low(self):
                # Ensure valid data exists
        if not self.datalow:
            return pd.DataFrame()  # return empty if no data

        # Create a DataFrame from the collected data
        df = pd.DataFrame(self.datalow)
        df['prev_low'] = df['low'].shift(1)
        return df['prev_low'].iloc[-1] 

    
    def collect_data_from_queue(self):
        """
        Collects all data from the queue and stores it in a list.
        """
        while not calc_data_queue.empty():
            self.data.append(calc_data_queue.get())
        
    

    #def nextValidId(self, orderId: int):
    #    super().nextValidId(orderId)
    #    self.order_id = orderId
    #    print(f"next valid id is {self.order_id}")

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.order_id = orderId
        print(f"next valid id is {self.order_id}")

        # Create a contract for AAPL stock
        mycontract = Contract()
        mycontract.symbol = INITIAL_SYMBOL
        mycontract.secType = "STK"    
        mycontract.exchange = "SMART"
        mycontract.currency = "USD"
        
        # Request contract details for AAPL
        self.reqContractDetails(orderId, mycontract)


    def place_order_if_ready(self):
        """
        Place an order if the required values are calculated.
        """
        try:
            limit_price = round(self.prev_low_val + 0.5 * self.atr_data, 2)
            print("Limit Price:", limit_price)

            # Create a contract for the order
            mycontract = Contract()
            mycontract.symbol = INITIAL_SYMBOL
            mycontract.secType = "STK"
            mycontract.exchange = "SMART"
            mycontract.currency = "USD"

            # Create an order object
            myorder = Order()
            myorder.action = INITIAL_POSITION
            myorder.orderType = "LMT"
            myorder.lmtPrice = limit_price
            myorder.totalQuantity = 100

            # Place the order
            self.placeOrder(self.order_id, mycontract, myorder)
            print("Order placed successfully.")

            #Create order for stop loss
            stop_price =round(self.prev_low_val - 0.1 * self.atr_data, 2)
            print('Stop Loss Price: ', stop_price)
            stop_order_id = self.order_id + 1
            order = Order()
            order.action = END_POSITION  
            order.totalQuantity = 100
            order.orderType = "STP"  # Stop order
            order.auxPrice = stop_price  # Stop price
            self.placeOrder(stop_order_id, mycontract, order)
            print("Stop placed successfully.")

        except Exception as e:
            print(f"Error placing order: {e}")

    def openOrder(self, orderId: int, contract: Contract, order: Order, orderState):
        print(f"openOrder. orderId: {orderId}, contract: {contract}, order: {order}")

    def orderStatus(self, orderId: int, status: str, filled: Decimal, remaining: Decimal, avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
        print(f"orderId: {orderId}, status: {status}, filled: {filled}, remaining: {remaining}, avgFillPrice: {avgFillPrice}, permId: {permId}, parentId: {parentId}, lastFillPrice: {lastFillPrice}, clientId: {clientId}, whyHeld: {whyHeld}, mktCapPrice: {mktCapPrice}")

    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        print(f"reqId: {reqId}, contract: {contract}, execution: {execution}")



# Separate function for calculation data request
def get_calc_data(symbol, timeframe):
    print(f"Getting calculation data for {symbol} {timeframe}")

    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    what_to_show = 'TRADES'

    client.reqHistoricalData(
        2, contract, '', '1 W', timeframe, what_to_show, True, 2, False, []
    )

    
# called by charting library when the
def get_bar_data(symbol, timeframe):
    print(f"getting bar data for {symbol} {timeframe}")

    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    what_to_show = 'TRADES'
    
    #now = datetime.datetime.now().strftime('%Y%m%d %H:%M:%S')
    chart.spinner(True)

    client.reqHistoricalData(
        1, contract, '', '30 D', timeframe, what_to_show, True, 2, False, []
    )

    time.sleep(1)
       
    chart.watermark(symbol)


# handler for the screenshot button
def take_screenshot(key):
    img = chart.screenshot()
    t = time.time()
    with open(f"screenshot-{t}.png", 'wb') as f:
        f.write(img)


def on_search(chart, searched_string):
    get_bar_data(searched_string, chart.topbar['timeframe'].value)
    chart.topbar['symbol'].set(searched_string)


def on_timeframe_selection(chart):
    print("Selected timeframe")
    print(chart.topbar['symbol'].value, chart.topbar['timeframe'].value)
    get_bar_data(chart.topbar['symbol'].value, chart.topbar['timeframe'].value)
    

# callback for when the user changes the position of the horizontal line
def on_horizontal_line_move(chart, line):
    print(f'Horizontal line moved to: {line.price}')



# called when we want to update what is rendered on the chart 
def update_chart():
    global current_lines
    try:
        bars = []
        while True:  # Keep checking the queue for new data
            data = graph_data_queue.get_nowait()
            bars.append(data)
    except queue.Empty:
        print("empty queue")
    finally:
        # once we have received all the data, convert to pandas dataframe
        df = pd.DataFrame(bars)
        print(df)

        # set the data on the chart
        chart.set(df)
        
        if not df.empty:
            # draw a horizontal line at the high
            chart.horizontal_line(df['high'].max(), func=on_horizontal_line_move)

            # if there were any indicator lines on the chart already (eg. SMA), clear them so we can recalculate
            if current_lines:
                for l in current_lines:
                    l.delete()
            
            current_lines = []

            # calculate any new lines to render
            # create a line with SMA label on the chart
            line = chart.create_line(name='SMA 50')
            line.set(pd.DataFrame({
                'time': df['date'],
                f'SMA 50': df['close'].rolling(window=50).mean()
            }).dropna())
            current_lines.append(line)

            # once we get the data back, we don't need a spinner anymore
            chart.spinner(False)


if __name__ == '__main__':
    # create a client object
    client = PTLClient(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)

    # create chart object, specify display settings
    chart = Chart(toolbox=True, width=1000, inner_width=1, inner_height=1)

    chart.legend(True)
    
    # set up a function to call when searching for symbol
    chart.events.search += on_search

    # set up top bar
    chart.topbar.textbox('symbol', INITIAL_SYMBOL)

    # give ability to switch between timeframes
    chart.topbar.switcher('timeframe', ('1 min', '5 mins', '1 hour'), default='1 min', func=on_timeframe_selection)

    # populate initial chart
    get_calc_data(INITIAL_SYMBOL, '1 hour')
    get_bar_data(INITIAL_SYMBOL, '1 min')

    # create a button for taking a screenshot of the chart
    chart.topbar.button('screenshot', 'Screenshot', func=take_screenshot)

    # show the chart
    chart.show(block=True)