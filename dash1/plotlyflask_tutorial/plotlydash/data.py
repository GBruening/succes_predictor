"""Prepare data for Plotly Dash."""
import numpy as np
import pandas as pd
import os

def create_dataframe():
    """Create Pandas DataFrame from local CSV."""
    print(os.getcwd())
    df = pd.read_csv("D:/Google Drive/succes_predictor/dash/data/311-calls.csv", parse_dates=["created"])
    df["created"] = df["created"].dt.date
    df.drop(columns=["incident_zip"], inplace=True)
    num_complaints = df["complaint_type"].value_counts()
    to_remove = num_complaints[num_complaints <= 30].index
    df.replace(to_remove, np.nan, inplace=True)
    return df
