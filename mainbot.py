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

#ESTA FUNCIONANDO - VERIFICAR CALCULOS Y LATENCIA 

# create a queue for data coming from Interactive Brokers API
# Add global variables to store data separately for graphing and calculation
calc_data_queue = queue.Queue()
low_data_queue = queue.Queue()

# a list for keeping track of any indicator lines
current_lines = []

# initial chart symbol to show
INITIAL_SYMBOL = "MSFT"
INITIAL_POSITION = "SELL"

if INITIAL_POSITION == "BUY":
    END_POSITION = "SELL"
elif INITIAL_POSITION == "SELL":
    END_POSITION = "BUY"
else:
    print('Incorrect Position')


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
        print('connected')

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
            low_data_queue.put(data)
        elif req_id == 2:  # Calculation data
            calc_data_queue.put(data)


    def historicalDataEnd(self, reqId, start, end):
        print(f"end of data {start} {end}")
        if reqId == 1:  # Graph data
            self.collect_data_from_queue_low()
            self.prev_low_val = self.get_previous_low()
            print('Previous Low: ', self.prev_low_val)
            if self.atr_data is not None and self.prev_low_val is not None:
                self.place_order_if_ready()
            else:
                print("ATR or Previous Low not calculated. Order will not be placed.")
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

        # Ensure that the 'date' column is properly sorted and valid
        #df['date'] = pd.to_datetime(df['date'])  # Convert to datetime if necessary

        # Calculate True Range (TR)
        df['prev_close'] = df['close'].shift(1)
        df['TR'] = df[['high', 'prev_close']].max(axis=1) - df[['low', 'prev_close']].min(axis=1)
        # Calculate ATR using a rolling window
        df['ATR'] = df['TR'].rolling(window=period).mean()
        df['ATR'] = df['ATR']/1.7

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

    def collect_data_from_queue_low(self):
        """
        Collects all data from the queue and stores it in a list.
        """
        while not low_data_queue.empty():
            self.datalow.append(low_data_queue.get())
        
    

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
        if INITIAL_POSITION == "BUY":
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
        elif INITIAL_POSITION == "SELL":
            try:
                limit_price = round(self.prev_low_val - 0.5 * self.atr_data, 2)
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
                stop_price =round(self.prev_low_val + 0.1 * self.atr_data, 2)
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
        else: 
            print('No initial position indicated')
            

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
    client.reqHistoricalData(
        1, contract, '', '1 D', timeframe, what_to_show, True, 2, False, []
    )

if __name__ == '__main__':
    # create a client object
    client = PTLClient(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
    time.sleep(1)
    if client.isConnected():
        get_calc_data(INITIAL_SYMBOL, '1 hour')
        get_bar_data(INITIAL_SYMBOL, '1 min')
    else:
        print("Client is not connected.")

