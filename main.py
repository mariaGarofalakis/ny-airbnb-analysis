import pandas as pd
import streamlit as st
from math import radians, cos, sin, asin, sqrt
import re
import introduction, analysis, details, investment, prediction, statistics

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

@st.cache(allow_output_mutation=True)
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
    df_listings['distance'] = df_listings.apply(lambda x: haversine(df_attractions, x['latitude'], x['longitude']),
                                                axis=1)
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
    df_predictions = pd.get_dummies(df_predictions, columns=['neighbourhood'], prefix='', prefix_sep='')

    return df_listings, df_attractions, df_predictions, facilities



st.set_page_config(page_title="New York City Airbnb Analysis", page_icon="🗽", layout="wide")

html_temp ="""
    <div style="background-color:#FF5A60;padding:1.5px">
    <font color=\"#FFFFFF\" size=\"32\"><strong><center>New York City Airbnb Analysis</center></strong></font>
    </div><br>"""
st.markdown(html_temp, unsafe_allow_html=True)

df_listings, df_attractions, df_predictions, facilities = get_data()

PAGES = {
    "Introduction": introduction,
    "Basic Statistics": statistics,
    "Data Analysis": analysis,
    "Prediction": prediction,
    "Investment": investment,
    "Technical Details": details
}


st.sidebar.title('Navigation')
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page = PAGES[selection]

if page == prediction:
    page.app(df_listings, df_attractions, df_predictions, facilities)
elif page == details:
    page.app()
else:
    page.app(df_listings, df_attractions)
