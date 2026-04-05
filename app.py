import os
import requests
import pickle
import streamlit as st

# ==============================
# DOWNLOAD similarity.pkl FROM DRIVE
# ==============================
import os
import requests

if not os.path.exists("similarity.pkl"):
    url = "https://github.com/Bhaskarroy123/Movie-Recommendation-System/releases/download/v1.0/similarity.pkl"
    r = requests.get(url)
    with open("similarity.pkl", "wb") as f:
        f.write(r.content)


# ==============================
# API HELPER
# ==============================
def fetch_movie_details(movie_id, movie_title):
    api_key = st.secrets["API_KEY"]

    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&append_to_response=credits"
        data = requests.get(url).json()

        if not data.get('poster_path'):
            search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie_title}"
            search_data = requests.get(search_url).json()

            if search_data.get('results'):
                new_id = search_data['results'][0]['id']
                data = requests.get(
                    f"https://api.themoviedb.org/3/movie/{new_id}?api_key={api_key}&append_to_response=credits"
                ).json()

        poster_path = data.get('poster_path')
        poster = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Image"

        rating = data.get('vote_average', "N/A")
        overview = data.get('overview', "No overview available")

        cast = data.get('credits', {}).get('cast', [])
        actors = ", ".join([c['name'] for c in cast[:3]]) if cast else "N/A"

        return poster, rating, overview, actors

    except:
        return "https://via.placeholder.com/500x750?text=Error", "N/A", "N/A", "N/A"

# ==============================
# RECOMMEND FUNCTION
# ==============================
def recommend(movie_name):
    title_col = 'title' if 'title' in movies.columns else 'original_title'
    id_col = 'movie_id' if 'movie_id' in movies.columns else 'id'

    index = movies[movies[title_col] == movie_name].index[0]
    distances = sorted(list(enumerate(similarity[index])), key=lambda x: x[1], reverse=True)

    results = []
    for i in distances[1:6]:
        m_id = movies.iloc[i[0]][id_col]
        m_title = movies.iloc[i[0]][title_col]

        match = round(i[1] * 100, 1)

        poster, rating, overview, actors = fetch_movie_details(m_id, m_title)

        results.append({
            "name": m_title,
            "poster": poster,
            "match": match,
            "rating": rating,
            "overview": overview,
            "actors": actors
        })

    return results

# ==============================
# UI
# ==============================
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.title("🎬 Movie Recommendation System")

movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

title_column = 'title' if 'title' in movies.columns else 'original_title'

selected_movie = st.selectbox("Select a movie", movies[title_column].values)

if st.button("Show Recommendation"):
    recs = recommend(selected_movie)

    cols = st.columns(5)

    for i, movie in enumerate(recs):
        with cols[i]:
            st.image(movie['poster'], use_container_width=True)
            st.markdown(f"**{movie['name']}**")
            st.markdown(f"⭐ {movie['rating']}")
            st.markdown(f"🎯 Match: {movie['match']}%")

            with st.expander("Overview"):
                st.write(movie['overview'])
                st.caption(f"Cast: {movie['actors']}")