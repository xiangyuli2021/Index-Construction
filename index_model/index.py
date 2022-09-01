import datetime as dt
import pandas as pd
import numpy as np

class IndexModel:
    def __init__(self) -> None:
        
        # read provided data
        self.stock = pd.read_csv('data_sources/stock_prices.csv',parse_dates=['Date'],index_col=0,dayfirst=True)

        # use the weight determined for each day and multiply by the daily return to obtain the portforlio daily return
        self.weighted_daily_Return = []
        
    def calc_index_level(self, start_date: dt.date, end_date: dt.date) -> None:
         
        # index universe stock names
        stock_names = list(self.stock.columns)
        
        # number of stocks in the index universe
        stock_number = len(stock_names)

        # number of month required for index value calculation
        number_of_month = (start_date.year - end_date.year) * 12 + end_date.month - start_date.month + 1
        
        # start date
        start_date = pd.to_datetime(start_date)
        
        # calculate each stocks daily return
        for one_stock in stock_names:
            self.stock[one_stock + '_daily_return'] = self.stock[one_stock].pct_change()
        
        # find the last business day in each month
        last_day = self.stock.loc[self.stock.groupby(self.stock.index.to_period('M')).apply(lambda x: x.index.max())]
        
        # based on the mkt captilization value as of the last business day select 3 stocks to include in the index
        c = ['1st Mkt Cap','2nd Mkt Cap','3rd Mkt Cap']
        stock_selection = (last_day.apply(lambda x: pd.Series(x.nlargest(3).index, index=c), axis=1))
        
        # number of business days for each month in the year of 2020
        number_of_days = self.stock.loc[self.stock.index >= start_date].index.to_period('M').value_counts().sort_index()
        
        # weight is used to store each month's stock weights based on their mkt cap
        weight = np.zeros((number_of_month,stock_number))
        
        for i in range(number_of_month):
            for j in range(stock_number):
                if stock_names[j] == stock_selection.iloc[i,0]:
                    weight[i,j] = 0.5
                elif stock_names[j] == stock_selection.iloc[i,1]:
                    weight[i,j] = 0.25
                elif stock_names[j] == stock_selection.iloc[i,2]:
                    weight[i,j] = 0.25
                    
        # for each month, the weight is determined on the last day at the previous month
        # so for each month, only one weight array is needed, repeat that array based on the number of business days for each month
        weight_arr = []
        
        for i in range(number_of_month):
            
            if i == number_of_month - 1:
                weight_arr.append(np.tile(weight[i,:],(number_of_days[i]-1,1)))
            else:
                weight_arr.append(np.tile(weight[i,:],(number_of_days[i],1)))
               
        # because the starting day's return is not required, just append the original daily return here to keep the datetime index consistent
        self.weighted_daily_Return.append(self.stock.loc[[start_date], stock_names[0] + '_daily_return':stock_names[-1] + '_daily_return'])
        
        # obtain the first business day for each month in 2020
        dates1 = pd.date_range(start=pd.Timestamp(start_date), periods=12, freq='BMS')
        
        # obtain the second business day for each month in 2020, since the selection becomes effective at the end of first business day
        dates2 = pd.date_range(start=pd.Timestamp(start_date), periods=12, freq='BMS') + pd.Timedelta(days=1)
        
        for i in range(number_of_month):
            
            if i == number_of_month-1:
                self.weighted_daily_Return.append(self.stock.loc[dates2[i]:,stock_names[0] + '_daily_return':stock_names[-1] + '_daily_return'] * weight_arr[i])
            
            else:
                self.weighted_daily_Return.append(self.stock.loc[dates2[i]:dates1[i+1],stock_names[0] + '_daily_return':stock_names[-1] + '_daily_return'] * weight_arr[i])
            
        # merge each month's return together into a single dataframe    
        self.weighted_daily_Return= pd.concat(self.weighted_daily_Return)
        
        # obtain the row sum to get the portfolio return
        self.weighted_daily_Return['Sum'] = self.weighted_daily_Return[list(self.weighted_daily_Return)].sum(axis=1)

        # assign the starting index value
        self.weighted_daily_Return.loc[start_date,'index_value'] = 100
        
        # calculate the index value based on the daily portfolio return
        for i in range(1,self.weighted_daily_Return.shape[0]):
            self.weighted_daily_Return.iloc[i,-1] = self.weighted_daily_Return.iloc[i-1,-1]*(1+self.weighted_daily_Return.iloc[i,-2])

    def export_values(self, file_name: str) -> None:
        
        self.weighted_daily_Return['index_value'].to_csv(file_name)
