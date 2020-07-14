from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.scanner import ScannerSubscription
from ibapi.ticktype import TickTypeEnum
from ibapi.common import *
from ibapi.tag_value import TagValue
from ibapi.execution import ExecutionFilter


import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep, strftime, localtime,time 

sleeptime = 2

#ORDERS
#########################################################
#########################################################   

def read_nextvalidid(reqId):

    class TestApp(EWrapper, EClient):

        def __init__(self):
            EClient.__init__(self,self)

            self.nextValidOrderId = []
            

        def error(self, reqId:TickerId, errorCode:int, errorString:str):
            if reqId > -1:
                print("Error. Id: " , reqId, " Code: " , errorCode , " Msg: " , errorString)
            
        def nextValidId(self,orderId):
            super().nextValidId(orderId)
            self.nextValidOrderId.append(orderId)
            print("NextValidId:", orderId)
            self.disconnect()
           
    app = TestApp()
    app.connect('127.0.0.1', 7497, 0)
    
    app.reqIds(-1)
    nid = app.nextValidOrderId
        
    app.run()
    sleep(sleeptime)
    
    return nid[0]

def placing_orders(orderId, reqId, symbol, sec_type, exch, prim_exch, curr, order_type, quantity, action, positions):
    
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exch
    contract.primaryExchange = prim_exch
    contract.currency = curr
    
    order = Order()
    order.orderType = order_type
    order.totalQuantity = quantity
    order.action = action
     

    class TestApp(EWrapper, EClient):

        def __init__(self):
            EClient.__init__(self,self)

        def error(self, reqId:TickerId, errorCode:int, errorString:str):
            if reqId > -1:
                print("Error. Id: " , reqId, " Code: " , errorCode , " Msg: " , errorString)

    app = TestApp()
    app.connect('127.0.0.1', 7497, 0)        
  
    app.placeOrder(orderId = orderId, contract = contract, order = order)
    print ('order quantity placed for {} is: {} '.format(contract.symbol, order.totalQuantity))
        
    sleep(sleeptime)
    
    return order, contract

    app.disconnect()
    app.run()


def read_positions(subscribe, acctCode):
    
    class TestApp(EWrapper, EClient):


        def __init__(self):
            EClient.__init__(self,self)
            self.up = pd.DataFrame([], columns = ['Position', 'marketPrice', 'marketValue', 'averageCost', 'unrealizedPNL', 'realizedPNL'])
            
        def error(self, reqId:TickerId, errorCode:int, errorString:str):
            if reqId > -1:
                print("Error. Id: " , reqId, " Code: " , errorCode , " Msg: " , errorString)
            
        def updatePortfolio (self, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName):
            self.up.index.name = 'Symbol'            
            self.up.loc[contract.symbol] = position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL
            
        def positionEnd(self):
            super().positionEnd()
            print("PositionEnd")
            self.cancelPositions()
            self.disconnect()

            
    app = TestApp()
    app.connect('127.0.0.1', 7497, 0)
    
    app.reqAccountUpdates(subscribe = subscribe, acctCode = acctCode)
    app.reqPositions()
    
    update = app.up
    
    app.run()
    
    sleep(sleeptime)
    print ('Reading Portfolio')
    rows = update[update['Position']==0].index
    update.drop(rows,axis=0,inplace =True)
#     update.loc['Total',:] = update.sum()           
#     idx = update.index.tolist()
#     idx.pop(idx.index('Total'))
#    ani = update.reindex(idx+['Total'])

    return update

def read_account(reqId, subscribe, acctCode):
    
    class TestApp(EWrapper, EClient):

        def __init__(self):
            EClient.__init__(self,self)
            self.up = pd.DataFrame([],columns=['Values'])
            
        def error(self, reqId:TickerId, errorCode:int, errorString:str):
            if reqId > -1:
                print("Error. Id: " , reqId, " Code: " , errorCode , " Msg: " , errorString)
            
        def updateAccountValue(self, key, value, currency, accountName):

            self.up.index.name = 'Keys'
            self.up.loc[key] = value
            
        def accountDownloadEnd(self, account):

            print("AccountDownloadEnd. Account:", account)
            self.disconnect()

    app = TestApp()
    app.connect('127.0.0.1', 7497, 0)

    app.reqAccountUpdates(subscribe = subscribe, acctCode = acctCode)
    
    update = app.up
    
    app.reqAccountUpdates(False, acctCode)
    
    app.run()
    
    sleep(sleeptime)
    print ('Reading Account')
    return update    


def cancel_openorders():
    
    class TestApp(EWrapper, EClient):

        def __init__(self):
            EClient.__init__(self,self)
            self.open_orders = pd.DataFrame(columns = ['action','quantity',
                                                       'type','algoStrategy',
                                                       'algoParams','pre_status','status'])

        def error(self, reqId:TickerId, errorCode:int, errorString:str):
            if reqId > -1:
                print("Error. Id: " , reqId, " Code: " , errorCode , " Msg: " , errorString)

        def openOrder(self, orderId, Contract, Order, OrderState):
            super().openOrder(orderId, Contract, Order, OrderState)

            self.open_orders.loc[Contract.symbol,:] = [Order.action ,
                                                       Order.totalQuantity, 
                                                       Order.orderType,
                                                       Order.algoStrategy,
                                                       Order.algoParams[0],
                                                       OrderState.status,'canceled']

        def cancelOrder(self,orderId):
            super().cancelOrder(orderId)
            print('cancel order ended')
            #self.disconnect()

        def openOrderEnd(self):
            super().openOrderEnd()
            print('open order ended')
            self.disconnect()

    app = TestApp()
    app.connect('127.0.0.1', 7497, 0)

    #app.reqIds(-1)
    app.reqAllOpenOrders()
    open_orders = app.open_orders

    app.reqGlobalCancel()

    app.run()
    sleep(sleeptime)

    return open_orders


def get_openorders():
    
    class TestApp(EWrapper, EClient):

        def __init__(self):
            EClient.__init__(self,self)
            self.open_orders = pd.DataFrame(columns = ['action','executed_orders',
                                                       'type','algoStrategy',
                                                       'algoParams','status'])

        def error(self, reqId:TickerId, errorCode:int, errorString:str):
            if reqId > -1:
                print("Error. Id: " , reqId, " Code: " , errorCode , " Msg: " , errorString)

        def openOrder(self, orderId, Contract, Order, OrderState):
            super().openOrder(orderId, Contract, Order, OrderState)

            self.open_orders.loc[Contract.symbol,:] = [Order.action ,
                                                       Order.totalQuantity, 
                                                       Order.orderType,
                                                       Order.algoStrategy,
                                                       Order.algoParams[0],
                                                       OrderState.status]

        def openOrderEnd(self):
            super().openOrderEnd()
            print('open order ended')
            self.disconnect()

    app = TestApp()
    app.connect('127.0.0.1', 7497, 0)

    app.reqIds(-1)
    app.reqAllOpenOrders()
    open_orders = app.open_orders

    app.run()
    sleep(sleeptime)

    return open_orders


def closing_positions(stock_to_close, portfolio, order_id):
    
    class TestApp(EWrapper, EClient):

        def __init__(self):
            EClient.__init__(self,self)

        def error(self, reqId:TickerId, errorCode:int, errorString:str):
            if reqId > -1:
                print("Error. Id: " , reqId, " Code: " , errorCode , " Msg: " , errorString)

    app = TestApp()
    app.connect('127.0.0.1', 7497, 0)

    if app.isConnected():
        print ('app is running ...')
        print ('closing {} positions which are not present in action'.format(len(stock_to_close)))
        # Closing Position

        for i in stock_to_close :

            contract = Contract()
            contract.symbol = i
            contract.secType = 'STK'
            contract.exchange = 'SMART'
            #contract.primaryExchange = 'ISLAND'
            contract.currency = 'USD'

            order = Order()
            order.orderType = 'MKT'
            order.totalQuantity = int(np.abs(portfolio.loc[i,'Position']))

            if portfolio.loc[i,'Position'] > 0:

                order.action = 'SELL'
                #order.cashQty = weigth * 1.5 * net_liq
                order.algoStrategy = 'Adaptive'
                order.algoParams = []
                order.algoParams.append(TagValue("adaptivePriority", 'Normal'))

                app.placeOrder(orderId = order_id, contract = contract, order = order)
                order_id = order_id + 1
                print ('closing position for {} is: {} '.format(contract.symbol, order.totalQuantity))

            elif portfolio.loc[i,'Position'] < 0:

                order.action = 'BUY'
                #order.cashQty = weigth * 1.5 * net_liq
                order.algoStrategy = 'Adaptive'
                order.algoParams = []
                order.algoParams.append(TagValue("adaptivePriority", 'Normal'))

                app.placeOrder(orderId = order_id, contract = contract, order = order)
                order_id = order_id + 1
                print ('closing position for {} is: {} '.format(contract.symbol, order.totalQuantity))
                

    else:
        print ('app not connected')

    app.disconnect()        
    return order_id+1
        
def rebalancing_to_leverage(action_balance, order_id):
    
    class TestApp(EWrapper, EClient):

        def __init__(self):
            EClient.__init__(self,self)

        def error(self, reqId:TickerId, errorCode:int, errorString:str):
            if reqId > -1:
                print("Error. Id: " , reqId, " Code: " , errorCode , " Msg: " , errorString)



    if app.isConnected():
        print ('app is running ...')
        print ('balancing {} positions'.format(len(action_balance.index)))
        # Closing Position

        for i in action_balance.index:

            contract = Contract()
            contract.symbol = i
            contract.secType = 'STK'
            contract.exchange = 'SMART'
            contract.currency = 'USD'

            order = Order()
            order.orderType = 'MKT'
            order.totalQuantity = np.abs(action_balance.loc[i,'shares'])

            if action_balance.loc[i,'shares'] > 0:

                order.action = 'BUY'
                order.algoStrategy = 'Adaptive'
                order.algoParams = []
                order.algoParams.append(TagValue("adaptivePriority", 'Normal'))
                app.placeOrder(orderId = order_id, contract = contract, order = order)
                order_id = order_id + 1
                print (' buy order quantity placed for {} is: {} '.format(contract.symbol, order.totalQuantity))

            elif action_balance.loc[i,'shares'] < 0:

                order.action = 'SELL'
                order.algoStrategy = 'Adaptive'
                order.algoParams = []
                order.algoParams.append(TagValue("adaptivePriority", 'Normal'))
                app.placeOrder(orderId = order_id, contract = contract, order = order)
                order_id = order_id + 1
                print (' sell order quantity placed for {} is: {} '.format(contract.symbol, order.totalQuantity))

    else:
        print ('app not connected')
    app.disconnect()        
        
        
def placing_final_orders(action_final, order_id):        

    class TestApp(EWrapper, EClient):

        def __init__(self):
            EClient.__init__(self,self)

        def error(self, reqId:TickerId, errorCode:int, errorString:str):
            if reqId > -1:
                print("Error. Id: " , reqId, " Code: " , errorCode , " Msg: " , errorString)
    
    app = TestApp()
    app.connect('127.0.0.1', 7497, 0)
    
    for ticker in action_final.index:

        contract = Contract()
        contract.symbol = ticker
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        #contract.primaryExchange = 'ISLAND'
        contract.currency = 'USD'

        order = Order()
        order.orderType = 'MKT'

        order.totalQuantity = np.abs(action_final.loc[ticker])[0]

        if action_final.loc[ticker][0] > 0:

            order.action = 'BUY'
            order.algoStrategy = 'Adaptive'
            order.algoParams = []
            order.algoParams.append(TagValue("adaptivePriority", 'Normal'))

            app.placeOrder(orderId = order_id, contract = contract, order = order)
            order_id = order_id + 1
            print ('buy order quantity placed for {} is: {} '.format(contract.symbol, order.totalQuantity))

        elif action_final.loc[ticker][0] < 0:

            order.action = 'SELL'
            order.algoStrategy = 'Adaptive'
            order.algoParams = []
            order.algoParams.append(TagValue("adaptivePriority", 'Normal'))

            app.placeOrder(orderId = order_id, contract = contract, order = order)
            order_id = order_id + 1
            print ('sell order quantity placed for {} is: {} '.format(contract.symbol, order.totalQuantity))

    app.disconnect()
    
def commission_report(acctCode, time):
    
    class TestApp(EWrapper, EClient):

        def __init__(self):
            EClient.__init__(self,self)

            self.executed_orders = pd.DataFrame(columns=['ticker',
                                                         'time','shares', 'action',
                                                         'price','marketValue',
                                                         'RealizedPNL','commission'])
            self.val = 0
            self.val2 = 0

        def error(self, reqId:TickerId, errorCode:int, errorString:str):
            if reqId > -1:
                print("Error. Id: " , reqId, " Code: " , errorCode , " Msg: " , errorString)

        def execDetails(self, reqId, contract, execution):
            super().execDetails(reqId, contract, execution)

            self.executed_orders.loc[self.val,['ticker',
                                               'time',
                                               'shares',
                                               'action',
                                               'price',
                                               'marketValue']] = [contract.symbol, 
                                                            pd.to_datetime(execution.time),
                                                            execution.shares,execution.side,execution.price,
                                                            execution.shares*execution.price]

            self.val = self.val + 1
            
        def commissionReport(self, commissionReport):
            super().commissionReport(commissionReport)

            self.executed_orders.loc[self.val2,['RealizedPNL','commission']] = [float(commissionReport.realizedPNL), 
                                                                                float(commissionReport.commission)]
            
            self.val2 = self.val2 + 1

        def execDetailsEnd(self,reqId):
            super().execDetailsEnd(reqId)
            self.disconnect()


    execution_filter = ExecutionFilter()
    execution_filter.acctCode = acctCode
    execution_filter.time = time

    app = TestApp()
    app.connect('127.0.0.1', 7497, 0)

    app.reqExecutions(0,execution_filter)
    df = app.executed_orders

    app.run()
    sleep(sleeptime)
    
    df.set_index('time',inplace=True)
    df.sort_values(by='time',inplace=True)
    df['RealizedPNL'][df['RealizedPNL']>1000000] = 'OPEN'
    
    return df


def execute_stocks(close,optimal_weights_regularized):
    
    df_c = pd.DataFrame(data=close[optimal_weights_regularized.index].iloc[-1].values,
                   index = close[optimal_weights_regularized.index].iloc[-1].index,
                   columns = ['close'])
    df_c.index.name = 'asset'

    optimal_weights_regularized_rounded = np.round(optimal_weights_regularized,2)
    name = optimal_weights_regularized_rounded.columns[0]
    
    optimal_rounded = optimal_weights_regularized_rounded[optimal_weights_regularized_rounded[name] != 0.00]

    return optimal_rounded










