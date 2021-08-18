#%%
import numpy as np
import json
import os
import pandas as pd
import time
from datetime import datetime
import seaborn as sns
from matplotlib import pyplot as plt

from sqlalchemy import create_engine
import psycopg2
server = 'localhost'
database = 'nathria_prog'
username = 'postgres'
password = 'postgres'

if 'conn' in locals():
    conn.close()
engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
curs = conn.cursor()



# curs.execute('select * from "nathria_prog";')
# temp_df = pd.DataFrame(curs.fetchall())
# temp_df.columns = [desc[0] for desc in curs.description]
#%%