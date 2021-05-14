import base64
import streamlit as st
import folium
from streamlit_folium import folium_static
from folium import IFrame
from folium.plugins import HeatMap


png = ["sites/statue_of_liberty.PNG",
           "sites/central_park.PNG",
           "sites/Top_of_the_Rock.PNG",
           "sites/Rockefeller_Center.PNG",
           "sites/Metropolitan_measum.PNG",
           "sites/Broadway.PNG",
           "sites/empire_state.PNG",
           "sites/9-11.PNG",
           "sites/high_line.PNG",
           "sites/times_squars.PNG",
           "sites/brooklin_bridge.PNG",
           "sites/fifth_avenue.PNG",
           "sites/central_terminal.PNG",
           "sites/one_world_obd.PNG",
           "sites/the_frick.PNG",
           "sites/library.PNG"]


def app(df_listings, df_attractions):
    html_temp = """
            <div><font color=\"#C8C8C8\" size=\"18\"><strong>Is there any connection between NY City's attraction and the Airbnb prices?</font></div><br>
            <div><font color=\"#C8C8C8\" size=\"6\">How many Airbnb listings are located in NY?</font></div>"""
    st.markdown(html_temp, unsafe_allow_html=True)

    st.markdown("This website will provide you with an easy and fun search on the available Airbnb accommodation in New York City. "
    "We know that in a city as big and expensive as New York, finding a suitable apartment can be a daunting task. "
    "You can find interactive tools that illustrate the variation of the values of the key fields \(such as price, ratings, etc.\). ")

    df_heatmap = df_listings.copy()
    df_heatmap['count'] = 1

    map_hooray = folium.Map([40.730610, -73.935242], zoom_start=11, tiles="OpenStreetMap")
    heatmap = HeatMap(data=df_heatmap[['latitude', 'longitude', 'count']].groupby(
        ['latitude', 'longitude']).sum().reset_index().values.tolist(), radius=8, max_zoom=13)

    heatmap.add_to(map_hooray)

    popup = []

    for i in range(len(png)):
        encoded = base64.b64encode(open(png[i], 'rb').read()).decode()
        building_name = df_attractions.Attraction[i]
        html = building_name
        html += '<img src="data:image/png[i];base64,{}" width="100" height="100">'.format(encoded)
        iframe = IFrame(html, width=130, height=150)
        popup.append(folium.Popup(iframe, max_width=130))

    for i in range(len(png)):
        folium.Marker([df_attractions.latitude[i], df_attractions.longitude[i]], popup=popup[i],
                      icon=folium.Icon(color='blue', icon_color='white', icon='globe')).add_to(map_hooray)

    folium_static(map_hooray, width=1000, height=600)