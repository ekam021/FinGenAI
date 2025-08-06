import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

def forecast_expense(df, category='Overall', months=3):
    df['Month'] = df['Date'].dt.to_period('M').astype(str)

    if category != 'Overall':
        df = df[df['Category'] == category]

    monthly_summary = df[df['Amount'] < 0].groupby('Month')['Amount'].sum().abs().reset_index()
    monthly_summary['MonthIndex'] = np.arange(len(monthly_summary))

    if len(monthly_summary) < 2:
        return None, "Not enough data to forecast."

    model = LinearRegression()
    X = monthly_summary[['MonthIndex']]
    y = monthly_summary['Amount']
    model.fit(X, y)

    future_indices = np.arange(len(monthly_summary), len(monthly_summary) + months).reshape(-1, 1)
    forecast = model.predict(future_indices)

    future_months = pd.date_range(start=pd.to_datetime(monthly_summary['Month'].iloc[-1]) + pd.DateOffset(months=1),
                                  periods=months, freq='M').strftime('%Y-%m')

    forecast_df = pd.DataFrame({'Month': future_months, 'Predicted_Expense': forecast.round(2)})
    return forecast_df, None

