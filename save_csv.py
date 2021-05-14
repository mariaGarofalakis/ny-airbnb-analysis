import pandas as pd
from math import radians, cos, sin, asin, sqrt
import re
import numpy as np

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

neighs = df_listings['neighbourhood'].unique()
focus_neighs = np.append(neighs[:20], neighs[-20:])

#### listings distribution
df_count = df_listings[df_listings.neighbourhood.isin(focus_neighs)].groupby('neighbourhood').count()[
    'id_listings'].reset_index(name='count')
df_count['neigh_cat'] = pd.Categorical(df_count['neighbourhood'], categories=focus_neighs, ordered=True)
df_count = df_count.sort_values(['neigh_cat'])

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


##################################  for amenities ##################################################
df_listings['count_amenities'] = df_listings.apply(lambda x: len(x['amenities'].split(',')), axis=1)
df_listings['amenities'] = df_listings.apply(lambda x: x['amenities'].split(','), axis=1)
regex = re.compile('[^a-zA-Z\d\s]')
df_listings.amenities = df_listings.amenities.apply(lambda x: [regex.sub('', it) for it in x])
df_predictions = pd.get_dummies(df_listings.amenities.apply(pd.Series).stack()).sum(level=0)


##### Amenities distribution
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



k = df_predictions.sum(axis=0, skipna=True)
filt_amnities = k[k.values >= 1090].index.tolist()
df_predictions = df_predictions.loc[:, df_predictions.columns.isin(filt_amnities)]

df_predictions = df_predictions.drop(
    columns=['translation missing enhostingamenity49', 'translation missing enhostingamenity50'])
facilities = df_predictions.columns.to_list()
df_predictions = df_predictions.assign(neighbourhood=df_listings['neighbourhood'])
df_predictions = df_predictions.assign(distance=df_listings['distance'])
df_predictions = pd.get_dummies(df_predictions, columns=['neighbourhood'], prefix='', prefix_sep='')

df_clust = df_listings.copy()
df_clust = df_clust.dropna(subset=['zipcode'])
df_clust.zipcode = df_clust.zipcode.apply(lambda x: int(re.findall('([0-9.]+)', str(x))[0]))
df_clust = df_clust.assign(price=np.ceil(df_clust['price'] / 50.0) * 50)

df_listings.to_csv('csv_files/df_listings.csv')
df_attractions.to_csv('csv_files/df_attractions.csv')
df_count.to_csv('csv_files/df_count.csv')
df_neigh_price.to_csv('csv_files/df_neigh_price.csv')
df_neigh_rating.to_csv('csv_files/df_neigh_rating.csv')
df_neigh_amenities.to_csv('csv_files/df_neigh_amenities.csv')
df_predictions.to_csv('csv_files/df_predictions.csv')
df_clust.to_csv('csv_files/df_clust.csv')
pd.DataFrame(facilities).to_csv('csv_files/facilities.csv')