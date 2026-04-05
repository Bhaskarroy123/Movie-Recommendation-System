import pickle
import streamlit as st
import requests

# ==============================
# 1. API HELPER (WITH FALLBACK)
# ==============================
def fetch_movie_details(movie_id, movie_title):
    api_key = "8265bd1679663a7ea12ac168da84d2e8"
    
    # Attempt 1: Fetch by ID
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&append_to_response=credits"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        # 🔥 THE FIX: If ID fails (not 200) or poster is missing, search by Title
        if response.status_code != 200 or not data.get('poster_path'):
            search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie_title}"
            search_data = requests.get(search_url, timeout=5).json()
            
            if search_data.get('results'):
                data = search_data['results'][0]
                # Re-fetch full details for the new ID to get credits/rating correctly
                new_id = data['id']
                data = requests.get(f"https://api.themoviedb.org/3/movie/{new_id}?api_key={api_key}&append_to_response=credits").json()
            else:
                return "https://via.placeholder.com/500x750?text=No+Poster", "N/A", "No overview", "N/A"

        # Safe Extraction
        poster_path = data.get('poster_path')
        # .lstrip('/') ensures no double slashes like .../w500//path.jpg
        full_poster = f"https://image.tmdb.org/t/p/w500/{poster_path.lstrip('/')}" if poster_path else "https://via.placeholder.com/500x750?text=No+Poster"
        
        rating = round(data.get('vote_average', 0), 1)
        overview = data.get('overview', 'No description available.')
        
        cast = data.get('credits', {}).get('cast', [])
        actors = ", ".join([member['name'] for member in cast[:3]]) if cast else "N/A"
        
        return full_poster, rating, overview, actors

    except:
        return "https://via.placeholder.com/500x750?text=Error", "N/A", "N/A", "N/A"

# ==============================
# 2. RECOMMENDATION ENGINE
# ==============================
def recommend(movie_name):
    title_col = 'title' if 'title' in movies.columns else 'original_title'
    id_col = 'movie_id' if 'movie_id' in movies.columns else 'id'
    
    index = movies[movies[title_col] == movie_name].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    
    rec_data = []
    for i in distances[1:6]:
        m_id = movies.iloc[i[0]][id_col]
        m_title = movies.iloc[i[0]][title_col]
        
        match_score = round(i[1] * 100, 1)
        
        # Pass BOTH ID and Title to the helper function
        poster, rating, overview, actors = fetch_movie_details(m_id, m_title)
        
        rec_data.append({
            "name": m_title,
            "poster": poster,
            "match": match_score,
            "rating": rating,
            "overview": overview,
            "actors": actors
        })
    return rec_data

# ==============================
# 3. UI & DATA LOADING
# ==============================
st.set_page_config(page_title="Movie Pro", layout="wide")
st.header('🎬 Movie Recommendation System')

# Ensure files are in the same folder or update path (e.g., 'model/movie_list.pkl')
movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

title_column = 'title' if 'title' in movies.columns else 'original_title'
selected_movie = st.selectbox("Type or select a movie", movies[title_column].values)

if st.button('Show Recommendation'):
    with st.spinner('Syncing with TMDb Database...'):
        recommendations = recommend(selected_movie)
        
        cols = st.columns(5)
        for i, movie in enumerate(recommendations):
            with cols[i]:
                st.markdown(f"**{movie['name']}**")
                st.image(movie['poster'])
                st.markdown(f"🎯 **{movie['match']}% Match**")
                st.markdown(f"⭐ **{movie['rating']}/10**")
                
                with st.expander("View Details"):
                    st.caption(f"**Cast:** {movie['actors']}")
                    st.write(f"**Overview:** {movie['overview'][:150]}...")