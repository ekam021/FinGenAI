import pandas as pd
import streamlit as st
import pandas as pd
import plotly.express as px

def load_transactions(file):
    df = pd.read_csv(file)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Amount'] = df['Amount'].replace('[₹,+]', '', regex=True).astype(float)
    return df

def categorize_expenses(df):
    def get_category(desc):
        desc = desc.lower()
        if 'amazon' in desc or 'flipkart' in desc:
            return 'Shopping'
        elif 'swiggy' in desc or 'zomato' in desc:
            return 'Food'
        elif 'salary' in desc or 'freelance' in desc:
            return 'Income'
        elif 'electricity' in desc or 'bill' in desc:
            return 'Utilities'
        elif 'movie' in desc:
            return 'Entertainment'
        else:
            return 'Others'
    df['Category'] = df['Description'].apply(get_category)
    return df

def get_summary(df):
    expense_df = df[df['Amount'] < 0]
    summary = expense_df.groupby('Category')['Amount'].sum().abs().sort_values(ascending=False)
    return summary



