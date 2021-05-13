import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

def app(df_listings, df_attractions):
    st.subheader("Distribution of listings per focus neighbourhood")
    st.markdown(
        "Since the unique neighbourhoods are around 90, we decided to plot the distribution of listings only for the **\"20 most close to the attractions\"** neighbourhoods and the **\"20 most distant from the attractions\"** neighbourhoods.")

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
    st.markdown(
        "As can be seen the difference in the number of listings between the **Manhattan** area and the rest is huge. It seems that our initial assumption was correct and more central neighbourhoods have a higher proportion of apartments in Airbnb.")

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
    st.markdown(
        "As can be seen in the above figure, neighbourhoods which are more distant from the attractions tend to have listings with lower prices (Price: 100 or 200 with frequency 1), such as **The Rockaways**, **Jamaica**, **Bayside**, etc. Moreover, we wanted to investigate if there was a similar behavior in the distribution of **ratings**.")

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

    st.markdown(
        "Based on the figure, it seems that most central neighbourhoods differatiate in the ratings ranging between 60 and 100, while the more distant ones have higher ratings. However, this behavior might be relevant to the small amount of listings in the distant ones.")

    st.subheader("Distribution of Amenities per Neighbourhood")
    st.markdown(
        "Given the ratings distribution, we were curious regarding the amount of **amenities** provided in each neighbourhood on average and whether the owners are less concerned about the quality of the apartment if their listing is close to any attraction. Therefore, we visualized the attribute's distribution.")

    ##### Amenities distribution
    #df_listings['count_amenities'] = df_listings.apply(lambda x: len(x['amenities'].split(',')), axis=1)
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

    st.markdown(
        "In regards, to the amenities distribution it is worth mentioning that the distribution of the \"closest to the attractions\" neighbourhoods is much more varied than the ones further way and the highest frequencies are around **15-20** amenities. On the other hand, the \"distant from the attractions\" neighbourhoods show a higher number of amenities, around **30-40**.")
