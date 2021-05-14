import pandas as pd
import streamlit as st
import folium
from streamlit_folium import folium_static
import numpy as np
from geopy.geocoders import Nominatim
from sklearn.ensemble import RandomForestRegressor
from folium.features import DivIcon
from math import radians, cos, sin, asin, sqrt


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


def app(df_listings, df_attractions, df_predictions, facilities):
    st.subheader("Prediction of price for a new listing")
    st.markdown(
        "If you are interested in adding a new listing to Airbnb, this tool will help you to find an appropriate price "
        "for your house according to the demand for the specific neighbourhood and the facilities that you are offering. "
        "All you have to do is to add the neighbourhood of your choise and the amenities you are planning to provide.")

    X_test = pd.DataFrame(columns=df_predictions.columns)
    X_test.loc[len(X_test)] = 0

    neighs = df_listings['neighbourhood'].unique()
    rprt_status = st.sidebar.selectbox("Choose Neighbourhood(*)", neighs)
    container = st.sidebar.beta_container()
    all = st.sidebar.checkbox("Select all")

    if all:
        selected_options = container.multiselect("Select one or more amenities:",
                                                 facilities, facilities)
    else:
        selected_options = container.multiselect("Select one or more amenities:",
                                                 facilities)

    if st.button('Predict the price of your new listing'):
        geolocator = Nominatim(user_agent="electra")
        location = geolocator.geocode(rprt_status + ", New York")
        X_test.distance = haversine(df_attractions, location.latitude, location.longitude)
        X_test[selected_options] = 1
        X_test[rprt_status] = 1
        model = RandomForestRegressor(max_depth=8, min_samples_leaf=0.1, min_samples_split=0.1, n_estimators=50)
        model.fit(df_predictions, df_listings.price.to_numpy()[:, np.newaxis])
        y_pred = model.predict(X_test)

        map_hooray = folium.Map([location.latitude, location.longitude], zoom_start=11, tiles="OpenStreetMap")

        html = "<font color= \"#225d7a\" face = \"Raleway\" size = \"5\"><strong>Price: {}$</strong></font>".format(
            str(round(y_pred[0])))

        folium.Marker([location.latitude, location.longitude], icon=DivIcon(icon_size=(150, 10),
                                                                            icon_anchor=(60, 20), html=html)).add_to(
            map_hooray)
        map_hooray.add_child(folium.CircleMarker([location.latitude, location.longitude], radius=80,
                                                 color="#428DB2",
                                                 fill=True,
                                                 fill_color="#428DB2", ))

        folium_static(map_hooray, width=1000, height=600)