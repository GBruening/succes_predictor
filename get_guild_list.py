#%% Cell 1
import numpy as np
import json
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup


from contextlib import closing
from requests import get
from requests.exceptions import RequestException

# from Bio import Entrez
# Entrez.api_key = "YOUR API KEY"

import string

#%% 
def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        print('Error during requests to {0} : {1}'.format(url, str(e)))
        return None

def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)

url = 'https://www.warcraftlogs.com/zone/rankings/26#metric=progress&boss=2383'
url = 'https://www.warcraftlogs.com/'
html = simple_get(url)
html = BeautifulSoup(html, 'html.parser')

test = html.findAll('a')#, href=True, id=True)

#%% 
guild_list = []
for a in test:
    if a.get('class') and a['class'][0].find('main-table-guild')>0:
        adsfasdf

# %%
