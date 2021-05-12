import base64
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import folium
from branca.element import MacroElement, Template
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from streamlit_folium import folium_static
from folium import IFrame
from folium.plugins import MarkerCluster, HeatMap
from math import radians, cos, sin, asin, sqrt
import numpy as np
import re
from geopy.geocoders import Nominatim
from sklearn.ensemble import RandomForestRegressor
from folium.features import DivIcon

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
def get_data(tab=None):
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
    df_listings['distance'] = df_listings.apply(lambda x: haversine(df_attractions, x['latitude'], x['longitude']),
                                                axis=1)
    df_listings = df_listings.sort_values(by='distance')

    if tab == "Predictions":
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
        df_predictions = pd.get_dummies(df_predictions, columns=['neighbourhood'], prefix='', prefix_sep='')

        return df_listings, df_attractions, df_predictions, facilities
    else:
        return df_listings, df_attractions

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
tabs = ["Introduction", "Basic Statistics", "Data Analysis", "Prediction", "Investigation", "Technical Details"]
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
    st.subheader('How many Airbnb listings are located in NY?')

    df_listings, df_attractions = get_data()
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

    # add a marker for every record in the filtered data, use a clustered view
    marker_cluster = MarkerCluster().add_to(map_hooray)  # create marker clusters

    folium_static(map_hooray, width=1000, height=600)

elif active_tab == "Basic Statistics":
    df_listings, df_attractions = get_data()

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
    df_listings['count_amenities'] = df_listings.apply(lambda x: len(x['amenities'].split(',')), axis=1)
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
    df_listings, df_attractions = get_data()

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
    minimum = st.sidebar.number_input("Minimum Price", min_value=5, step=50)
    maximum = st.sidebar.number_input("Maximum Price", min_value=5, value=3000, step=50)
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
        html = "Price: "+ str(row.price)+"$"+"<br>"+"Rating: "+ str(row.review_scores_rating)

        iframe = folium.IFrame(html, width=130, height=60)

        new_pops = folium.Popup(iframe, max_width=130)

        folium.Marker([row.latitude,row.longitude], radius=5, popup=new_pops,).add_to(marker_cluster)

    folium_static(map_hooray, width=1000, height=600)

elif active_tab == "Prediction":
    st.subheader("Prediction of price for a new listing")
    st.markdown(
        "If you are interested in adding a new listing to Airbnb, this tool will help you to find an appropriate price "
        "for your house according to the demand for the specific neighbourhood and the facilities that you are offering. "
        "All you have to do is to add the neighbourhood of your choise and the amenities you are planning to provide.")

    df_listings, df_attractions, df_predictions, facilities = get_data(tab="Predictions")
    X_test = pd.DataFrame(columns=df_predictions.columns)
    X_test.loc[len(X_test)] = 0

    neighs = df_listings['neighbourhood'].unique()
    rprt_status = st.sidebar.selectbox("Choose Neighbourhood(*)", neighs)
    container = st.sidebar.beta_container()
    all = st.sidebar.checkbox("Select all")

    if all:
        selected_options = container.multiselect("Select one or more options:",
                                                 facilities, facilities)
    else:
        selected_options = container.multiselect("Select one or more options:",
                                                 facilities)

    if st.button('Predict the price of your new listing'):
        geolocator = Nominatim(user_agent="electra")
        location = geolocator.geocode(rprt_status+", New York")
        X_test.distance = haversine(df_attractions, location.latitude, location.longitude)
        X_test[selected_options] = 1
        X_test[rprt_status] = 1
        model = RandomForestRegressor(max_depth=8, min_samples_leaf=0.1, min_samples_split=0.1, n_estimators=50)
        model.fit(df_predictions, df_listings.price.to_numpy()[:,np.newaxis])
        y_pred = model.predict(X_test)

        map_hooray = folium.Map([location.latitude, location.longitude], zoom_start=11, tiles="OpenStreetMap")

        html = "<font color= \"#225d7a\" face = \"Raleway\" size = \"5\"><strong>Price: {}$</strong></font>".format(str(round(y_pred[0])))

        folium.Marker([location.latitude, location.longitude], icon=DivIcon(icon_size=(150,10),
                            icon_anchor=(60,20), html=html)).add_to(map_hooray)
        map_hooray.add_child(folium.CircleMarker([location.latitude, location.longitude], radius=80,
                            color="#428DB2",
                            fill=True,
                            fill_color="#428DB2",))

        folium_static(map_hooray, width=1000, height=600)

elif active_tab == "Investigation":
    st.subheader("Real estate investment")
    st.markdown("Imagine that you run a real estate business and you want to invest in Airbnb. This application provides the "
                "ability to find the most profitable location for your new house. All you have to do is to study the map below "
                "and click on the specific cluster. This will give you a better intuition of how the prices in different regions of NY city are "
                "grouped together. In that way we are doing all the \"hard\" work of filtering out the regions which have about the same average price and now you "
                "are ready to focus on a specific area of NY according to your business plan.")

    df_listings, df_attractions = get_data()
    df_listings = df_listings.dropna(subset=['zipcode'])
    df_listings.zipcode = df_listings.zipcode.apply(lambda x: int(re.findall('([0-9.]+)', str(x))[0]))
    df_listings = df_listings.assign(price=np.ceil(df_listings['price'] / 50.0) * 50)

    X_train, X_test, = train_test_split(df_listings, test_size=0.05)
    df_clustering = X_test.loc[:, X_test.columns.isin(['price', 'zipcode'])]

    kmeans = KMeans(n_clusters=10, random_state=0)
    clust = X_test[["latitude", "longitude", 'price', 'zipcode']].copy()
    clust = clust.assign(cluster=kmeans.fit_predict(df_clustering)[:, np.newaxis])
    data = clust.copy()

    ## create color column
    lst_elements = sorted(list(clust['cluster'].unique()))
    lst_colors = ['#8A2BE2', '#FF7F50', '#7FFF00', '#D2691E', '#00FFFF', '#E9967A', '#2F4F4F', '#FF69B4', '#66CDAA', '#FFFF00']
    data["color"] = data['cluster'].apply(lambda x:
                                          lst_colors[lst_elements.index(x)])

    ## create size column (scaled)
    scaler = MinMaxScaler(feature_range=(6, 25))
    data["size"] = scaler.fit_transform(clust['price'].values.reshape(-1, 1)).reshape(-1)

    lat = 40.730610
    lon = -73.935242
    map_hooray = folium.Map([lat, lon], zoom_start=11, tiles="cartodbpositron")

    ## add points
    data.apply(lambda row: folium.CircleMarker(
        location=[row['latitude'], row['longitude']], popup="Price: "+str(round(row['price'])),
        color=row["color"], fill=True,
        radius=row["size"]).add_to(map_hooray), axis=1)

    ## add html legend
    legend_html = """{% macro html(this, kwargs) %} <div style="position:fixed; bottom:10px; left:10px; border:2px solid black; z-index:9999; font-size:14px;">&nbsp;<b>""" + 'cluster' + """:</b><br>"""
    for i in lst_elements:
        legend_html = legend_html + """&nbsp;<i class="fa fa-circle 
         fa-1x" style="color:""" + lst_colors[lst_elements.index(i)] + """">
         </i>&nbsp;""" + str(i) + """<br>"""
    legend_html = legend_html + """</div> {% endmacro %}"""

    macro = MacroElement()
    macro._template = Template(legend_html)

    map_hooray.add_child(macro)

    folium_static(map_hooray, width=1000, height=600)

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
