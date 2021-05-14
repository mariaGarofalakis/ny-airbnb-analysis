import streamlit as st
import folium
from branca.element import MacroElement, Template
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from streamlit_folium import folium_static
import numpy as np

def app(df_clust):
    st.subheader("Real estate investment")
    st.markdown("Imagine that you run a real estate business and you want to invest in Airbnb. This application provides the "
                "ability to find the most profitable location for your new house. All you have to do is to study the map below "
                "and click on the specific cluster. This will give you a better intuition of how the prices in different regions of NY city are "
                "grouped together. In that way we are doing all the \"hard\" work of filtering out the regions which have about the same average price and now you "
                "are ready to focus on a specific area of NY according to your business plan.")


    X_train, X_test, = train_test_split(df_clust, test_size=0.05)
    df_clustering = X_test.loc[:, X_test.columns.isin(['price', 'zipcode'])]

    kmeans = KMeans(n_clusters=10, random_state=0)
    clust = X_test[["latitude", "longitude", 'price', 'zipcode', 'distance']].copy()
    clust = clust.assign(cluster=kmeans.fit_predict(df_clustering)[:, np.newaxis])
    data = clust.copy()

    ## create color column
    lst_elements = sorted(list(clust['cluster'].unique()))
    lst_colors = ['#8A2BE2', '#FF7F50', '#7FFF00', '#D2691E', '#00FFFF', '#E9967A', '#2F4F4F', '#FF69B4', '#66CDAA', '#FFFF00']
    data["color"] = data['cluster'].apply(lambda x:
                                          lst_colors[lst_elements.index(x)])

    x = clust.groupby(["cluster"]).mean('price')

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
    legend_html = """{% macro html(this, kwargs) %} <div style="position:fixed; bottom:10px; left:10px; border:2px solid black; z-index:9999; font-size:14px;">&nbsp;<b>""" + 'cluster - average price' + """:</b><br>"""
    for i in lst_elements:
        legend_html = legend_html + """&nbsp;<i class="fa fa-circle 
         fa-1x" style="color:""" + lst_colors[lst_elements.index(i)] + """">
         </i>&nbsp;""" + str(i) + """: """ + str(round(x.iloc[i]['price'])) + """<br>"""
    legend_html = legend_html + """</div> {% endmacro %}"""

    macro = MacroElement()
    macro._template = Template(legend_html)

    map_hooray.add_child(macro)

    folium_static(map_hooray, width=1000, height=600)