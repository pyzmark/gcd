import pandas as pd
import numpy as np
import re

pd.set_option('display.max_columns', 5000) 
pd.set_option('display.max_rows', 5000)

gcd = pd.read_csv('~/Dropbox/git/gcd/gcd_raw.csv')

# Pandas doesn't like Nans, esp since next step is converting the floats in pleaides to int
# we replace them with the code for the Med from Pleiades

gcd['pleiades'] = gcd['pleiades'].fillna(1043)

# going straight to str would mean leaving a ".00" at the end. this doesn't
gcd['pleiades'] = gcd['pleiades'].astype(int)
gcd['pleiades'] = gcd['pleiades'].astype(str)

import urllib3
from bs4 import BeautifulSoup
import requests
from urllib.request import urlopen, Request
import json

gcd['lat'] = ""
gcd['long'] = ""

# to avoid doing this for all the doubled mint places, we put all unique
# pleiades numbers into a list, which will be the basis for scraping
uniplei = gcd.pleiades.unique()

# those results go into a dictionary. We will assign latlong based on this
pleidic = {}
for i in uniplei:
    try:
        URL = "https://pleiades.stoa.org/places/" + i + "/json"
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")
        # But it does not return a JSON object, rather HTML. So you'll have to strip that
        # Also, you need to cast soup as a string, as it comes out as a beautiful soup object
        soup = str(soup)
        pleijson = json.loads(soup)
        long = pleijson['reprPoint'][0]
        lat = pleijson['reprPoint'][1]
        pleidic.update({i: [lat,long]})
    except:
        pleidic.update({i: [0,0]})
        continue

# syracuse specifically has a messed up pleiades JSON entry. So we manually enter it here
pleidic.update({'462503': [37.0687655418,15.284171651]})

pldf = pd.DataFrame.from_dict(pleidic, orient='index')
pldf = pldf.rename(columns={"0":"lat","1":"long"})
pldf = pldf.reset_index()

# put in lat long based on pleidic
for row,i in enumerate(gcd['pleiades']):
    gcd['lat'].loc[row] = pleidic[i][0]
    gcd['long'].loc[row] = pleidic[i][1]

gcd.to_csv(path_or_buf='gcd_raw.csv')
