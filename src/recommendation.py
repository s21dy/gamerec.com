# Data Preporcess
import pandas as pd
import numpy as np
import sqlite3

#Recommendation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix, hstack
from sklearn.decomposition import TruncatedSVD

# Load Dataset
def load_data(db_path="../data/processed/process_game.db"):
    conn = sqlite3.connect(db_path)
    data = pd.read_sql_query("SELECT * FROM processed_game", conn)
    conn.close()

    # Optimize memory usage
    data = data.dropna(subset=['all_reviews', 'genre', 'recent_reviews', 'popular_tags'])

    data['id'] = data['id'].astype(int)
    data['all_reviews'] = data['all_reviews'].astype(str)
    data['genre'] = data['genre'].astype(str)
    data['recent_reviews'] = data['recent_reviews'].astype(str)
    data['popular_tags'] = data['popular_tags'].astype(str)
    return data

# Text Preprocessing
def preprocess_text(text):
    """Preprocess text data by cleaning and removing unnecessary characters."""
    return ' '.join(text.split()).lower()

def reduce_dimensions(matrix, n_components=100):
    svd = TruncatedSVD(n_components=n_components)
    reduced_matrix = svd.fit_transform(matrix)
    return csr_matrix(reduced_matrix)

# Compute Similarity Matrix
def compute_similarity_matrix(data, weights=None, n_components=100):
    """
    Compute the similarity matrix using weighted TF-IDF vectors and SVD for dimension reduction.
    
    Args:
        data (pd.DataFrame): Input data with textual columns.
        weights (dict): Weights for each text column.
        n_components (int): Number of components for SVD dimensionality reduction.
    
    Returns:
        scipy.sparse.csr_matrix: Cosine similarity matrix.
    """    
    if weights is None:
        weights = {'all_reviews': 0.3, 'genre': 0.1, 
                   'recent_reviews': 0.4, 'popular_tags': 0.2}    
    
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000, max_df=0.9)
    vectors = []
    for column, weight in weights.items():
        tfidf_matrix = vectorizer.fit_transform(data[column].apply(preprocess_text))
        weighted_matrix = tfidf_matrix * weight
        vectors.append(weighted_matrix)

    combined_matrix = hstack(vectors)
    reduced_matrix = TruncatedSVD(n_components=n_components, random_state=42).fit_transform(combined_matrix)
    return cosine_similarity(csr_matrix(reduced_matrix), dense_output=False) # Output remains sparse

# Recommendation function
def get_game_rec(selected_game, data, similarity_matrix, top_n=15):
    """
    Recommend games based on the selected game.
    Args:
        selected_game (str): Name of the selected game.
        data (pd.DataFrame): Game data with names and other attributes.
        similarity_matrix (scipy.sparse.csr_matrix): Precomputed similarity matrix.
        top_n (int): Number of recommendations to return. 
    Returns:
        pd.Series: Recommended game names.
    """
    try:
        # Find the index of the selected game
        game_index = data[data['name'] == selected_game].index[0]
        game_similarities = similarity_matrix.getrow(game_index).toarray().flatten()        
        similar_games = sorted(enumerate(game_similarities), key=lambda x: x[1], reverse=True)
        recommended_indices = [i[0] for i in similar_games[1:top_n + 1]]
        return data.iloc[recommended_indices]   
    except IndexError:
        return pd.DataFrame({'Error': [f"'{selected_game}' not found in the dataset."]})
    except Exception as e:
        return pd.DataFrame({'Error': [str(e)]})

p_data = load_data()
similarity_matrix = compute_similarity_matrix(p_data)