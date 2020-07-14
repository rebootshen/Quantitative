import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn import preprocessing
# from sklearn.impute import SimpleImputer

import utils_s


# imp = SimpleImputer(missing_values=[np.nan, np.inf, -np.inf], strategy='most_frequent')

def Momentum(close,window_length):
    
    momentum = close.apply(lambda x:(x - x.shift(window_length))/x).iloc[(window_length-1):,:].fillna(0)
    momentum_drz = pd.DataFrame(data = preprocessing.scale(momentum),
                                                           index = momentum.index,
                                                           columns = momentum.columns)
    
    return momentum_drz

def Smooth(factor, window_length):
    
    smooth_factor = factor.rolling(window=window_length).mean().iloc[(window_length-1):,:].fillna(0)
    
    return smooth_factor

def Returns(close,window_length):
    
    returns = close.apply(lambda x:(x - x.shift(window_length))/x).iloc[(window_length-1):,:].fillna(0)
    
    return returns

def overnight_sentiment(close, openn, window_length, trailing_window):
    
    return_over = pd.DataFrame(index = close.index, columns=close.columns)
    close_shifted = close.apply(lambda x:x.shift(window_length))

    for date in close.index:
        return_over.loc[date] = (openn.loc[date] - close_shifted.loc[date]) / close_shifted.loc[date]

    overnight_sentiment = return_over.rolling(trailing_window).sum()
    
    overnight_sentiment_drz = pd.DataFrame(data = preprocessing.scale(overnight_sentiment),
                                                       index = overnight_sentiment.index,
                                                       columns = overnight_sentiment.columns)  
    
    return overnight_sentiment_drz

def direction(close, openn, window_length, trailing_window):
    
    p = ((close - openn)/close)*-1

    p.replace([np.inf, -np.inf], np.nan, inplace=True)    
    rolling_p = p.rolling(trailing_window).sum()
    direction_scaled = pd.DataFrame(data = preprocessing.scale(rolling_p),
                                                       index = rolling_p.index,
                                                       columns = rolling_p.columns)  
    
    return direction_scaled

def sentiment(close, high, low, sent, trailing_window, universe):
    
    indexer = close.index
    
    total = sent['news_volume'].unstack('ticker')[universe]
    score = sent['sentiment'].unstack('ticker')[universe]
    
    close = close[universe]
    high = high[universe]
    low = low[universe]
    
    assert len(close.columns) == len(total.columns) == len(score.columns)
    
    p = ((high-low)/close)
    v = p.rolling(trailing_window).sum()
    s = (total*score).rolling(trailing_window).sum()
    final = (v*s)*-1
  
    assert len(final.columns) == len(close.columns)
    
    sent_factor_scaled = pd.DataFrame(data = preprocessing.scale(final),
                               index = final.index,
                               columns = final.columns).reindex(indexer)
    
    sent_factor_scaled = sent_factor_scaled[universe]
    assert len(sent_factor_scaled.columns) == len(close.columns)
    
    return sent_factor_scaled
    
def Fund_QReturn(multi_df,factor):
    
    factor_unstack = multi_df[factor].unstack('Symbol')
    
    plt.figure(figsize=(20,10))
    plt.plot(factor_unstack)
    plt.xticks(rotation=70)
    plt.grid(True)
    plt.legend(factor_unstack.columns)
    plt.show()

    factor_unstack_chge = ((factor_unstack - factor_unstack.shift(1))/factor_unstack.shift(1)).iloc[1:,:]
    dates= {}

    for tick in factor_unstack_chge.columns:
        dates[tick] = []
        for date in factor_unstack_chge.index:
            if factor_unstack_chge.loc[date,tick]!=0:
                dates[tick].append(date)
                
    for tick in factor_unstack_chge.columns:
        i=0
        for date in factor_unstack_chge.index:
            try:
                if date == dates[tick][i]:
                    try:
                        factor_unstack_chge.loc[slice(date,dates[tick][i+1] - pd.Timedelta(days=1)),tick] = factor_unstack_chge.loc[date,tick]
                    except:
                        factor_unstack_chge.loc[date:,tick] = factor_unstack_chge.loc[date,tick]
                        continue
                    i=i+1
            except:
                pass
    
    return factor_unstack_chge