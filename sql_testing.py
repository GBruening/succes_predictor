#%%
from sqlalchemy import create_engine
import pandas as pd
import json

with open('get_guild_list/guild_list_hungering.json', encoding='utf-8') as f:
    guilds = json.load(f)

# DC is guild 725
guild_num = 725
guild_info = {'guild_name': guilds[guild_num]['name'],
              'realm': guilds[guild_num]['realm'].replace(' ','-'),
              'region': guilds[guild_num]['region']}

with open(guild_info['guild_name']+'_prog_pulls.json', encoding = 'utf-8') as f:
    prog_pulls = json.load(f)
prog_pulls = pd.read_json(prog_pulls)

engine = create_engine('sqlite://',echo=False)

prog_pulls.to_sql(name = 'nathria_prog', con = engine)
# %%

# %%
import pyodbc
server = 'localhost'
database = 'postgres'
username = 'postgres'
password = 'postgres'

con = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
cusor = cnsn.cursor()


# %%
import psycopg2
