import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import numpy as np
import re
import folium
from folium import plugins
import altair as alt

# From Jupyter notebook
# Load Data
df = pd.read_csv('gcd_raw.csv')
df['mint_location'] = df['mint_location'].str.title()
df['denomination'] = df['denomination'].str.title()
# Begin Streamlit app below

app_title = 'Greek Coin Dies'
#app_subtitle = 'An Overview'

def display_graph(df, metal, mint_location, denomination, report_type, field_name, graph_title, range_min, range_max):
    df = df[(df['range_min'] > range_min) & (df['range_max'] < range_max)]
    if mint_location:
        df = df[df['mint_location'] == mint_location]
    if denomination:
        df = df[df['denomination'] == denomination]
    blocks = blocks = [-550, -525, -500, -475, -450, -425, -400, -375, -350, -325]
    block = -550
    sublist = []
    while block < -300:
        br_min = block
        br_max = block + 25
        sub = df[(df['range_min'] > br_min) & (df['range_max'] < br_max)]
        sumsub = sub['number_of_obverse_dies'].sum()
        sublist.append(sumsub)
        block = block + 25
    dies = pd.DataFrame({
    "Dies": sublist,
    "Time":  blocks})
    line_chart = alt.Chart(dies).mark_line().encode(
    alt.X('Time'),
    alt.Y('Dies', scale=alt.Scale(domain=(0, 900))),
       ).configure_axis(grid=False).configure_view(
    strokeWidth=1).properties(
    width=400,
    height=200
)
#    st.line_chart(sublist, height=100)
    st.altair_chart(line_chart, use_container_width=True)

def display_metric(df, metal, mint_location, denomination, report_type, field_name, metric_title, range_min, range_max):
    df = df[(df['range_min'] > range_min) & (df['range_max'] < range_max)]
    if mint_location:
        df = df[df['mint_location'] == mint_location]
    if denomination:
        df = df[df['denomination'] == denomination]
    total = df[field_name].sum()
    st.metric(metric_title, '{:,}'.format(int(total)))


def display_map(df, mint_location, denomination, range_min, range_max):
    latitude = 38
    longitude = 25

    if denomination:
        df = df[df['denomination'] == denomination]
    if mint_location:
        df = df[df['mint_location'] == mint_location]
    if range_min:
        df = df[df['range_min'] > range_min]
    if range_max:
        df = df[df['range_max'] < range_max]

    # This is needed for the map. If this is a drag on data, we might
    # want to pre-construct this later and import it through pickle
    # we need a list of distinct cities
    summed = df.groupby(by=["mint_location", "lat", "long"]).sum()
    summed = summed.reset_index(level=["mint_location", "lat", "long"])

    # Create map and display it
    test_map = folium.Map(
        location=[latitude, longitude], zoom_start=5, tiles='cartodbdark_matter'
    )

    colorcom = ['#C5E9FB', '#FEFBC9', '#CDFBC5', '#E8BC53',
        '#AD53E8', '#FE4850', '#C9DFFE', '#F8FEC9', '#D68787']
    periods = ['_524_500', '_499_475', '_474_450', '_449_425',
        '_424_400', '_399_375', '_374_350', '_349_325', '_324_300']

    # folium.TileLayer('cartodbpositron').add_to(test_map)

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

    # function to populate the map with bubbles and labels that include
    # information like title, time period active, etc.
    sign = folium.map.FeatureGroup(show=True)
    signsize = list(summed['number_of_obverse_dies'])

    # add pop-up text to each marker on the map
    signlatitudes = list(summed.lat)
    signlongitudes = list(summed.long)
    labels = list(
        summed.mint_location.astype(str) + ' produced ' + summed['number_of_obverse_dies'].astype(str) +
        ' dies between ' + summed['range_min'].astype(str) + " and " + summed['range_max'].astype(str) + ' BCE.'
    )
    for lat, lng, label, size in zip(signlatitudes, signlongitudes, labels, signsize):
        if size == 0:
            continue
        else:
            sign.add_child(
                folium.features.CircleMarker(
                    [lat, lng],
                        # define how big you want the circle markers to be
                        radius=radiator(size)*2,
                        color='black',
                        fill=True,
                        fill_color='#FE4850',
                        fill_opacity=0.8,
                        opacity=1,
                        weight=0.3,
                        popup=folium.Popup(label, parse_html=True)
                        )
                    )
    test_map.add_child(sign)
    sign.layer_name = 'Obverse Coin Dies'

#    folium.LayerControl(collapsed=False).add_to(test_map)

    return test_map 

def main():
    st.set_page_config(app_title)
    st.title(app_title)
#    st.caption(app_subtitle)


    metal = ''
    mint_location = ''
    denomination = ''
    #range_min = -430.00
    #range_max = -400.00
    report_type = 'obverse dies'
    metric_title = f'Number of {report_type}'
    graph_title = f'Dies from the {mint_location} mint'
    

    # Display filters and map
    slider_range = st.sidebar.slider("Date Range", -550, -300, (-550,-300))
    range_min = slider_range[0]
    range_max = slider_range[1]

    city_list = list(df['mint_location'].unique())
    city_list = [x for x in city_list if str(x) != 'nan']
    city_list.sort()
    city_list = ['All'] + city_list

    city_selector = st.sidebar.selectbox("Select State", (city_list))
    mint_location = city_selector

    if city_selector == 'All':
        mint_location = ''

    denom_list = list(df['denomination'].unique())
    denom_list = [x for x in denom_list if str(x) != 'nan']
    denom_list.sort()
    denom_list = ['All'] + denom_list 

    denom_selector = st.sidebar.selectbox("Select Denomination", (denom_list))
    denomination = denom_selector
   
    if denom_selector == 'All':
        denomination = ''

    # Display metrics
#    if mint_location:
#        st.subheader(f'{report_type} for {mint_location}')
#    else:
#        st.subheader(f'{report_type}')

    col1, col2 = st.columns(2)
    with col1:
        display_metric(df, metal,mint_location,denomination,report_type,'number_of_obverse_dies',metric_title, range_min, range_max)
    with col2:
        display_graph(df, metal,mint_location,denomination,report_type,'number_of_obverse_dies',metric_title, range_min, range_max)

    test_map = display_map(df, mint_location, denomination, range_min, range_max)
    st_data = st_folium(test_map, width=750, height=500)

    #st.write(df.shape)
    #st.write(df.head(20))
    #st.write(df.columns)

if __name__ == "__main__":
    main()
