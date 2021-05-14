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
    
    st.sidebar.title('Selection')
    
    neighs = df_listings['neighbourhood'].unique()
    neighs = np.concatenate([['Radius from the attractions'], neighs])
    
    queries = ['Lowest price', 'Highest score', 'Highest response rate', 'Popularity']
    parameters = ['price', 'review_scores_rating', 'host_response_rate', 'reviews_per_month']
    orders = [True, False, False, False]
    
    lat_mean = df_attractions.latitude.mean()
    lon_mean = df_attractions.longitude.mean()
    
    rprt_status = st.sidebar.selectbox("Choose Radius or Neighbourhood", neighs)
    
    if rprt_status == 'Radius from the attractions':
        radius = st.sidebar.slider("Select a radius (km)", min_value=0.25, max_value=10.0, value=2.0, step=0.25)
        filtered_data = df_listings[df_listings['distance'] < radius]
    else:
        filtered_data = df_listings[df_listings['neighbourhood'] == rprt_status]
    
    container = st.sidebar.beta_container()
    selected_options = container.multiselect("Select one or more queries (by order of priority):",
                                                 queries)
    
    if selected_options:
        ordered_parameters = [parameters[queries.index(option)] for option in selected_options]
        ordered_orders = [orders[queries.index(option)] for option in selected_options]
        
        filtered_data = filtered_data.sort_values(by=ordered_parameters, ascending=ordered_orders)
        
        no_listings = st.sidebar.slider("Select a no. of listings to show", min_value=1, max_value=50, value=25, step=1)
        
        filtered_data = filtered_data.head(no_listings)
    
    st.subheader("Listing Finder")
    st.markdown(
        "In order to facilitate the task of finding a listing, we've created this tool will allow users to search for a listing based on their different preferences. "
        "On the left side of the panel, you can select the neighbourhood you're insterested in, or select a radius in km from the center of NY's main attractions. "
        "By default, the finder will show all the listings situated in the area selected. The user can then select a query to show a number (from 1 to 50) of listings that satisfy his/her requirements.   ")

    st.markdown("_Note: the order of the queries matters. The first query will be prioritised before the second and so on._"
        )
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
    
    if rprt_status == 'Radius from the attractions':
        folium.Circle(
            radius=radius*1000,
            location=[lat_mean, lon_mean],
            color="crimson",
            fill=True
        ).add_to(map_hooray)
    
    # add a marker for every record in the filtered data, use a clustered view
    marker_cluster = MarkerCluster().add_to(map_hooray)  # create marker clusters
    for index, row in filtered_data.iterrows():
        html = "Price: " + str(row.price) + "$" + "<br>" + "Rating: " + str(row.review_scores_rating) + "<br>" + \
            "Response rate: " + str(row.host_response_rate) + "<br>" + "Reviews: " + str(row.reviews_per_month)

        iframe = folium.IFrame(html, width=130, height=60)

        new_pops = folium.Popup(iframe, max_width=130)

        folium.Marker([row.latitude, row.longitude], radius=5, popup=new_pops, ).add_to(marker_cluster)
        
    folium_static(map_hooray, width=1000, height=600)
