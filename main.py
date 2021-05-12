import base64

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import webbrowser
from folium.plugins import HeatMap
import folium
from streamlit_folium import folium_static
from folium import IFrame
from folium.plugins import MarkerCluster
from math import radians, cos, sin, asin, sqrt
import numpy as np
import re

#

def haversine(df_attractions, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    lat1 = df_attractions.latitude.mean()
    lon1 = df_attractions.longitude.mean()

    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * r

@st.cache
def get_data():
    df_listings = pd.read_csv("new_york.csv", index_col='Unnamed: 0')
    df_attractions = pd.read_csv("attractions.csv", index_col='Unnamed: 0')

    # remove special characters from price column and listings with NaN value
    df_listings = df_listings.dropna(subset=['price'])
    df_listings['price'] = df_listings.price.replace(to_replace='[a-zA-Z]', value='', regex=True)
    df_listings['price'] = df_listings.price.replace(to_replace=',|\$', value='', regex=True)
    df_listings['price'] = pd.to_numeric(df_listings['price'], errors='coerce')
    df_listings = df_listings[df_listings['price'] > 0]

    # remove special characters from rating column and listings with NaN value
    df_listings = df_listings.dropna(subset=['review_scores_rating'])
    df_listings['review_scores_rating'] = df_listings.review_scores_rating.replace(to_replace='[a-zA-Z]', value='',
                                                                                   regex=True)
    df_listings['review_scores_rating'] = df_listings.review_scores_rating.replace(to_replace='\s\s+', value='',
                                                                                   regex=True)
    df_listings['review_scores_rating'] = pd.to_numeric(df_listings['review_scores_rating'], errors='coerce')
    df_listings = df_listings[df_listings['review_scores_rating'] > 0]

    # remove listings with NaN value at neighbourhood column
    df_listings = df_listings.dropna(subset=['neighbourhood'])

    ################################ count haversine distance from aver attractions #################
    df_listings['distance'] = df_listings.apply(lambda x: haversine(df_attractions, x['latitude'], x['longitude']), axis=1)
    df_listings = df_listings.sort_values(by='distance')

    ##################################  for amenities ##################################################
    df_listings['count_amenities'] = df_listings.apply(lambda x: len(x['amenities'].split(',')), axis=1)
    df_listings['amenities'] = df_listings.apply(lambda x: x['amenities'].split(','), axis=1)
    regex = re.compile('[^a-zA-Z\d\s]')
    df_listings.amenities = df_listings.amenities.apply(lambda x: [regex.sub('', it) for it in x])
    df_predictions = pd.get_dummies(df_listings.amenities.apply(pd.Series).stack()).sum(level=0)

    k = df_predictions.sum(axis=0, skipna=True)
    filt_amnities = k[k.values >= 1090].index.tolist()
    df_predictions = df_predictions.loc[:, df_predictions.columns.isin(filt_amnities)]

    df_predictions = df_predictions.drop(
        columns=['translation missing enhostingamenity49', 'translation missing enhostingamenity50'])
    facilities = df_predictions.columns.to_list()
    df_predictions = df_predictions.assign(neighbourhood=df_listings['neighbourhood'])
    df_predictions = df_predictions.assign(distance=df_listings['distance'])
    df_predictions = pd.get_dummies(df_predictions, columns=['neighbourhood'])

    return df_listings, df_attractions,df_predictions,facilities

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


st.set_page_config(page_title="New York City Airbnb Analysis", page_icon="🗽", layout="wide")

html_temp ="""
    <div style="background-color:#B3CFDD;padding:1.5px">
    <h1 style="color=white;text-align:center;">New York City Airbnb Analysis </h1>
    </div><br>"""
st.markdown(html_temp, unsafe_allow_html=True)

st.markdown(
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous">',
    unsafe_allow_html=True,
)
query_params = st.experimental_get_query_params()
tabs = ["Introduction", "Basic Statistics", "Data Analysis", "Predictions", "Technical Details"]
if "tab" in query_params:
    active_tab = query_params["tab"][0]
else:
    active_tab = "Introduction"

if active_tab not in tabs:
    st.experimental_set_query_params(tab="Introduction")
    active_tab = "Introduction"

li_items = "".join(
    f"""
    <li class="nav-item">
        <a class="nav-link{' active' if t==active_tab else ''}" href="/?tab={t}">{t}</a>
    </li>
    """
    for t in tabs
)
tabs_html = f"""
    <ul class="nav nav-tabs">
    {li_items}
    </ul>
"""

st.markdown(tabs_html, unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)



if active_tab == "Introduction":
    st.header("Is there any connection between NY City's attraction and the Airbnb prices?")
    st.title('Heatmap of listings prices in NY city')

    df_listings, df_attractions, df_predictions, facilities = get_data()


    map_hooray = folium.Map([40.730610, -73.935242], zoom_start=11, tiles="OpenStreetMap")

    heatmap = HeatMap(list(
        zip(df_listings['latitude'], df_listings['longitude'], df_listings["price"])),
                      min_opacity=0.2,
                      max_val=df_listings["price"].max(),
                      radius=15, blur=15,
                      max_zoom=1)

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
                      icon=folium.Icon(color='blue', icon_color='yellow', icon='globe')).add_to(map_hooray)

    # add a marker for every record in the filtered data, use a clustered view
    marker_cluster = MarkerCluster().add_to(map_hooray)  # create marker clusters


    folium_static(map_hooray, width=1000, height=600)



elif active_tab == "Basic Statistics":
    df_listings, df_attractions, df_predictions, facilities = get_data()

    st.subheader("Distribution of listings per focus neighbourhood")
    st.markdown("Since the unique neighbourhoods are around 90, we decided to plot the distribution of listings only for the **\"20 most close to the attractions\"** neighbourhoods and the **\"20 most distant from the attractions\"** neighbourhoods.")

    neighs = df_listings['neighbourhood'].unique()
    focus_neighs = np.append(neighs[:20], neighs[-20:])

    #### listings distribution
    df_count = df_listings[df_listings.neighbourhood.isin(focus_neighs)].groupby('neighbourhood').count()[
        'id_listings'].reset_index(name='count')
    df_count['neigh_cat'] = pd.Categorical(df_count['neighbourhood'], categories=focus_neighs, ordered=True)
    df_count = df_count.sort_values(['neigh_cat'])

    fig = px.bar(df_count, x='neighbourhood', y='count')
    fig.update_layout(autosize=False, width=1400, height=500, xaxis_title="Focus Neighbourhoods",
                      yaxis_title="Number of Listings")
    fig.update_traces(marker_color='#428DB2', marker_line_color='#428DB2',
                      marker_line_width=1.5, opacity=0.8)
    st.plotly_chart(fig)

    st.subheader("Distribution of Prices per Neighbourhood")
    st.markdown("As can be seen the difference in the number of listings between the **Manhattan** area and the rest is huge. It seems that our initial assumption was correct and more central neighbourhoods have a higher proportion of apartments in Airbnb.")

    ##### Price distribution
    df_listings = df_listings.assign(round_price=np.ceil(df_listings['price'] / 100.0) * 100)

    df_neigh_price = pd.DataFrame()

    for neigh in df_listings.neighbourhood.unique():
        price_per_neigh = df_listings[df_listings['neighbourhood'] == neigh].groupby('round_price').count()[
            'id_listings']
        total_listings = df_listings[df_listings['neighbourhood'] == neigh].count()['id_listings']
        df_neigh_price[neigh] = price_per_neigh / total_listings

    df_neigh_price.reset_index(inplace=True)
    df_neigh_price['round_price'] = df_neigh_price['round_price'].astype(int)
    df_neigh_price['round_price'] = df_neigh_price['round_price'].astype(str)

    bar = []

    for i, neigh in enumerate(focus_neighs):
        bar.append(
            go.Bar(name=neigh, x=df_neigh_price.round_price, y=df_neigh_price[neigh], marker=dict(colorscale='viridis'),
                   marker_line_width=2, opacity=0.5))

    fig = go.Figure(data=bar)
    fig.update_layout(barmode='overlay', autosize=False, width=1400, height=600, xaxis_title="Price",
                      yaxis_title="Relative Frequency")
    st.plotly_chart(fig)

    st.subheader("Distribution of Ratings per Neighbourhood")
    st.markdown("As can be seen in the above figure, neighbourhoods which are more distant from the attractions tend to have listings with lower prices (Price: 100 or 200 with frequency 1), such as **The Rockaways**, **Jamaica**, **Bayside**, etc. Moreover, we wanted to investigate if there was a similar behavior in the distribution of **ratings**.")

    #### Ratings distribution
    df_listings = df_listings.assign(round_rating=np.ceil(df_listings['review_scores_rating'] / 5.0) * 5)

    df_neigh_rating = pd.DataFrame()

    for neigh in df_listings.neighbourhood.unique():
        rating_per_neigh = df_listings[df_listings['neighbourhood'] == neigh].groupby('round_rating').count()[
            'id_listings']
        total_listings = df_listings[df_listings['neighbourhood'] == neigh].count()['id_listings']
        df_neigh_rating[neigh] = rating_per_neigh / total_listings

    df_neigh_rating.reset_index(inplace=True)
    df_neigh_rating['round_rating'] = df_neigh_rating['round_rating'].astype(int)
    df_neigh_rating['round_rating'] = df_neigh_rating['round_rating'].astype(str)

    bar = []

    for i, neigh in enumerate(focus_neighs):
        bar.append(go.Bar(name=neigh, x=df_neigh_rating.round_rating, y=df_neigh_rating[neigh],
                          marker=dict(colorscale='viridis'),
                          marker_line_width=2, opacity=0.5))

    fig = go.Figure(data=bar)
    fig.update_layout(barmode='overlay', autosize=False, width=1400, height=500, xaxis_title="Rating",
                      yaxis_title="Relative Frequency")
    st.plotly_chart(fig)

    st.markdown("Based on the figure, it seems that most central neighbourhoods differatiate in the ratings ranging between 60 and 100, while the more distant ones have higher ratings. However, this behavior might be relevant to the small amount of listings in the distant ones.")

    st.subheader("Distribution of Amenities per Neighbourhood")
    st.markdown("Given the ratings distribution, we were curious regarding the amount of **amenities** provided in each neighbourhood on average and whether the owners are less concerned about the quality of the apartment if their listing is close to any attraction. Therefore, we visualized the attribute's distribution.")

    ##### Amenities distribution
   # df_listings['count_amenities'] = df_listings.apply(lambda x: len(x['amenities'].split(',')), axis=1)
    df_listings = df_listings.assign(round_amenities=np.ceil(df_listings['count_amenities'] / 5.0) * 5)

    df_neigh_amenities = pd.DataFrame()

    for neigh in df_listings.neighbourhood.unique():
        amenities_per_neigh = df_listings[df_listings['neighbourhood'] == neigh].groupby('round_amenities').count()[
            'id_listings']
        total_listings = df_listings[df_listings['neighbourhood'] == neigh].count()['id_listings']
        df_neigh_amenities[neigh] = amenities_per_neigh / total_listings

    df_neigh_amenities.reset_index(inplace=True)
    df_neigh_amenities['round_amenities'] = df_neigh_amenities['round_amenities'].astype(int)
    df_neigh_amenities['round_amenities'] = df_neigh_amenities['round_amenities'].astype(str)

    bar = []

    for i, neigh in enumerate(focus_neighs):
        bar.append(go.Bar(name=neigh, x=df_neigh_amenities.round_amenities, y=df_neigh_amenities[neigh],
                          marker=dict(colorscale='viridis'),
                          marker_line_width=2, opacity=0.5))

    fig = go.Figure(data=bar)
    fig.update_layout(barmode='overlay', autosize=False, width=1400, height=500, xaxis_title="Amenities",
                      yaxis_title="Relative Frequency")
    st.plotly_chart(fig)

    st.markdown("In regards, to the amenities distribution it is worth mentioning that the distribution of the \"closest to the attractions\" neighbourhoods is much more varied than the ones further way and the highest frequencies are around **15-20** amenities. On the other hand, the \"distant from the attractions\" neighbourhoods show a higher number of amenities, around **30-40**.")

elif active_tab == "Data Analysis":

    st.header("Prices and ratings distributions")
    st.markdown(
        "On the left site of the panel there is an interactive field where we can select  the neighbourhood and the price range of our disire. "
        "In addition a distribution of prices and user's ratings are shown by the two figures above according to our selections. "
        "In that way we can compare the values of prices between different neighbourhoods and choose the one which is more suitable to our budget ")
    df_listings, df_attractions, df_predictions, facilities = get_data()

    neighs = df_listings['neighbourhood'].unique()

    ###################### round prices #############################
    df_listings = df_listings.assign(round_price=np.ceil(df_listings['price'] / 50.0) * 50)

    ################################ streamlit ######################################################
    rprt_status = st.sidebar.selectbox("Choose Neighbourhood(*)", neighs)
    minimum = st.sidebar.number_input("Minimum Price", min_value=50, step=50)
    maximum = st.sidebar.number_input("Maximum Price", min_value=50, value=3000, step=50)
    if minimum > maximum:
        st.error("Please enter a valid range")
    st.sidebar.write("(*) The neighbourhoods are sorted based on their distance from the tourist attractions")

    col1, col2 = st.beta_columns([2,2])
    filtered_data = df_listings[(df_listings['neighbourhood'] == rprt_status) & (df_listings['round_price'] >= minimum) & (
                    df_listings['round_price'] <= maximum)].copy()
    fig1 = px.histogram(filtered_data, x='round_price', width=800, height=350)
    col1.plotly_chart(fig1)

    fig2 = px.histogram(filtered_data, x='review_scores_rating', width=800, height=350)
    col2.plotly_chart(fig2)

    popup = []

    for i in range(len(png)):
        encoded = base64.b64encode(open(png[i], 'rb').read()).decode()
        building_name = df_attractions.Attraction[i]
        html = building_name
        html += '<img src="data:image/png[i];base64,{}" width="100" height="100">'.format(encoded)
        iframe = IFrame(html, width=130, height=150)
        popup.append(folium.Popup(iframe, max_width=130))

    st.title('Map of listings for selected neighbourhood')

    st.markdown(
         "In order to get a better intution of how the listings are distributed is space we provide a map of NY city where all the selected listings are "
        "teamed together into clusters. If you zoom in a specific cluster you can get the exact location of the listing. Also by clicking "
        "a specific marker a pop up window is showing up, which provides us with informations for the price and the user's ratings for this specific listing. "
        "On the map there are markers with NY city's most significant attractions so as we can relate the distance of the available listings "
        "with those regions of the city with the most interesting places to visit. Finally by clicking the attraction's marker a picture of it shows up "
        "which is a good indication for a new visitor of the city.")

    map_hooray = folium.Map([40.730610, -73.935242], zoom_start=11, tiles="OpenStreetMap")

    for i in range(len(png)):
        folium.Marker([df_attractions.latitude[i], df_attractions.longitude[i]], popup=popup[i],
                      icon=folium.Icon(color='blue', icon_color='yellow', icon='globe')).add_to(map_hooray)

    # add a marker for every record in the filtered data, use a clustered view
    marker_cluster = MarkerCluster().add_to(map_hooray)  # create marker clusters
    for index, row in filtered_data.iterrows():
        html = "Price: "+ str(row.price)+"$"+"<br>"+"Rating: "+ str(row.review_scores_rating)

        iframe = folium.IFrame(html, width=130, height=60)

        new_pops = folium.Popup(iframe, max_width=130)

        folium.Marker([row.latitude,row.longitude], radius=5, popup=new_pops,).add_to(marker_cluster)

    folium_static(map_hooray, width=1000, height=600)
    #st.markdown(map_hooray._repr_html_(), unsafe_allow_html=True)


elif active_tab == "Predictions":
    st.header("Prediction of price for a new listing")
    st.markdown("If you are interested in adding a new listing to RBNB, this tool will help you to find an apropriate price "
                "for your house according to the demand for the specific neighbourhood and the facilities that you are ofering. "
                "All you have to do is to add the neighbourhood of your choise and ofcourse the amenities you are going to provide.")

    df_listings, df_attractions, df_predictions, facilities = get_data()

    neighs = df_listings['neighbourhood'].unique()
    rprt_status = st.sidebar.selectbox("Choose Neighbourhood(*)", neighs)

    #st_ms = st.sidebar.multiselect("facilities", df_predictions.columns.tolist(), default=facilities)

    container = st.sidebar.beta_container()
    all = st.sidebar.checkbox("Select all")

    if all:
        selected_options = container.multiselect("Select one or more options:",
                                                 facilities,facilities)
    else:
        selected_options = container.multiselect("Select one or more options:",
                                                 facilities)





elif active_tab == "Technical Details":
    st.header("Explainer Notebook")
    st.markdown("If you are interested in the technical details, our implementations are available as a Jupyter Notebook.")
    left, right = st.beta_columns([1,3])
    with left:
        if st.button('iPython Notebook'):
            html_temp = """<a href="https://colab.research.google.com/drive/1zQPLZkdHfL12qhDBVvIrRM47PVjwrPVd?usp=sharing" target="_blank">Link to our Explainer Notebook</a>"""
            st.markdown(html_temp, unsafe_allow_html=True)
    with right:
        if st.button('Data'):
            html_temp = """<a href="https://drive.google.com/drive/folders/18WcZMktFQj5W_dAmK7hL-Y8cFGHvwmXH?usp=sharing" target="_blank">Link to our Data</a>"""
            st.markdown(html_temp, unsafe_allow_html=True)
    st.markdown(
        "Created for the assignment of 02806 Social data analysis and visualization course offered by the Technical University of Denmark.")

    html_temp = """
        <div align="center">
        <br>
        <h6 style="text-align:center;">Copyright, 2021</h6>
        <h6 style="text-align:center;">Electra Zarafeta, Maria Garofalaki, Jorge Sintes</h6>
        </div><br>"""
    st.markdown(html_temp, unsafe_allow_html=True)

    st.balloons()
else:
    st.error("Something has gone terribly wrong.")
