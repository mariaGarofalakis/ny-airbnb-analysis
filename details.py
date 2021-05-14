import streamlit as st

def app():
    st.header("Explainer Notebook")
    st.markdown(
        "If you are interested in the technical details, our implementations are available as a Jupyter Notebook.")
    left, mid, right = st.beta_columns(3)
    with left:
        if st.button('iPython Notebook'):
            html_temp = """<a href="https://colab.research.google.com/drive/1zQPLZkdHfL12qhDBVvIrRM47PVjwrPVd?usp=sharing" target="_blank">Link to our Explainer Notebook</a>"""
            st.markdown(html_temp, unsafe_allow_html=True)
    with mid:
        if st.button('GitHub Repo'):
            html_temp = """<a href="https://github.com/ElectraZarafeta/ny-airbnb-analysis.git" target="_blank">Link to our GitHub Repo</a>"""
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