import pandas as pd
import streamlit as st
from math import radians, cos, sin, asin, sqrt
import re
import introduction, analysis, listing_finder, details, investment, prediction, statistics

@st.cache(allow_output_mutation=True)
def get_data():
    df_listings = pd.read_csv("csv_files/df_listings.csv", index_col='Unnamed: 0')
    df_attractions = pd.read_csv("csv_files/df_attractions.csv", index_col='Unnamed: 0')
    df_predictions = pd.read_csv("csv_files/df_predictions.csv", index_col='Unnamed: 0')
    df_clust = pd.read_csv("csv_files/df_clust.csv", index_col='Unnamed: 0')
    facilities = pd.read_csv("csv_files/facilities.csv", index_col='Unnamed: 0')
    df_count = pd.read_csv("csv_files/df_count.csv", index_col='Unnamed: 0')
    df_neigh_price = pd.read_csv("csv_files/df_neigh_price.csv", index_col='Unnamed: 0')
    df_neigh_rating = pd.read_csv("csv_files/df_neigh_rating.csv", index_col='Unnamed: 0')
    df_neigh_amenities = pd.read_csv("csv_files/df_neigh_amenities.csv", index_col='Unnamed: 0')

    return df_listings, df_attractions, df_predictions, df_clust, facilities['0'].values.tolist(), df_count, df_neigh_price, df_neigh_rating, df_neigh_amenities

st.set_page_config(page_title="New York City Airbnb Analysis", page_icon="🗽", layout="wide")

html_temp ="""
    <div style="background-color:#FF5A60;padding:1.5px">
    <font color=\"#FFFFFF\" size=\"32\"><strong><center>New York City Airbnb Analysis</center></strong></font>
    </div><br>"""
st.markdown(html_temp, unsafe_allow_html=True)

df_listings, df_attractions, df_predictions, df_clust, facilities, df_count, df_neigh_price, df_neigh_rating, df_neigh_amenities = get_data()

PAGES = {
    "Introduction": introduction,
    "Basic Statistics": statistics,
    "Data Analysis": analysis,
    "Listing Finder": listing_finder,
    "Prediction": prediction,
    "Investment": investment,
    "Technical Details": details
}


st.sidebar.title('Navigation')
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page = PAGES[selection]

if page == prediction:
    page.app(df_listings, df_attractions, df_predictions, facilities)
elif page == investment:
    page.app(df_clust)
elif page == statistics:
    page.app(df_listings, df_count, df_neigh_price, df_neigh_rating, df_neigh_amenities)
elif page == details:
    page.app()
else:
    page.app(df_listings, df_attractions)
