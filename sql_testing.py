#%%
from sqlalchemy import create_engine
import pandas as pd
import json
import psycopg2

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

# engine = create_engine('sqlite://',echo=False)

# prog_pulls.to_sql(name = 'nathria_prog', con = engine)

# # %%
# import psycopg2
# server = 'localhost'
# database = 'dvdrental'
# username = 'postgres'
# password = 'postgres'

# conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
# curs = conn.cursor()
# curs.execute("select exists(select * from information_schema.tables where table_name=%s)", ('actor',))
# curs.fetchone()[0]
# # test = curs.execute('SELECT * FROM actor','dvd')

# my_table = pd.read_sql('select * from actor', conn)

#%%
from sqlalchemy import create_engine
server = 'localhost'
database = 'nathria_prog'
username = 'postgres'
password = 'postgres'

engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
curs = conn.cursor()
curs.execute("select exists(select * from information_schema.tables where table_name=%s)", (guild_info['guild_name'],))

if not curs.fetchone()[0]:
    prog_pulls.to_sql(guild_info['guild_name'],engine)



# %%
