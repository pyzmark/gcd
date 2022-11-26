import pandas as pd
import numpy as np
import re

# Import my mediated dataset. This encodes all dating in
# the form of columns which sum relevant die output according
# to 25 yr period. This is sub-optimal. I will imporove
# this someday
gcd = pd.read_csv('~/Dropbox/git/gcd/gcd_raw.csv')

# Pandas doesn't like Nans, esp since next step is converting the floats in pleaides to int
# we replace them with the code for the Med from Pleiades
gcd['pleiades'] = gcd['pleiades'].fillna(1043)

# going straight to str would mean leaving a ".00" at the end. this doesn't
gcd['pleiades'] = gcd['pleiades'].astype(int)
gcd['pleiades'] = gcd['pleiades'].astype(str)

# Libraries for scraping Pleiades (we need lat/long)
# luckily gcd already has the Pleiades numbers in a column
import urllib3
from bs4 import BeautifulSoup
import requests
from urllib.request import urlopen, Request
import json

# columns have to exist to be populated. So this does that
gcd['lat'] = ""
gcd['long'] = ""

# to avoid doing this for all the doubled mint places, we put all unique
# pleiades numbers into a list, which will be the basis for scraping
# Saves times
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

# put in lat long based on pleidic
for row,i in enumerate(gcd['pleiades']):
    gcd['lat'].loc[row] = pleidic[i][0]
    gcd['long'].loc[row] = pleidic[i][1]

# realistically at some point I will probbly want to redo the data structure so that gcd looks 
# different than it does. gcd is a mediated data set, based on rawer data that appears in a
# rather different form
# but at this point, I just want to get this finished

# we need a list of distinct cities in gcd
summed = gcd.groupby(by=["mint_location","lat","long"]).sum()
summed = summed.reset_index(level=["mint_location","lat","long"])

# Below is used to set up the various colors for the different eras, which are keyed to the date codes in 'periods'
colorcom = ['#C5E9FB','#FEFBC9','#CDFBC5','#E8BC53','#AD53E8','#FE4850','#C9DFFE','#F8FEC9','#D68787']
periods = ['_524_500','_499_475','_474_450','_449_425','_424_400','_399_375','_374_350','_349_325','_324_300']

# Some libraries for making the map
import folium
from folium import plugins

# Build the map, focusing on Europe
latitude = 38
longitude = 25

# Create map and display it
test_map = folium.Map(
    location=[latitude, longitude], zoom_start=5, tiles='cartodbdark_matter'
)

# Here we determine the size of bubbles based on
# die numbers. Gets passed on to builder below
def radiator(dies):
    if dies == 0:
        return 0
    elif dies < 1:
        return 1
    elif dies < 2:
        return 2
    elif dies < 5:
        return 3
    elif dies < 10:
        return 4
    elif dies < 20:
        return 5
    elif dies < 50:
        return 6
    elif dies < 100:
        return 7
    else:
        return 8

# capitalize mint locations for readbility on labels
summed['mint_location'] = summed['mint_location'].str.capitalize()

# The counter is there so that we can show only one layer
# and hide the rest. When it is zero, the layer is shown
# the below function adds one after the first loop and hides
# all subsequent layers
counter = 0

# function to populate the map with bubbles and labels that include
# information like title, time period active, etc.
def adder(this,colnum):
    global counter
    
    # clean up date ranges for labels
    date = re.sub(r'(_)(\d\d\d)(_)(\d\d\d)', '\\2-\\4', i)
    
    # this uses the above counter variable to hide everything
    # after the first layer
    if counter == 1:
        sign = folium.map.FeatureGroup(show=False)
    else:
        sign = folium.map.FeatureGroup(show=True)
        counter += 1
    signsize = list(summed[i])

    # add pop-up text to each marker on the map
    signlatitudes = list(summed.lat)
    signlongitudes = list(summed.long)
    labels = list(
        summed.mint_location.astype(str) + ' produced ' + summed[i].astype(str) + \
        ' dies between ' + date + ' BCE.' 
    )
    for lat, lng, label, size in zip(signlatitudes, signlongitudes, labels, signsize):
        if size == 0:
            continue
        else:
            sign.add_child(
                folium.features.CircleMarker(
                    [lat, lng],
                    radius=radiator(size)*2,  # define how big you want the circle markers to be
                    color='black',
                    fill=True,
                    fill_color=colorcom[colnum],
                    fill_opacity=0.8,
                    opacity=1,
                    weight=0.3,
                    popup=folium.Popup(label, parse_html=True)
                )
        )
    test_map.add_child(sign)
    sign.layer_name = date + ' BCE'

# this actualizes the function above. enumerate allows us to 
# control certain aspects of the function
for row, i in enumerate(periods):
    adder(i,row)

# construct map altogether    
folium.LayerControl(collapsed=False).add_to(test_map)

# Save it to index.html, since my site is pointed to this
test_map.save("index.html")