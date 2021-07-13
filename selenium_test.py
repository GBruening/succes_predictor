#%% 
import numpy as np
import time
import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

browser = webdriver.Chrome('C:\Windows\chromeDriver')


def find_val_in_str(string_in, search_string1, search_string2):
    idx1 = string_in.find(search_string1)+len(search_string1)
    idx2 = string_in.find(search_string2)
    return(string_in[idx1:idx2])

guild_list = []
for page_num in np.arange(1,4):
    
    url = 'https://www.warcraftlogs.com/zone/rankings/26#metric=progress&boss=2383'
    if page_num > 1:
        url = url + '&page=' + str(page_num)

    browser.get(url)
    if page_num == 1:
        time.sleep(10)
    else:
        time.sleep(3)

    print('Loaded Website')
    html = browser.page_source

    html = BeautifulSoup(html, 'html.parser')
    html_listed = html.findAll('a')#, href=True, id=True)

    tr_pull = html.findAll('tr')

    for k, item in enumerate(tr_pull):
        if str(item).find('sorting_1">')>-1:
            td_pull = item.findAll('td')
            
            guild_rank = find_val_in_str(str(td_pull[0]),'sorting_1">','\n\t</td>')
            guild_ilvl = find_val_in_str(str(td_pull[3]),'nowrap="">','\n\n</td>')

            a_pull = item.findAll('a')
            for a in a_pull:
                a_str = str(a)
                if a_str.find('main-table-guild')>-1 and a_str.find('/">')>-1:
                    guild_name = find_val_in_str(a_str,'/">','</a')
                    guild_id = find_val_in_str(a_str,'/guild/id/','/">')
                elif a_str.find('main-table-guild')>-1:
                    guild_name = find_val_in_str(a_str,'-done">','</a')
                    guild_id = find_val_in_str(a_str,'/reports/','#fight=')
            # asdfasdfasdf
            guild_list.append({'name': guild_name,
                            'id':   guild_id,
                            'rank': guild_rank,
                            'ilvl': guild_ilvl})

    #%% 
    print('Parsing Html')
            
    print('Done Html, page: ' + str(page_num))
        
with open('guild_list.json', 'w', encoding = 'utf-8') as f:
    json.dump(guild_list, f, ensure_ascii=False, indent = 4)


# %%
