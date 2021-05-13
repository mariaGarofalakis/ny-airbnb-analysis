import base64
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import folium_static
from folium import IFrame
from folium.plugins import MarkerCluster
import numpy as np


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
    neighs = df_listings['neighbourhood'].unique()

    st.subheader("Prices and Ratings distributions")
    st.markdown(
        "On the left side of the panel there is an interactive field where we can select  the neighbourhood and the price range of our disire. "
        "In addition a distribution of prices and user's ratings are shown by the two figures above according to our selections. "
        "In that way we can compare the values of prices between different neighbourhoods and choose the one which is more suitable to our budget ")

    ###################### round prices #############################
    df_listings = df_listings.assign(round_price=np.ceil(df_listings['price'] / 50.0) * 50)

    ################################ streamlit ######################################################
    rprt_status = st.sidebar.selectbox("Choose Neighbourhood(*)", neighs)
    minimum = st.sidebar.number_input("Minimum Price (Starting from: 5$)", min_value=5, max_value=10000, value=300, step=50)
    maximum = st.sidebar.number_input("Maximum Price (Up to: 10000$)", min_value=5, max_value=10000, value=700, step=50)
    if minimum > maximum:
        st.error("Please enter a valid range")
    st.sidebar.write("(*) The neighbourhoods are sorted based on their distance from the tourist attractions")

    col1, col2 = st.beta_columns([2, 2])
    filtered_data = df_listings[
        (df_listings['neighbourhood'] == rprt_status) & (df_listings['round_price'] >= minimum) & (
                df_listings['round_price'] <= maximum)].copy()
    fig1 = px.histogram(filtered_data, x='round_price', width=800, height=350)
    fig1.update_traces(marker_color='#428DB2', marker_line_color='#428DB2',
                      marker_line_width=1.5, opacity=0.8)
    col1.plotly_chart(fig1)

    fig2 = px.histogram(filtered_data, x='review_scores_rating', width=800, height=350)
    fig2.update_traces(marker_color='#428DB2', marker_line_color='#428DB2',
                       marker_line_width=1.5, opacity=0.8)
    col2.plotly_chart(fig2)

    st.subheader('Map of listings for selected neighbourhood')

    st.markdown(
        "In order to get a better intution of how the listings are distributed is space we provide a map of NY city where all the selected listings are "
        "teamed together into clusters. If you zoom in a specific cluster you can get the exact location of the listing. Also by clicking "
        "a specific marker a pop up window is showing up, which provides us with informations for the price and the user's ratings for this specific listing. "
        "On the map there are markers with NY city's most significant attractions so as we can relate the distance of the available listings "
        "with those regions of the city with the most interesting places to visit. Finally by clicking the attraction's marker a picture of it shows up "
        "which is a good indication for a new visitor of the city.")

    popup = []

    for i in range(len(png)):
        encoded = base64.b64encode(open(png[i], 'rb').read()).decode()
        building_name = df_attractions.Attraction[i]
        html = building_name
        html += '<img src="data:image/png[i];base64,{}" width="100" height="100">'.format(encoded)
        iframe = IFrame(html, width=130, height=150)
        popup.append(folium.Popup(iframe, max_width=130))

    map_hooray = folium.Map([40.730610, -73.935242], zoom_start=11, tiles="OpenStreetMap")

    for i in range(len(png)):
        folium.Marker([df_attractions.latitude[i], df_attractions.longitude[i]], popup=popup[i],
                      icon=folium.Icon(color='blue', icon_color='white', icon='globe')).add_to(map_hooray)

    # add a marker for every record in the filtered data, use a clustered view
    marker_cluster = MarkerCluster().add_to(map_hooray)  # create marker clusters
    for index, row in filtered_data.iterrows():
        html = "Price: " + str(row.price) + "$" + "<br>" + "Rating: " + str(row.review_scores_rating)

        iframe = folium.IFrame(html, width=130, height=60)

        new_pops = folium.Popup(iframe, max_width=130)

        folium.Marker([row.latitude, row.longitude], radius=5, popup=new_pops, ).add_to(marker_cluster)

    folium_static(map_hooray, width=1000, height=600)